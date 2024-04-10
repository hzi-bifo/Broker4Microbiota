import os
import random
import gzip
from django.contrib import admin
from django.shortcuts import render 
from django.conf import settings
from Bio import SeqIO
from io import StringIO
from .models import Order, Sample
from .forms import CreateGZForm

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

def unpack_gz(modeladmin, request, queryset):
    for sample in queryset:
        forward_file_path = os.path.join(settings.MEDIA_ROOT, sample.filename_forward)
        reverse_file_path = os.path.join(settings.MEDIA_ROOT, sample.filename_reverse)

        if sample.filename_forward.endswith('.gz'):
            sample.filename_forward = sample.filename_forward[:-3]
            sample.save()

        if sample.filename_reverse.endswith('.gz'):
            sample.filename_reverse = sample.filename_reverse[:-3]
            sample.save()

        with gzip.open(forward_file_path, 'rt') as forward_gz, open(forward_file_path[:-3], 'wt') as forward_file:
            forward_file.write(forward_gz.read())

        with gzip.open(reverse_file_path, 'rt') as reverse_gz, open(reverse_file_path[:-3], 'wt') as reverse_file:
            reverse_file.write(reverse_gz.read())

        os.remove(forward_file_path)
        os.remove(reverse_file_path)

    modeladmin.message_user(request, f"Unpacked GZ files for {queryset.count()} samples.")

unpack_gz.short_description = "Unpack GZ"


def validate_fastq_files(modeladmin, request, queryset):
    for sample in queryset:
        forward_file_path = os.path.join(settings.MEDIA_ROOT, sample.filename_forward)
        reverse_file_path = os.path.join(settings.MEDIA_ROOT, sample.filename_reverse)

        try:
            with open(forward_file_path, 'r') as forward_file:
                forward_content = forward_file.read()
                SeqIO.parse(StringIO(forward_content), 'fastq')

            with open(reverse_file_path, 'r') as reverse_file:
                reverse_content = reverse_file.read()
                SeqIO.parse(StringIO(reverse_content), 'fastq')

            sample.status = 'Valid FASTQ'
            sample.save()
        except Exception as e:
            sample.status = 'Invalid FASTQ'
            sample.save()
            modeladmin.message_user(request, f"Error validating FASTQ files for Sample {sample.id}: {str(e)}", level=40)

    modeladmin.message_user(request, f"FASTQ validation completed for {queryset.count()} samples.")


class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'date', 'quote_no', 'billing_address', 'ag_and_hzi', 'contact_phone', 'email', 'data_delivery', 'signature', 'experiment_title', 'dna', 'rna', 'library', 'method', 'buffer', 'organism', 'isolated_from', 'isolation_method')


class SampleAdmin(admin.ModelAdmin):
    list_display = ('order', 'id', 'concentration', 'volume', 'ratio_260_280', 'ratio_260_230', 'comments', 'date', 'mixs_metadata_standard', 'mixs_metadata', 'filename_forward', 'filename_reverse', 'nf_core_mag_outdir', 'status')
    actions = [add_example_filenames, validate_fastq_files, 'create_gz', unpack_gz]

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

    def create_gz(self, request, queryset):
        if 'apply' in request.POST:
            form = CreateGZForm(request.POST)
            if form.is_valid():
                compression_level = form.cleaned_data['compression_level']
                for sample in queryset:
                    forward_file_path = os.path.join(settings.MEDIA_ROOT, sample.filename_forward)
                    reverse_file_path = os.path.join(settings.MEDIA_ROOT, sample.filename_reverse)

                    if not sample.filename_forward.endswith('.gz'):
                        sample.filename_forward += '.gz'
                        sample.save()

                    if not sample.filename_reverse.endswith('.gz'):
                        sample.filename_reverse += '.gz'
                        sample.save()

                    with open(forward_file_path, 'rt') as forward_file, gzip.open(forward_file_path + '.gz', 'wt', compresslevel=compression_level) as forward_gz:
                        forward_gz.write(forward_file.read())

                    with open(reverse_file_path, 'rt') as reverse_file, gzip.open(reverse_file_path + '.gz', 'wt', compresslevel=compression_level) as reverse_gz:
                        reverse_gz.write(reverse_file.read())

                    os.remove(forward_file_path)
                    os.remove(reverse_file_path)

                self.message_user(request, f"Created GZ files for {queryset.count()} samples with compression level {compression_level}.")
                return
        else:
            form = CreateGZForm()

        return render(request, 'admin/create_gz_form.html', {'form': form, 'samples': queryset, 'title': 'Create GZ'})

    create_gz.short_description = "Create GZ"

admin.site.register(Order, OrderAdmin)
admin.site.register(Sample, SampleAdmin)