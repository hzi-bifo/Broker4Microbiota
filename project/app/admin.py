import os
import random
import gzip
import requests
from django.contrib import admin, messages
from django.shortcuts import render 
from django.core.files.base import ContentFile
from django.conf import settings
from Bio import SeqIO
from io import StringIO
from .models import Order, Sample, Submission
from .forms import CreateGZForm
from django.template.loader import render_to_string
from xml.etree import ElementTree as ET
import logging

logger = logging.getLogger(__name__)

logger.debug(f"Current ENA password: {settings.ENA_PASSWORD}")

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'date', 'quote_no', 'billing_address', 'ag_and_hzi', 'contact_phone', 'email', 'data_delivery', 'signature', 'experiment_title', 'dna', 'rna', 'library', 'method', 'buffer', 'organism', 'isolated_from', 'isolation_method')

class SampleAdmin(admin.ModelAdmin):
    list_display = ('order', 'id', 'alias', 'title', 'taxon_id', 'scientific_name', 'investigation_type', 'study_type', 'platform', 'library_source', 'concentration', 'volume', 'ratio_260_280', 'ratio_260_230', 'comments', 'date', 'mixs_metadata_standard', 'mixs_metadata', 'filename_forward', 'filename_reverse', 'nf_core_mag_outdir', 'status')
    actions = ['generate_xml_and_create_submission']

    def generate_xml_and_create_submission(self, request, queryset):
        selected_samples = queryset
        order = selected_samples.first().order

        submission = Submission.objects.create(order=order)
        submission.samples.set(selected_samples)

        context = {
            'samples': selected_samples,
        }

        sample_xml_content = render_to_string('admin/app/sample/sample_xml_template.xml', context)
        submission.sample_object_xml = sample_xml_content

        file_path = os.path.join(settings.BASE_DIR, 'app', 'templates', 'admin', 'app', 'sample', 'submission_template.xml')
        with open(file_path, 'r') as file:
            submission_xml_content = file.read()
            print(submission_xml_content)  # Debugging: Check the content

        submission.submission_object_xml = submission_xml_content

        submission.save()

        self.message_user(request, f'Successfully created Submission {submission.id} with {selected_samples.count()} samples')

    generate_xml_and_create_submission.short_description = 'Generate XML and create Submission'

    def run_nfcore_mag(modeladmin, request, queryset):
        from subprocess import Popen, PIPE
        
        for sample in queryset:
            forward_path = os.path.join(settings.MEDIA_ROOT, sample.filename_forward)
            reverse_path = os.path.join(settings.MEDIA_ROOT, sample.filename_reverse)
            
            # Check if both files exist and are valid FASTQ
            if not (os.path.isfile(forward_path) and os.path.isfile(reverse_path) and sample.status == 'Valid FASTQ'):
                modeladmin.message_user(request, f"Sample {sample.id} missing valid FASTQ files. Skipping.", level=40)
                continue
            
            # Construct Nextflow command
            cmd = [
                "nextflow", "run", "nf-core/mag",
                "--input", f"{forward_path},{reverse_path}",
                "--outdir", os.path.join(settings.MEDIA_ROOT, "output", sample.sample_name),
                "-profile", "docker"  # Adjust profile as needed
            ]
            
            # Execute Nextflow pipeline (consider background execution)
            process = Popen(cmd, stdout=PIPE, stderr=PIPE)
            output, error = process.communicate()
            
            # Handle output and errors (logging, updating sample status etc.)
            if process.returncode == 0:
                modeladmin.message_user(request, f"nf-core/mag successfully run for Sample {sample.id}.")
                # Update sample status if needed
            else:
                modeladmin.message_user(request, f"Error running nf-core/mag for Sample {sample.id}: {error.decode()}", level=40)

        modeladmin.message_user(request, f"nf-core/mag processing initiated for selected samples.")

    run_nfcore_mag.short_description = "Run nf-core/mag pipeline"

admin.site.register(Order, OrderAdmin)
admin.site.register(Sample, SampleAdmin)

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'sample_count', 'accession_status', 'submission_object_xml')
    
    actions = ['register_sample']

    def sample_count(self, obj):
        return obj.samples.count()
    sample_count.short_description = 'Number of Samples'

    def register_sample(self, request, queryset):
        for submission in queryset:
            try:
                # Save XML content to files for debugging
                sample_xml_filename = f"sample_{submission.id}.xml"
                submission_xml_filename = f"submission_{submission.id}.xml"
                with open(sample_xml_filename, 'w') as sample_file:
                    sample_file.write(submission.sample_object_xml)
                with open(submission_xml_filename, 'w') as submission_file:
                    submission_file.write(submission.submission_object_xml)

                # Prepare files for submission
                files = {
                    'SUBMISSION': (submission_xml_filename, open(submission_xml_filename, 'rb')),
                    'SAMPLE': (sample_xml_filename, open(sample_xml_filename, 'rb')),
                }

                # Prepare authentication
                auth = (settings.ENA_USERNAME, settings.ENA_PASSWORD)
                print(f"Current ENA password: {settings.ENA_PASSWORD}")
                # Make the request
                response = requests.post(
                    "https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/",
                    files=files,
                    auth=auth
                )

                # Close the files
                files['SUBMISSION'][1].close()
                files['SAMPLE'][1].close()

                if response.status_code == 200:
                    # Parse the XML response
                    root = ET.fromstring(response.content)
                    receipt_xml = ET.tostring(root, encoding='unicode')
                    submission.receipt_xml = receipt_xml
                    submission.save()
                    self.message_user(request, "Submission registered successfully.", messages.SUCCESS)
                else:
                    logger.error(f"Failed to register submission {submission.id}. Response: {response.content}")
                    self.message_user(request, "Failed to register submission.", messages.ERROR)
            except Exception as e:
                logger.exception(f"Error registering submission {submission.id}: {e}")
                self.message_user(request, "An error occurred while registering the submission.", messages.ERROR)

    register_sample.short_description = "Register sample with ENA"

admin.site.register(Submission, SubmissionAdmin)