import os
import random
import time
import subprocess
import gzip
import requests
from django.contrib import admin, messages
from django.shortcuts import render 
from django.core.files.base import ContentFile
from django.conf import settings
from Bio import SeqIO
from io import StringIO
from .models import Order, Sample, Submission, Pipelines
from .forms import CreateGZForm
from django.template.loader import render_to_string
from xml.etree import ElementTree as ET
import logging

logger = logging.getLogger(__name__)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'date', 'quote_no', 'billing_address', 'ag_and_hzi', 'contact_phone', 'email', 'data_delivery', 'signature', 'experiment_title', 'dna', 'rna', 'library', 'method', 'buffer', 'organism', 'isolated_from', 'isolation_method')

class SampleAdmin(admin.ModelAdmin):
    list_display = ('order', 'sample_name', 'alias', 'title', 'taxon_id', 'scientific_name', 'investigation_type', 'study_type', 'platform', 'library_source', 'concentration', 'volume', 'ratio_260_280', 'ratio_260_230', 'comments', 'date', 'mixs_metadata_standard', 'mixs_metadata', 'filename_forward', 'filename_reverse', 'nf_core_mag_outdir', 'status')
    actions = ['generate_xml_and_create_submission', 'run_mag_pipeline']

    def run_mag_pipeline(self, request, queryset):
        
        selected_samples = queryset

        # Generate a unique run_id
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)
        run_id = f"{timestamp}_{random_num}"

        pipeline = Pipelines.objects.create(run_id=run_id)
        pipeline.samples.set(selected_samples)

        # Generate samplesheet.csv
        samplesheet_content = "sample,group,short_reads_1,short_reads_2,long_reads\n"
        for sample in selected_samples:
            samplesheet_content += f"{sample.alias},0,{sample.filename_forward},{sample.filename_reverse},\n"
        samplesheet_path = os.path.join(settings.MEDIA_ROOT, 'sample_files', f"{run_id}_samplesheet.csv")
        with open(samplesheet_path, 'w') as file:
            file.write(samplesheet_content)
        logger.info(f"Generated samplesheet.csv at: {samplesheet_path}")

        # Generate config file
        config_path = os.path.join(settings.MEDIA_ROOT, 'sample_files', f"{run_id}.config")
        test_config_path = os.path.join(settings.MEDIA_ROOT,'sample_files', "test.config")
        with open(test_config_path, 'r') as file:
            config_content = file.read()
        config_content = config_content.replace("input                         = 'samplesheet.csv'", f"input                         = '{samplesheet_path}'")
        with open(config_path, 'w') as file:
            file.write(config_content)
        logger.info(f"Generated config file at: {config_path}")

        # Run nextflow command
        output_folder = os.path.join(settings.MEDIA_ROOT, 'sample_files', f"{run_id}_out")
        log_path = os.path.join(output_folder, f"{run_id}.log")
        command = f"nextflow run nf-core/mag -profile docker -c {config_path} --outdir {output_folder}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        # Save pipeline details
        pipeline.status = 'running'
        pipeline.output_folder = output_folder
        with open(log_path, 'w') as file:
            file.write(stdout.decode())
        pipeline.save()

        self.message_user(request, f'Started MAG pipeline for {selected_samples.count()} samples')

    run_mag_pipeline.short_description = 'Run MAG pipeline'

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


class PipelinesAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'status', 'output_folder', 'sample_count', 'order')
    
    def sample_count(self, obj):
        return obj.samples.count()
    sample_count.short_description = 'Number of Samples'
    
    def order(self, obj):
        samples = obj.samples.all()
        if samples:
            return samples.first().order
        return None
    order.short_description = 'Order'

admin.site.register(Pipelines, PipelinesAdmin)