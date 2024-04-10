import os
import random
import gzip
from django.contrib import admin
from django.shortcuts import render 
from django.conf import settings
from Bio import SeqIO
from io import StringIO
from .models import Order, Sample, Submission
from .forms import CreateGZForm
from django.template.loader import render_to_string


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

        xml_content = render_to_string('admin/app/sample/sample_xml_template.xml', context)
        submission.sample_object_xml = xml_content
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
    list_display = ('id', 'order', 'sample_count', 'accession_status')
    list_filter = ('accession_status',)
    search_fields = ('order__name', 'samples__title', 'sample_accession_number', 'samea_accession_number')

    def sample_count(self, obj):
        return obj.samples.count()
    sample_count.short_description = 'Number of Samples'

admin.site.register(Submission, SubmissionAdmin)