import os
import random
from django.contrib import admin
from django.conf import settings
from .models import Order, Sample

def generate_fastq_content(num_reads=1000):
    bases = ['A', 'T', 'G', 'C']
    fastq_content = ""
    for i in range(num_reads):
        read_id = f"@read{i+1}"
        sequence = ''.join(random.choices(bases, k=100))
        quality_scores = ''.join(['I'] * 100)
        fastq_content += f"{read_id}\n{sequence}\n+\n{quality_scores}\n"
    return fastq_content


def add_example_filenames(modeladmin, request, queryset):
    sample_files_dir = os.path.join(settings.MEDIA_ROOT, 'sample_files')
    os.makedirs(sample_files_dir, exist_ok=True)

    for sample in queryset:
        sample.filename_forward = f"sample_files/Sample{sample.id}_R1.fastq"
        sample.filename_reverse = f"sample_files/Sample{sample.id}_R2.fastq"
        sample.save()

        # Create the sample files
        forward_file_path = os.path.join(settings.MEDIA_ROOT, sample.filename_forward)
        reverse_file_path = os.path.join(settings.MEDIA_ROOT, sample.filename_reverse)

        with open(forward_file_path, 'w') as forward_file, open(reverse_file_path, 'w') as reverse_file:
            forward_file.write(generate_fastq_content())
            reverse_file.write(generate_fastq_content())

    modeladmin.message_user(request, f"Example filenames and simulated fastq files added for {queryset.count()} samples.")

add_example_filenames.short_description = "Simulate data for samples"

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'date', 'quote_no', 'billing_address', 'ag_and_hzi', 'contact_phone', 'email', 'data_delivery', 'signature', 'experiment_title', 'dna', 'rna', 'library', 'method', 'buffer', 'organism', 'isolated_from', 'isolation_method')

class SampleAdmin(admin.ModelAdmin):
    list_display = ('order', 'id', 'concentration', 'volume', 'ratio_260_280', 'ratio_260_230', 'comments', 'date', 'mixs_metadata_standard', 'mixs_metadata',  'filename_forward', 'filename_reverse', 'status')
    actions = [add_example_filenames]

admin.site.register(Order, OrderAdmin)
admin.site.register(Sample, SampleAdmin)