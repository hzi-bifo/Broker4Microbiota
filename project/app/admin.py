import os
import random
import time
import subprocess
import gzip
import requests
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe 
from django.core.files.base import ContentFile
from django.conf import settings
from Bio import SeqIO
from io import StringIO
from .models import Order, Sample, SampleSubmission, ReadSubmission, Pipelines, Read, Project, ProjectSubmission, MagRun, SubMGRun, Bin, Assembly, SAMPLE_TYPE_NORMAL, SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG, Alignment, Mag, SiteSettings, StatusNote

from .forms import CreateGZForm
from django.template.loader import render_to_string
from xml.etree import ElementTree as ET
import logging
import json
import shutil
from pathlib import Path
from django_q.tasks import async_task, result
from . import hooks, async_calls
import importlib
import hashlib
from .utils import calculate_md5, gzip_file

logger = logging.getLogger(__name__)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'name', 'status', 'date', 'platform', 'sequencing_instrument', 'library_strategy', 'experiment_title', 'organism', 'email', 'submitted')
    list_filter = ('status', 'submitted', 'platform', 'library_strategy', 'date')
    search_fields = ('name', 'experiment_title', 'email', 'organism', 'project__title')
    readonly_fields = ('id', 'status_updated_at', 'submitted')
    
    fieldsets = (
        ('Project Information', {
            'fields': ('project', 'name', 'status', 'status_updated_at', 'submitted')
        }),
        ('Contact Information', {
            'fields': ('billing_address', 'ag_and_hzi', 'contact_phone', 'email', 'date', 'quote_no', 'signature')
        }),
        ('Experiment Details', {
            'fields': ('experiment_title', 'data_delivery', 'dna', 'rna', 'method', 'buffer', 'organism', 'isolated_from', 'isolation_method')
        }),
        ('Sequencing Configuration', {
            'fields': ('platform', 'sequencing_instrument', 'library', 'library_name', 'library_source', 'library_selection', 'library_strategy', 'insert_size')
        }),
        ('System Information', {
            'fields': ('checklist_changed', 'status_notes'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(Order, OrderAdmin)


class StatusNoteAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'note_type', 'created_at', 'is_rejection')
    list_filter = ('note_type', 'is_rejection', 'created_at')
    search_fields = ('order__id', 'user__username', 'content')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

admin.site.register(StatusNote, StatusNoteAdmin)


class SiteSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for SiteSettings model.
    Ensures only one instance can exist and provides a user-friendly interface.
    """
    # Organize fields into logical groups
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'organization_name', 'organization_short_name', 'tagline')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'website_url')
        }),
        ('Branding', {
            'fields': ('logo', 'favicon'),
            'description': 'Upload your organization\'s logo and favicon. Recommended sizes: Logo 200x50px, Favicon 32x32px'
        }),
        ('Appearance', {
            'fields': ('primary_color', 'secondary_color'),
            'description': 'Customize the color scheme of your application'
        }),
        ('Footer', {
            'fields': ('footer_text',),
            'description': 'Additional footer content (HTML allowed)'
        }),
        ('Empty State Messages', {
            'fields': ('empty_projects_text', 'projects_with_samples_text'),
            'description': 'Messages shown on the project list page in different states'
        }),
        ('Form Customization', {
            'fields': ('project_form_title', 'project_form_description', 'order_form_title', 'order_form_description'),
            'description': 'Customize form titles and descriptions'
        }),
        ('Order Submission', {
            'fields': ('submission_instructions',),
            'description': 'Instructions shown after order submission'
        }),
        ('ENA (European Nucleotide Archive) Settings', {
            'fields': ('ena_username', 'ena_password_display', 'ena_password', 'ena_test_mode', 'ena_center_name'),
            'description': 'Configure ENA credentials and settings for project/sample submissions',
            'classes': ('wide',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'ena_password_display')
    
    def ena_password_display(self, obj):
        """Display masked password or empty message"""
        if obj.ena_password:
            return "••••••••"  # Password is set (masked)
        return "Not set"
    ena_password_display.short_description = "Current ENA Password"
    
    def get_form(self, request, obj=None, **kwargs):
        """Custom form handling for password field"""
        form = super().get_form(request, obj, **kwargs)
        
        # Replace the ena_password field with a custom password input
        if 'ena_password' in form.base_fields:
            from django import forms
            form.base_fields['ena_password'] = forms.CharField(
                label='New ENA Password',
                required=False,
                widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
                help_text='Enter a new password to change it. Leave blank to keep current password.'
            )
        
        return form
    
    def save_model(self, request, obj, form, change):
        """Handle password encryption when saving"""
        if 'ena_password' in form.cleaned_data:
            new_password = form.cleaned_data.get('ena_password')
            if new_password:  # Only update if a new password was provided
                obj.set_ena_password(new_password)
        
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        """
        Prevent adding more than one SiteSettings instance
        """
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of SiteSettings
        """
        return False
    
    def changelist_view(self, request, extra_context=None):
        """
        Redirect to the edit page if an instance exists,
        otherwise show the add page
        """
        if SiteSettings.objects.exists():
            obj = SiteSettings.objects.first()
            return redirect(f'/admin/app/sitesettings/{obj.pk}/change/')
        else:
            return redirect('/admin/app/sitesettings/add/')
    
    class Media:
        css = {
            'all': ('css/admin-sitesettings.css',)
        }
        js = ('js/admin-sitesettings.js',)

admin.site.register(SiteSettings, SiteSettingsAdmin)


class ReadAdmin(admin.ModelAdmin):
    list_display = ('id', 'sample', 'file_1', 'file_2', 'experiment_accession_number', 'run_accession_number', 'submitted')
    list_filter = ('submitted', 'sample__order__project')
    search_fields = ('sample__sample_id', 'experiment_accession_number', 'run_accession_number', 'file_1', 'file_2')
    readonly_fields = ('id', 'read_file_checksum_1', 'read_file_checksum_2', 'experiment_accession_number', 'run_accession_number', 'submitted')
    
    fieldsets = (
        ('Sample Association', {
            'fields': ('sample',)
        }),
        ('File Information', {
            'fields': ('file_1', 'file_2', 'uncompressed_file_1', 'uncompressed_file_2', 'read_file_checksum_1', 'read_file_checksum_2')
        }),
        ('ENA Information', {
            'fields': ('submitted', 'experiment_accession_number', 'run_accession_number')
        }),
    )

    actions = ['generate_xml_and_create_read_submission', 'create_mag_run']

    def generate_xml_and_create_read_submission(self, request, queryset):
        selected_reads = queryset

        read_submission = ReadSubmission.objects.create(read_object_txt_list=json.dumps([]))

        txt_list = {}
        for read in selected_reads:
            context = {
                'read': read,
                'project': read.sample.order.project,
                'sample': read.sample,
                'order': read.sample.order,
            }
            read_txt_content = render_to_string('admin/app/sample/read_manifest.txt', context)
            txt_list[read.sample_id] = read_txt_content
        read_submission.read_object_txt_list = json.dumps(txt_list)
        read_submission.name = f"{read.sample.sample_id}"

        read_submission.save()

        self.message_user(request, f'Successfully created ReadSubmission {read_submission.name} with {selected_reads.count()} samples')


    generate_xml_and_create_read_submission.short_description = 'Generate XML and create Read Submission'

    def create_mag_run(self, request, queryset):
        selected_reads = queryset

        mag_run = MagRun.objects.create()
        mag_run.reads.set(selected_reads)
        
        context = {
            'reads': selected_reads,
        }
        samplesheet_content = render_to_string('admin/app/sample/mag_samplesheet.csv', context)
        mag_run.samplesheet_content = samplesheet_content.rstrip()

        context = {
            'settings': settings,
        }
        cluster_config = render_to_string('admin/app/sample/mag_cluster_config.cfg', context)
        mag_run.cluster_config = cluster_config

        mag_run.save()

        self.message_user(request, f'Successfully created MAG run')


    create_mag_run.short_description = 'Create a MAG run'

admin.site.register(Read, ReadAdmin)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'alias', 'description', 'study_accession_id', 'alternative_accession_id', 'submitted', 'ena_status')
    list_filter = ('submitted', 'user')
    search_fields = ('title', 'alias', 'description', 'study_accession_id', 'alternative_accession_id', 'user__username', 'user__email')
    readonly_fields = ('id', 'ena_status')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'alias', 'description')
        }),
        ('ENA Information', {
            'fields': ('submitted', 'study_accession_id', 'alternative_accession_id', 'ena_status'),
            'description': 'European Nucleotide Archive (ENA) submission details'
        }),
    )

    def ena_status(self, obj):
        """Display ENA registration status"""
        if obj.submitted:
            status = '<span style="color: green;">✓ Registered</span>'
            if obj.study_accession_id:
                status += f'<br><small>Accession: {obj.study_accession_id}</small>'
            return mark_safe(status)
        else:
            return mark_safe('<span style="color: gray;">Not Registered</span>')
    
    ena_status.short_description = 'ENA Status'

    actions = ['generate_xml_and_create_project_submission', 'generate_submg_run_including_children']

    def generate_xml_and_create_project_submission(self, request, queryset):
        selected_projects = queryset

        project_submission = ProjectSubmission.objects.create()

        context = {
            'projects': selected_projects
        }

        project_xml_content = render_to_string('admin/app/sample/project_xml_template.xml', context)
        project_submission.project_object_xml = project_xml_content

        file_path = os.path.join(settings.BASE_DIR, 'app', 'templates', 'admin', 'app', 'sample', 'submission_template.xml')
        with open(file_path, 'r') as file:
            submission_xml_content = file.read()
            print(submission_xml_content)  # Debugging: Check the content

        project_submission.submission_object_xml = submission_xml_content

        project_submission.save()

        self.message_user(request, f'Successfully created ProjectSubmission {project_submission.id} with {selected_projects.count()} projects')

    generate_xml_and_create_project_submission.short_description = 'Generate XML and create Project Submission'

    def generate_submg_run_including_children(self, request, queryset):

        # create dependency object, which is a dictionary of object lists
        projects = []
        orders = []
        samples = []
        assembly_samples = []
        bin_samples = []
        mag_samples = []
        reads = []
        assemblys = []
        bins = []
        alignments = []

        for project in queryset:
            if not project.submitted and project not in projects:
                projects.append(project)
            for order in project.order_set.all():
                if not order.submitted and order not in orders:
                    orders.append(order)
                for sample in order.sample_set.filter(sample_type=SAMPLE_TYPE_NORMAL):
                    # dependencies
                    if not sample.submitted and sample not in samples:
                        samples.append(sample)         
                    # Get all reads for this sample
                    for read in sample.read_set.all():
                        if not read.submitted and read not in reads:
                            reads.append(read)
                        # Get all assemblies for this order
                for assembly in order.assembly_set.all():
                    if not assembly.submitted and assembly not in assemblys:
                        assemblys.append(assembly)
                    # Get all assembly samples for this assembly

                    for assembly_sample in Sample.objects.filter(sample_type=SAMPLE_TYPE_ASSEMBLY, assembly=assembly):
                       if not assembly_sample.submitted and assembly_sample not in samples:
                           assembly_samples.append(assembly_sample)
                    
                    # Get all bins for this order           
                for bin in order.bin_set.all():
                    if not bin.submitted and bin not in bins:
                        bins.append(bin)
                    # Get all bin samples for this bin

                    for bin_sample in Sample.objects.filter(sample_type=SAMPLE_TYPE_BIN, bin=bin):
                       if not bin_sample.submitted and bin_sample not in samples:
                           bin_samples.append(bin_sample)

                    # Get all mag samples for this bin
                    for mag_sample in Sample.objects.filter(sample_type=SAMPLE_TYPE_MAG, bin=bin):
                        if not mag_sample.submitted and mag_sample not in samples:
                            mag_samples.append(mag_sample)
                            
                for alignment in order.alignment_set.all():
                    if not alignment.submitted and alignment not in alignments:
                        alignments.append(alignment)

            yaml = []
            yaml.extend(project.getSubMGYAML())

            tax_id = []
            scientific_name = []
            for sample in Sample.objects.filter(sample_type=SAMPLE_TYPE_MAG, order=order):
                tax_id = sample.getSubMGTaxId(tax_id)
                scientific_name = sample.getSubMGScientificName(scientific_name)
            
            if len(tax_id) != 1:
                raise Exception(f"No tax id found for samples")
            if len(scientific_name) != 1:
                raise Exception(f"No scientific name found for sample")
            yaml.extend(sample.getSubMGTaxIdYAML(tax_id))
            yaml.extend(sample.getSubMGScientificNameYAML(scientific_name))
            
            sequencingPlatforms = []
            for order in orders:
                sequencingPlatforms = order.getSubMGSequencingPlatforms(sequencingPlatforms)
                yaml.extend(order.getSubMGYAML(sequencingPlatforms))
            yaml.extend(Sample.getSubMGYAMLHeader())
            for sample in samples:
                yaml.extend(sample.getSubMGYAML(SAMPLE_TYPE_NORMAL))

            if reads:
                yaml.extend(Read.getSubMGYAMLHeader())
            for read in reads:
                yaml.extend(read.getSubMGYAML())

            if assemblys:
                yaml.extend(Assembly.getSubMGYAMLHeader())
            for assembly in assemblys:
                yaml.extend(assembly.getSubMGYAML())
            # if len(assembly_samples) != 1:
            #    raise Exception(f"Multiple assembly samples found for assembly")
            for assembly_sample in assembly_samples:
               yaml.extend(assembly_sample.getSubMGYAML(SAMPLE_TYPE_ASSEMBLY))
            if assemblys:   
               yaml.extend(Assembly.getSubMGYAMLFooter())

            if bins:
                yaml.extend(Bin.getSubMGYAMLHeader())
            for bin in bins:
                yaml.extend(bin.getSubMGYAML())
                break
            tax_ids = {}
            tax_ids_content = ""
            for bin_sample in bin_samples:
                bin = bin_sample.bin
                tax_ids[bin.file.split('/')[-1].replace(".fa", "")] = [bin_sample.scientific_name, bin_sample.tax_id]
            for bin in bins:
                yaml.extend(bin.getSubMGYAMLTaxIDYAML())
                tax_ids_content = bin.getSubMGYAMLTaxIDContent(tax_ids)
                break 
            for bin_sample in bin_samples:
               yaml.extend(bin_sample.getSubMGYAML(SAMPLE_TYPE_BIN))
               break
            if bins:
               yaml.extend(Bin.getSubMGYAMLFooter())

            if mag_samples:
                yaml.extend(Mag.getSubMGYAMLHeader())
            mag_data = {}
            for mag_sample in mag_samples:
                bin = mag_sample.bin
                mag_data[bin.bin_number] = mag_sample.mag_data
            for mag_sample in mag_samples:
                yaml.extend(Mag.getSubMGYAMLMagDataYAML(mag_sample.mag_data))
                break
            for mag_sample in mag_samples:
                yaml.extend(mag_sample.getSubMGYAML(SAMPLE_TYPE_MAG))
                break

            if alignments:
                yaml.extend(Alignment.getSubMGYAMLHeader())
            for alignment in alignments:
                yaml.extend(alignment.getSubMGYAML())
                break

            subMG_run = SubMGRun.objects.create(order=order)
            output = '\n'.join(yaml)
            if bins:
                subMG_run.tax_ids = tax_ids_content
            subMG_run.yaml = output
 
            output_file_path = "/tmp/output.txt"

            with open(output_file_path, 'w') as output_file:
                print(output, file=output_file)
 
            subMG_run.save()

        return
    
    generate_submg_run_including_children.short_description = 'Generate SubMG run for this object, all dependencies, and all child objects'

admin.site.register(Project, ProjectAdmin)


class SampleAdmin(admin.ModelAdmin):
    list_display = ('id', 'sample_id', 'sample_alias', 'order', 'sample_type', 'scientific_name', 'tax_id', 'sample_accession_number', 'submitted', 'status')
    list_filter = ('sample_type', 'submitted', 'status', 'order__project')
    search_fields = ('sample_id', 'sample_alias', 'scientific_name', 'tax_id', 'sample_accession_number', 'sample_biosample_number', 'sample_title')
    readonly_fields = ('id', 'sample_accession_number', 'sample_biosample_number', 'submitted')
    
    fieldsets = (
        ('Sample Identification', {
            'fields': ('order', 'sample_type', 'sample_id', 'sample_alias', 'sample_title', 'sample_description', 'status')
        }),
        ('Taxonomy', {
            'fields': ('scientific_name', 'tax_id')
        }),
        ('ENA Information', {
            'fields': ('submitted', 'sample_accession_number', 'sample_biosample_number')
        }),
        ('Assembly/MAG Information', {
            'fields': ('assembly', 'bin', 'mag_data'),
            'classes': ('collapse',)
        }),
    )

    # temporary - this needs to be passed through properly
    # checklists = ['GSC_MIxS_wastewater_sludge']
    # checklists = ['GSC_MIxS_wastewater_sludge', 'GSC_MIxS_miscellaneous_natural_or_artificial_environment']

    # get checklists used for this model (from the sample? - array of checklist names?)
    # get fields from each checklist
    # use the fields to create a list_display

    # temporary: get fields named alias, name, taxon_id from the set in use

    # Change XML template to use all attributes for each sample

    # proper set of checklists for GMAK, ENA

    actions = ['generate_xml_and_create_sample_submission', 'create_test_reads']

    # def run_mag_pipeline(self, request, queryset):
        
    #     selected_samples = queryset

    #     # Generate a unique run_id
    #     timestamp = int(time.time())
    #     random_num = random.randint(1000, 9999)
    #     run_id = f"{timestamp}_{random_num}"

    #     pipeline = Pipelines.objects.create(run_id=run_id)
    #     pipeline.samples.set(selected_samples)

    #     # Generate samplesheet.csv
    #     samplesheet_content = "sample,group,short_reads_1,short_reads_2,long_reads\n"
    #     for sample in selected_samples:
    #         samplesheet_content += f"{sample.alias},0,{sample.filename_forward},{sample.filename_reverse},\n"
    #     samplesheet_path = os.path.join(settings.MEDIA_ROOT, 'sample_files', f"{run_id}_samplesheet.csv")
    #     with open(samplesheet_path, 'w') as file:
    #         file.write(samplesheet_content)
    #     logger.info(f"Generated samplesheet.csv at: {samplesheet_path}")

    #     # Generate config file
    #     config_path = os.path.join(settings.MEDIA_ROOT, 'sample_files', f"{run_id}.config")
    #     test_config_path = os.path.join(settings.MEDIA_ROOT,'sample_files', "test.config")
    #     with open(test_config_path, 'r') as file:
    #         config_content = file.read()
    #     config_content = config_content.replace("input                         = 'samplesheet.csv'", f"input                         = '{samplesheet_path}'")
    #     with open(config_path, 'w') as file:
    #         file.write(config_content)
    #     logger.info(f"Generated config file at: {config_path}")

    #     # Run nextflow command
    #     output_folder = os.path.join(settings.MEDIA_ROOT, 'sample_files', f"{run_id}_out")
    #     log_path = os.path.join(output_folder, f"{run_id}.log")
    #     command = f"nextflow run nf-core/mag -profile docker -c {config_path} --outdir {output_folder}"
    #     process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     stdout, stderr = process.communicate()

    #     # Save pipeline details
    #     pipeline.status = 'running'
    #     pipeline.output_folder = output_folder
    #     with open(log_path, 'w') as file:
    #         file.write(stdout.decode())
    #     pipeline.save()

    #     self.message_user(request, f'Started MAG pipeline for {selected_samples.count()} samples')

    # run_mag_pipeline.short_description = 'Run MAG pipeline'



    def create_test_reads(self, request, queryset):

        template_number = 1
        for sample in queryset:

            # uncompressed_template_1 = os.path.join(settings.LOCAL_DIR, '..', 'template_1.fastq')
            # uncompressed_template_2 = os.path.join(settings.LOCAL_DIR, '..', 'template_2.fastq')
            # uncompressed_paired_read_1 = os.path.join(settings.LOCAL_DIR, sample.sample_alias + '_1.fastq')
            # uncompressed_paired_read_2 = os.path.join(settings.LOCAL_DIR, sample.sample_alias + '_2.fastq')

            template_1_path = f"template_{template_number}_1.fastq.gz"
            template_2_path = f"template_{template_number}_2.fastq.gz"

            template_1 = os.path.join(settings.LOCAL_DIR, '..', template_1_path)
            template_2 = os.path.join(settings.LOCAL_DIR, '..', template_2_path)
            paired_read_1 = os.path.join(settings.LOCAL_DIR, sample.sample_alias + '_1.fastq.gz')
            paired_read_2 = os.path.join(settings.LOCAL_DIR, sample.sample_alias + '_2.fastq.gz')

            # temporary
            shutil.copyfile(template_1, paired_read_1)
            shutil.copyfile(template_2, paired_read_2)

            # shutil.copyfile(uncompressed_template_1, uncompressed_paired_read_1)
            # shutil.copyfile(uncompressed_template_2, uncompressed_paired_read_2)            

            # gzip_file(uncompressed_paired_read_1, paired_read_1)
            # gzip_file(uncompressed_paired_read_2, paired_read_2)

            paired_read_1_hash = calculate_md5(paired_read_1)
            paired_read_2_hash = calculate_md5(paired_read_2)

            if os.path.isfile(paired_read_1) and os.path.isfile(paired_read_2):
                read = Read.objects.create(sample=sample, file_1=paired_read_1, file_2=paired_read_2, read_file_checksum_1=paired_read_1_hash, read_file_checksum_2=paired_read_2_hash)
                read.save()

            template_number += 1

    create_test_reads.short_description = 'Generate reads'




    def generate_xml_and_create_sample_submission(self, request, queryset):
        selected_samples = queryset

        sampleSubmission = SampleSubmission.objects.create()
        sampleSubmission.samples.set(selected_samples)

        context = {
            'samples': selected_samples,
        }

        sample_xml_content = render_to_string('admin/app/sample/sample_xml_template.xml', context)
        sampleSubmission.sample_object_xml = sample_xml_content

        file_path = os.path.join(settings.BASE_DIR, 'app', 'templates', 'admin', 'app', 'sample', 'submission_template.xml')
        with open(file_path, 'r') as file:
            sampleSubmission_xml_content = file.read()
            print(sampleSubmission_xml_content)  # Debugging: Check the content

        sampleSubmission.sampleSubmission_object_xml = sampleSubmission_xml_content

        sampleSubmission.save()

        self.message_user(request, f'Successfully created SampleSubmission {sampleSubmission.id} with {selected_samples.count()} samples')

    generate_xml_and_create_sample_submission.short_description = 'Generate XML and create SampleSubmission'

    # def generate_submg_run(self, request, queryset):

    #     # create dependency object, which is a dictionary of object lists
    #     projects = []
    #     samples = []
    #     reads = []
    #     assemblies = []
    #     bins = []
    #     # if normal sample, each order and project, checking if already submitted (and mark as submitted), and whether already in list (don't add more than once)
    #     for sample in queryset:
    #         if not sample.submitted and sample not in samples:
    #             samples.append(sample)
    #             order = sample.order
    #             project = order.project
    #             if not project.submitted and project not in projects:
    #                 projects.append(project)

    #     subMG_run = SubMGRun.objects.create(order=order)
    #     subMG_run.projects.set(projects)
    #     subMG_run.samples.set(samples)
    #     subMG_run.reads.set(reads)
    #     subMG_run.assemblys.set(assemblies)
    #     subMG_run.bins.set(bins)
    #     subMG_run.save()

    #     return

    # generate_submg_run.short_description = 'Generate SubMG run for this object and all dependencies'



admin.site.register(Sample, SampleAdmin)



class SampleSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'sample_count', 'accession_status', 'has_sample_xml', 'has_submission_xml', 'has_receipt')
    list_filter = ('accession_status',)
    readonly_fields = ('id', 'accession_status', 'receipt_xml', 'get_samples_display')
    
    fieldsets = (
        ('Submission Information', {
            'fields': ('id', 'accession_status', 'get_samples_display')
        }),
        ('XML Files', {
            'fields': ('sample_object_xml', 'sampleSubmission_object_xml', 'receipt_xml'),
            'classes': ('collapse', 'wide')
        }),
    )
    
    actions = ['register_samples']

    def sample_count(self, obj):
        return obj.samples.count()
    sample_count.short_description = 'Number of Samples'
    
    def has_sample_xml(self, obj):
        return bool(obj.sample_object_xml)
    has_sample_xml.boolean = True
    has_sample_xml.short_description = 'Sample XML'
    
    def has_submission_xml(self, obj):
        return bool(obj.sampleSubmission_object_xml)
    has_submission_xml.boolean = True
    has_submission_xml.short_description = 'Submission XML'
    
    def has_receipt(self, obj):
        return bool(obj.receipt_xml)
    has_receipt.boolean = True
    has_receipt.short_description = 'Receipt'
    
    def get_samples_display(self, obj):
        samples = obj.samples.all()[:10]
        if samples:
            sample_list = [f"Sample {s.sample_id} ({s.scientific_name})" for s in samples]
            result = '\n'.join(sample_list)
            if obj.samples.count() > 10:
                result += f'\n... and {obj.samples.count() - 10} more'
            return result
        return 'No samples'
    get_samples_display.short_description = 'Associated Samples'

    def register_samples(self, request, queryset):
        for sampleSubmission in queryset:
            try:
                # Save XML content to files for debugging
                sample_xml_filename = os.path.join(settings.LOCAL_DIR, f"sample_{sampleSubmission.id}.xml")
                sampleSubmission_xml_filename = os.path.join(settings.LOCAL_DIR, f"sampleSubmission_{sampleSubmission.id}.xml")
                with open(sample_xml_filename, 'w') as sample_file:
                    sample_file.write(sampleSubmission.sample_object_xml)
                with open(sampleSubmission_xml_filename, 'w') as sampleSubmission_file:
                    sampleSubmission_file.write(sampleSubmission.sampleSubmission_object_xml)

                # Prepare files for sampleSubmission
                files = {
                    'SUBMISSION': (sampleSubmission_xml_filename, open(sampleSubmission_xml_filename, 'rb')),
                    'SAMPLE': (sample_xml_filename, open(sample_xml_filename, 'rb')),
                }

                # Prepare authentication
                from .utils import get_ena_credentials
                ena_username, ena_password, ena_test_mode, ena_center_name = get_ena_credentials()
                
                if not ena_username or not ena_password:
                    self.message_user(request, 'ENA credentials not configured. Please set them in Site Settings.', level=messages.ERROR)
                    return
                
                auth = (ena_username, ena_password)
                # Make the request
                submission_url = "https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/" if ena_test_mode else "https://www.ebi.ac.uk/ena/submit/drop-box/submit/"
                response = requests.post(
                    submission_url,
                    files=files,
                    auth=auth
                )

                # how is checklist supposed to be passed in xml file? - as an attribute, per sample
                # Just one checklist per sample / submission?
                # use v2 rest api
                # need concept of sample sets? Or just one checklist per order? The former, but start with the latter...
                # all actual checklists include default checklist. GMAK is on top of that.
                # so how would this work? Choose at least one checklist, and have any mandatory addtional ones on top from config (ie. GMAK)
                # order passes through checklist names and records include, exclude fields. Units, etc. are in the checklist itself.
                # need to tag checklist used as an attribute
                # need to see what can actually be removed from GMAK
                # or is GMAK the sample??? - no, it's a checklist

                # Close the files
                files['SUBMISSION'][1].close()
                files['SAMPLE'][1].close()

                if response.status_code == 200:
                    # Parse the XML response
                    root = ET.fromstring(response.content)
                    receipt_xml = ET.tostring(root, encoding='unicode')
                    sampleSubmission.receipt_xml = receipt_xml
                    if root.tag == 'RECEIPT':
                        success = root.attrib['success']
                        if success != 'true':
                            raise Exception(f"Failed to register sampleSubmission {sampleSubmission.id}. Response: {response.content}")
                    for child in root:
                        if child.tag == 'SAMPLE':
                                sample_alias = child.attrib['alias']
                                sample_accession_number = child.attrib['accession']
                                sampleSubmission.samples.filter(sample_alias=sample_alias).update(sample_accession_number=sample_accession_number)
                                for grandchild in child:
                                    if grandchild.tag == 'EXT_ID':
                                        sample_biosample_number = grandchild.attrib['accession']
                                        sampleSubmission.samples.filter(sample_alias=sample_alias).update(sample_biosample_number=sample_biosample_number)
                    sampleSubmission.accession_status = 'submitted'
                    sampleSubmission.save()
                    self.message_user(request, "SampleSubmission registered successfully.", messages.SUCCESS)
                else:
                    logger.error(f"Failed to register sampleSubmission {sampleSubmission.id}. Response: {response.content}")
                    self.message_user(request, "Failed to register sampleSubmission.", messages.ERROR)
            except Exception as e:
                logger.exception(f"Error registering sampleSubmission {sampleSubmission.id}: {e}")
                self.message_user(request, "An error occurred while registering the sampleSubmission.", messages.ERROR)

    register_samples.short_description = "Register sample with ENA"

admin.site.register(SampleSubmission, SampleSubmissionAdmin)

class ReadSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sample_count', 'accession_status', 'has_read_manifest', 'has_receipt')
    list_filter = ('accession_status',)
    search_fields = ('name',)
    readonly_fields = ('id', 'name', 'accession_status', 'receipt_xml', 'get_samples_display')
    
    fieldsets = (
        ('Submission Information', {
            'fields': ('id', 'name', 'accession_status', 'get_samples_display')
        }),
        ('Submission Data', {
            'fields': ('read_object_txt_list', 'receipt_xml'),
            'classes': ('collapse', 'wide')
        }),
    )
    
    actions = ['register_reads']

    def sample_count(self, obj):
        return obj.samples.count()
    sample_count.short_description = 'Number of Samples'
    
    def has_read_manifest(self, obj):
        return bool(obj.read_object_txt_list and obj.read_object_txt_list != '[]')
    has_read_manifest.boolean = True
    has_read_manifest.short_description = 'Has Manifest'
    
    def has_receipt(self, obj):
        return bool(obj.receipt_xml)
    has_receipt.boolean = True
    has_receipt.short_description = 'Receipt'
    
    def get_samples_display(self, obj):
        samples = obj.samples.all()[:10]
        if samples:
            sample_list = [f"Sample {s.sample_id}" for s in samples]
            result = '\n'.join(sample_list)
            if obj.samples.count() > 10:
                result += f'\n... and {obj.samples.count() - 10} more'
            return result
        return 'No samples'
    get_samples_display.short_description = 'Associated Samples'

    def register_reads(self, request, queryset):
        for read_submission in queryset:
            count = 0
            read_object_txt_list = json.loads(read_submission.read_object_txt_list)
            for sample_id in read_object_txt_list.keys():
                read = Read.objects.get(sample_id=sample_id)
                read_object_txt = read_object_txt_list[sample_id]
                # Save the read manifest to a file
                read_manifest_filename = os.path.join(settings.LOCAL_DIR, f"read_manifest_{read_submission.id}{count}.txt")
                with open(read_manifest_filename, 'w') as read_manifest_file:
                    read_manifest_file.write(read_object_txt)

                from .utils import get_ena_credentials
                ena_username, ena_password, ena_test_mode, ena_center_name = get_ena_credentials()
                
                if not ena_username or not ena_password:
                    self.message_user(request, 'ENA credentials not configured. Please set them in Site Settings.', level=messages.ERROR)
                    continue
                
                executable = f"java -jar {settings.JAR_LOCATION}"
                context = f"-context reads"
                username = f"-username {ena_username}"
                password = f"-password \"{ena_password}\""
                centre = f"-centerName {ena_center_name}" if ena_center_name else ""
                manifest = f"-manifest {read_manifest_filename}"
                test_flag = "-test" if ena_test_mode else ""
                outputDir = f"-outputDir {settings.LOCAL_DIR}"
                inputDir = f"-inputDir {settings.LOCAL_DIR}"
                # mode = f"-validate"
                mode = f"-submit"

                try:
                    webin_command = f"{executable} {context} {username} {password} {centre} {manifest} {outputDir} {inputDir} {mode} {test_flag}".strip()
                    print(webin_command)
                    process = subprocess.Popen(webin_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()
                    return_code = process.returncode
                    print(f"Stdout: {stdout}")
                    print(f"Stderr: {stderr}")
                    print(f"Return code: {return_code}")

                    if return_code != 0:
                        raise Exception(f"Error registering read submission {read_submission.id}: {stderr}")
                    
                    # Parse the XML response   
                    receipt_filename =  os.path.join(settings.LOCAL_DIR, "reads", f"{read_submission.name}/submit/receipt.xml")
                    with open(receipt_filename, 'r') as receipt_file:
                        receipt_xml = receipt_file.read()
                        root = ET.fromstring(receipt_xml)
                        if root.tag == 'RECEIPT':
                                success = root.attrib['success']
                                if success != 'true':
                                    raise Exception(f"Failed to register read submission {read_submission.id}")
                        for child in root:
                            if child.tag == 'RUN':
                                run_accession_number = child.attrib['accession']
                                # read_submission.samples.filter(sample_id=sample_id).first().reads.filter(sample_id=sample_id).update(run_accession_number=run_accession_number)
                                Read.objects.filter(sample_id=sample_id).update(run_accession_number=run_accession_number)
                            if child.tag == "EXPERIMENT":
                                experiment_accession_number = child.attrib['accession']
                                # read_submission.samples.filter(sample_id=sample_id).first().reads.filter(sample_id=sample_id).update(experiment_accession_number=experiment_accession_number)
                                Read.objects.filter(sample_id=sample_id).update(experiment_accession_number=experiment_accession_number)
                        read_submission.accession_status = 'submitted'
                        read_submission.save()
                        self.message_user(request, "Read submission registered successfully.", messages.SUCCESS)

                except Exception as e:
                    logger.exception(f"Error registering read submission {read_submission.id}: {e}")
                    self.message_user(request, "An error occurred while registering the read submission.", messages.ERROR)
                    
                count = count + 1

    register_reads.short_description = "Register sample with ENA"

admin.site.register(ReadSubmission, ReadSubmissionAdmin)


class ProjectSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_object_xml', 'receipt_xml', 'submission_object_xml', 'accession_status')
    
    actions = ['register_projects']

    def project_count(self, obj):
        return obj.projects.count()
    project_count.short_description = 'Number of Projects'

    def register_projects(self, request, queryset):
        for project_submission in queryset:
            try:
                Path(settings.LOCAL_DIR).mkdir(parents=True, exist_ok=True)
                # Save XML content to files for debugging
                project_xml_filename = os.path.join(settings.LOCAL_DIR, f"project_{project_submission.id}.xml")
                project_submission_xml_filename = os.path.join(settings.LOCAL_DIR, f"submission_{project_submission.id}.xml")
                with open(project_xml_filename, 'w') as project_file:
                    project_file.write(project_submission.project_object_xml)
                with open(project_submission_xml_filename, 'w') as project_submission_file:
                    project_submission_file.write(project_submission.submission_object_xml)

                # Prepare files for submission
                files = {
                    'SUBMISSION': (project_submission_xml_filename, open(project_submission_xml_filename, 'rb')),
                    'PROJECT': (project_xml_filename, open(project_xml_filename, 'rb')),
                }

                # Prepare authentication
                from .utils import get_ena_credentials
                ena_username, ena_password, ena_test_mode, ena_center_name = get_ena_credentials()
                
                if not ena_username or not ena_password:
                    self.message_user(request, 'ENA credentials not configured. Please set them in Site Settings.', level=messages.ERROR)
                    return
                
                auth = (ena_username, ena_password)
                # Make the request
                submission_url = "https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/" if ena_test_mode else "https://www.ebi.ac.uk/ena/submit/drop-box/submit/"
                response = requests.post(
                    submission_url,
                    files=files,
                    auth=auth
                )

                # how is checklist supposed to be passed in xml file? - as an attribute, per sample
                # Just one checklist per sample / submission?
                # use v2 rest api
                # need concept of sample sets? Or just one checklist per order? The former, but start with the latter...
                # all actual checklists include default checklist. GMAK is on top of that.
                # so how would this work? Choose at least one checklist, and have any mandatory addtional ones on top from config (ie. GMAK)
                # order passes through checklist names and records include, exclude fields. Units, etc. are in the checklist itself.
                # need to tag checklist used as an attribute
                # need to see what can actually be removed from GMAK
                # or is GMAK the sample??? - no, it's a checklist

                # Close the files
                files['SUBMISSION'][1].close()
                files['PROJECT'][1].close()

                if response.status_code == 200:
                    # Parse the XML response
                    root = ET.fromstring(response.content)
                    receipt_xml = ET.tostring(root, encoding='unicode')
                    project_submission.receipt_xml = receipt_xml
                    if root.tag == 'RECEIPT':
                        success = root.attrib['success']
                        if success != 'true':
                            raise Exception(f"Failed to register project submission {project_submission.id}. Response: {response.content}")
                    for child in root:
                        if child.tag == 'PROJECT':
                                alias = child.attrib['alias']
                                accession_number = child.attrib['accession']
                                Project.objects.filter(alias=alias).update(study_accession_id=accession_number)
                                for grandchild in child:
                                    if grandchild.tag == 'EXT_ID':
                                        alternative_accession_number = grandchild.attrib['accession']
                                        Project.objects.filter(alias=alias).update(alternative_accession_id=alternative_accession_number)
                    project_submission.accession_status = 'submitted'
                    project_submission.save()
                    self.message_user(request, "Project submission registered successfully.", messages.SUCCESS)
                else:
                    logger.error(f"Failed to register project submission {project_submission.id}. Response: {response.content}")
                    self.message_user(request, "Failed to register project submission.", messages.ERROR)
            except Exception as e:
                logger.exception(f"Error registering project submission {project_submission.id}: {e}")
                self.message_user(request, "An error occurred while registering the project submission.", messages.ERROR)

    register_projects.short_description = "Register sample with ENA"

admin.site.register(ProjectSubmission, ProjectSubmissionAdmin)


class MagRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'get_reads_count', 'get_samplesheet_preview', 'get_cluster_config_preview')
    list_filter = ('status',)
    readonly_fields = ('id', 'status', 'get_reads_display', 'samplesheet_content', 'cluster_config')
    
    fieldsets = (
        ('Run Information', {
            'fields': ('id', 'status')
        }),
        ('Associated Reads', {
            'fields': ('get_reads_display',)
        }),
        ('Configuration Files', {
            'fields': ('samplesheet_content', 'cluster_config'),
            'classes': ('wide',)
        }),
    )
    
    def get_reads_count(self, obj):
        return obj.reads.count()
    get_reads_count.short_description = 'Number of Reads'
    
    def get_samplesheet_preview(self, obj):
        if obj.samplesheet_content:
            return obj.samplesheet_content[:100] + '...' if len(obj.samplesheet_content) > 100 else obj.samplesheet_content
        return '-'
    get_samplesheet_preview.short_description = 'Samplesheet Preview'
    
    def get_cluster_config_preview(self, obj):
        if obj.cluster_config:
            return obj.cluster_config[:100] + '...' if len(obj.cluster_config) > 100 else obj.cluster_config
        return '-'
    get_cluster_config_preview.short_description = 'Config Preview'
    
    def get_reads_display(self, obj):
        reads = obj.reads.all()[:10]  # Show first 10
        if reads:
            read_list = [f"Read {r.id} (Sample: {r.sample.sample_id})" for r in reads]
            result = '\n'.join(read_list)
            if obj.reads.count() > 10:
                result += f'\n... and {obj.reads.count() - 10} more'
            return result
        return 'No reads associated'
    get_reads_display.short_description = 'Associated Reads'

    actions = ['start_run']

    def start_run(self, request, queryset):
        for mag_run in queryset:

            # chedck there is no other instance of this run running

            # Create a new temporary folder for the run
            id = random.randint(1000000, 9999999)
            run_folder = os.path.join(settings.LOCAL_DIR, f"{id}")
            os.makedirs(run_folder)

            with open(os.path.join(run_folder, 'samplesheet.csv'), 'w') as file:
                print(mag_run.samplesheet_content, file=file)

            with open(os.path.join(run_folder, 'cluster_config.cfg'), 'w') as file:
                print(mag_run.cluster_config, file=file)

            # Create a mag run instance
            # completed_process = subprocess.run(f"sleep 30; echo hello", shell=True, capture_output=True)
            # completed_process.stdout
            # kick off the job

            async_calls.run_mag(mag_run, run_folder)
            # save the process id

    start_run.short_description = 'Run MAG pipeline'

admin.site.register(MagRun, MagRunAdmin)

class SubMGRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'type', 'status', 'get_projects_count', 'get_samples_count', 'get_reads_count')
    list_filter = ('type', 'status')
    search_fields = ('order__name', 'order__project__title')
    readonly_fields = ('id', 'status', 'get_related_objects_display', 'yaml', 'tax_ids')
    
    fieldsets = (
        ('Run Information', {
            'fields': ('id', 'order', 'type', 'status')
        }),
        ('Related Objects', {
            'fields': ('get_related_objects_display',),
            'description': 'Objects included in this SubMG run'
        }),
        ('Configuration', {
            'fields': ('yaml', 'tax_ids'),
            'classes': ('collapse', 'wide')
        }),
    )
    
    def get_projects_count(self, obj):
        return obj.projects.count()
    get_projects_count.short_description = 'Projects'
    
    def get_samples_count(self, obj):
        return obj.samples.count()
    get_samples_count.short_description = 'Samples'
    
    def get_reads_count(self, obj):
        return obj.reads.count()
    get_reads_count.short_description = 'Reads'
    
    def get_related_objects_display(self, obj):
        info = []
        info.append(f"Projects: {obj.projects.count()}")
        info.append(f"Samples: {obj.samples.count()}")
        info.append(f"Reads: {obj.reads.count()}")
        info.append(f"Assemblies: {obj.assemblys.count()}")
        info.append(f"Bins: {obj.bins.count()}")
        info.append(f"MAGs: {obj.mags.count()}")
        return '\n'.join(info)
    get_related_objects_display.short_description = 'Related Objects Summary'

    actions = ['start_run']

    def start_run(self, request, queryset):
        for submg_run in queryset:

            # chedck there is no other instance of this run running

            # Create a new temporary folder for the run
            id = random.randint(1000000, 9999999)
            run_folder = os.path.join(settings.LOCAL_DIR, f"{id}")
            os.makedirs(run_folder)

            with open(os.path.join(run_folder, 'submg.yaml'), 'w') as file:
                print(submg_run.yaml.replace('tax_ids.txt', f'{run_folder}/tax_ids.txt'), file=file)

            with open(os.path.join(run_folder, 'tax_ids.txt'), 'w') as file:
                print(submg_run.tax_ids, file=file)

            # Create a mag run instance
            # completed_process = subprocess.run(f"sleep 30; echo hello", shell=True, capture_output=True)
            # completed_process.stdout
            # kick off the job

            async_calls.run_submg(submg_run, run_folder)
            # save the process id



        # cconstruct yaml - for objects not yet submitted
        # get project details out from project
        # get sample details out from sample, set as samplee
        # get read details out from read, set as read
        # get assembly details out from assembly, set as assembly
        # get bin details out from bin, set as bin
        # get mag details out from mag, set as mag

        # each object should output its own yaml - bins and mags will need to be adjused to store taxon, mag files
        # BAM files??
        # Remember multiplicity for samples

        # run job

        # hook needs to update accession, and set object status as complete

        # projects 
        # samples 
        # reads 
        ### assembly_samples 
        ### bin_samples 
        ### mag_samples
        # assemblys 
        # bins 
        # mags


    start_run.short_description = 'Run SubMG'

admin.site.register(SubMGRun, SubMGRunAdmin)


class AssemblyAdmin(admin.ModelAdmin):
    list_display = ('id', 'file')

    actions = []


admin.site.register(Assembly, AssemblyAdmin)

class BinAdmin(admin.ModelAdmin):
    list_display = ('id', 'file')

    actions = []

admin.site.register(Bin, BinAdmin)

class AlignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'file')

    actions = []

admin.site.register(Alignment, AlignmentAdmin)


# Dynamic Form Admin
from .models import FormTemplate, FormSubmission
import json


class FormTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for FormTemplate model.
    """
    list_display = ('name', 'form_type', 'version', 'facility_name', 'is_active', 'updated_at')
    list_filter = ('form_type', 'is_active', 'facility_specific')
    search_fields = ('name', 'description', 'facility_name')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'form_type', 'version', 'description')
        }),
        ('Facility Settings', {
            'fields': ('facility_specific', 'facility_name'),
            'description': 'Specify if this form is for a specific facility'
        }),
        ('Form Configuration', {
            'fields': ('json_schema',),
            'description': 'JSON schema defining the form structure',
            'classes': ('wide',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ('created_by',)
        return self.readonly_fields
    
    actions = ['clone_template', 'export_as_json', 'toggle_active']
    
    def clone_template(self, request, queryset):
        for template in queryset:
            clone = template.clone()
            clone.created_by = request.user
            clone.save()
            self.message_user(request, f"Successfully cloned '{template.name}'", messages.SUCCESS)
    clone_template.short_description = "Clone selected templates"
    
    def export_as_json(self, request, queryset):
        # Export selected templates as JSON
        templates_data = []
        for template in queryset:
            templates_data.append({
                'name': template.name,
                'form_type': template.form_type,
                'version': template.version,
                'description': template.description,
                'facility_specific': template.facility_specific,
                'facility_name': template.facility_name,
                'json_schema': template.json_schema
            })
        
        # For now, just display a message. In a real implementation,
        # this would download a JSON file
        self.message_user(request, f"Export functionality would export {len(templates_data)} templates", messages.INFO)
    export_as_json.short_description = "Export selected templates as JSON"
    
    def toggle_active(self, request, queryset):
        for template in queryset:
            template.is_active = not template.is_active
            template.save()
        self.message_user(request, "Toggled active status for selected templates", messages.SUCCESS)
    toggle_active.short_description = "Toggle active status"


admin.site.register(FormTemplate, FormTemplateAdmin)


class FormSubmissionAdmin(admin.ModelAdmin):
    """
    Admin interface for FormSubmission model.
    """
    list_display = ('id', 'form_template', 'user', 'get_form_type', 'created_at')
    list_filter = ('form_template__form_type', 'created_at')
    search_fields = ('user__username', 'form_template__name')
    readonly_fields = ('form_template', 'user', 'submission_data_pretty', 'project', 'order', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Submission Info', {
            'fields': ('form_template', 'user', 'created_at', 'updated_at')
        }),
        ('Related Objects', {
            'fields': ('project', 'order'),
            'description': 'Links to related Project or Order objects'
        }),
        ('Submission Data', {
            'fields': ('submission_data_pretty',),
            'classes': ('wide',)
        }),
    )
    
    def get_form_type(self, obj):
        return obj.form_template.get_form_type_display()
    get_form_type.short_description = 'Form Type'
    get_form_type.admin_order_field = 'form_template__form_type'
    
    def submission_data_pretty(self, obj):
        """
        Pretty print the JSON submission data
        """
        try:
            pretty_json = json.dumps(obj.submission_data, indent=2)
            return pretty_json
        except:
            return str(obj.submission_data)
    submission_data_pretty.short_description = 'Submission Data (Formatted)'
    
    def has_add_permission(self, request):
        # Don't allow manual creation of submissions through admin
        return False
    
    def has_change_permission(self, request, obj=None):
        # Make submissions read-only
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete submissions
        return request.user.is_superuser


admin.site.register(FormSubmission, FormSubmissionAdmin)