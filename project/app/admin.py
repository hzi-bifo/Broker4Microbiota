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
from .models import Order, Sample, Submission, ReadSubmission, Pipelines, Sequence, SequenceTemplate, Project, ProjectSubmission, MagRun, SubMGRun
from .forms import CreateGZForm
from django.template.loader import render_to_string
from xml.etree import ElementTree as ET
import logging
import json
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'quote_no', 'billing_address', 'ag_and_hzi', 'contact_phone', 'email', 'data_delivery', 'signature', 'experiment_title', 'dna', 'rna', 'library', 'method', 'buffer', 'organism', 'isolated_from', 'isolation_method')

admin.site.register(Order, OrderAdmin)



class SequenceTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'platform', 'insert_size', 'library_name', 'library_source', 'library_selection', 'library_strategy')

admin.site.register(SequenceTemplate, SequenceTemplateAdmin)



class SequenceAdmin(admin.ModelAdmin):
    list_display = ('sample', 'sequence_template', 'file_1', 'file_2')

    actions = ['generate_xml_and_create_read_submission', 'create_mag_run']

    def generate_xml_and_create_read_submission(self, request, queryset):
        selected_sequences = queryset

        read_submission = ReadSubmission.objects.create(read_object_txt_list=json.dumps([]))

        txt_list = {}
        for sequence in selected_sequences:
            context = {
                'sequence': sequence,
                'sequence_template': sequence.sequence_template,
                'project': sequence.sample.order.project,
                'sample': sequence.sample,
            }
            read_txt_content = render_to_string('admin/app/sample/read_manifest.txt', context)
            txt_list[sequence.sample_id] = read_txt_content
        read_submission.read_object_txt_list = json.dumps(txt_list)
        read_submission.name = f"{sequence.sample.sample_id}"

        read_submission.save()

        self.message_user(request, f'Successfully created ReadSubmission {read_submission.name} with {selected_sequences.count()} samples')


    generate_xml_and_create_read_submission.short_description = 'Generate XML and create Read Submission'

    def create_mag_run(self, request, queryset):
        selected_sequences = queryset

        mag_run = MagRun.objects.create()
        mag_run.sequence_set.set(selected_sequences)
        
        context = {
            'sequences': selected_sequences,
        }
        samplesheet_content = render_to_string('admin/app/sample/mag_sampleseheet.csv', context)
        mag_run.samplesheet_content = json.dumps(samplesheet_content)

        context = {
            'settings': settings,
        }
        cluster_config = render_to_string('admin/app/sample/mag_cluster_config.cfg', context)
        mag_run.cluster_config = json.dumps(cluster_config)

        mag_run.save()

        self.message_user(request, f'Successfully created MAG run')


    create_mag_run.short_description = 'Create a MAG run'

admin.site.register(Sequence, SequenceAdmin)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'alias', 'description', 'study_accession_id', 'alternative_accession_id')

    actions = ['generate_xml_and_create_project_submission']

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

admin.site.register(Project, ProjectAdmin)


class SampleAdmin(admin.ModelAdmin):
    list_display = (tuple(Sample().getFields().keys()))

    # temporary - this needs to be passed through properly
    # checklists = ['GSC_MIxS_wastewater_sludge']
    # checklists = ['GSC_MIxS_wastewater_sludge', 'GSC_MIxS_miscellaneous_natural_or_artificial_environment']

    # get checklists used for this model (from the sample? - array of checklist names?)
    # get fields from each checklist
    # use the fields to create a list_display

    # temporary: get fields named alias, name, taxon_id from the set in use

    # Change XML template to use all attributes for each sample

    # proper set of checklists for GMAK, ENA

    actions = ['generate_xml_and_create_submission', 'run_mag_pipeline', 'create_sequences']

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

    def create_sequences(self, request, queryset):
        for sample in queryset:
            paired_read_1 = os.path.join(settings.LOCAL_DIR, sample.sample_alias + '_1.fastq.gz')
            paired_read_2 = os.path.join(settings.LOCAL_DIR, sample.sample_alias + '_2.fastq.gz')
            template_1 = os.path.join(settings.LOCAL_DIR, '..', 'template_1.fastq.gz')
            template_2 = os.path.join(settings.LOCAL_DIR, '..', 'template_2.fastq.gz')

            # temporary
            shutil.copyfile(template_1, paired_read_1)
            shutil.copyfile(template_2, paired_read_2)

            # takes first template object - temporary
            if os.path.isfile(paired_read_1) and os.path.isfile(paired_read_2):
                sequence = Sequence.objects.create(sample=sample, file_1=paired_read_1, file_2=paired_read_2, sequence_template=SequenceTemplate.objects.first())
                sequence.save()

    create_sequences.short_description = 'Generate sequences'

    def generate_xml_and_create_submission(self, request, queryset):
        selected_samples = queryset

        submission = Submission.objects.create()
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

admin.site.register(Sample, SampleAdmin)



class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'sample_count', 'accession_status', 'submission_object_xml')
    
    actions = ['register_sample']

    def sample_count(self, obj):
        return obj.samples.count()
    sample_count.short_description = 'Number of Samples'

    def register_sample(self, request, queryset):
        for submission in queryset:
            try:
                # Save XML content to files for debugging
                sample_xml_filename = os.path.join(settings.LOCAL_DIR, f"sample_{submission.id}.xml")
                submission_xml_filename = os.path.join(settings.LOCAL_DIR, f"submission_{submission.id}.xml")
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
                    submission.receipt_xml = receipt_xml
                    if root.tag == 'RECEIPT':
                        success = root.attrib['success']
                        if success != 'true':
                            raise Exception(f"Failed to register submission {submission.id}. Response: {response.content}")
                    for child in root:
                        if child.tag == 'SAMPLE':
                                sample_alias = child.attrib['alias']
                                sample_accession_number = child.attrib['accession']
                                submission.samples.filter(sample_alias=sample_alias).update(sample_accession_number=sample_accession_number)
                                for grandchild in child:
                                    if grandchild.tag == 'EXT_ID':
                                        sample_biosample_number = grandchild.attrib['accession']
                                        submission.samples.filter(sample_alias=sample_alias).update(sample_biosample_number=sample_biosample_number)
                    submission.accession_status = 'submitted'
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

class ReadSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'sample_count', 'accession_status', 'read_object_txt_list')
    
    actions = ['register_sample']

    def sample_count(self, obj):
        return obj.samples.count()
    sample_count.short_description = 'Number of Samples'

    def register_sample(self, request, queryset):
        for read_submission in queryset:
            count = 0
            read_object_txt_list = json.loads(read_submission.read_object_txt_list)
            for sample_id in read_object_txt_list.keys():
                sequence = Sequence.objects.get(sample_id=sample_id)
                read_object_txt = read_object_txt_list[sample_id]
                # Save the read manifest to a file
                read_manifest_filename = os.path.join(settings.LOCAL_DIR, f"read_manifest_{read_submission.id}{count}.txt")
                with open(read_manifest_filename, 'w') as read_manifest_file:
                    read_manifest_file.write(read_object_txt)

                executable = f"java -jar {settings.JAR_LOCATION}"
                context = f"-context reads"
                username = f"-username {settings.ENA_USERNAME}"
                password = f"-password \"{settings.ENA_PASSWORD}\""
                # centre = f"-centerName {settings.ENA_CENTRE}"
                centre = f""
                manifest = f"-manifest {read_manifest_filename}"
                outputDir = f"-outputDir {settings.LOCAL_DIR}"
                inputDir = f"-inputDir {settings.LOCAL_DIR}"
                # mode = f"-validate"
                mode = f"-submit"
                environment = f"-test"

                try:
                    webin_command = f"{executable} {context} {username} {password} {centre} {manifest} {outputDir} {inputDir} {mode} {environment}"
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
                                # read_submission.samples.filter(sample_id=sample_id).first().sequences.filter(sample_id=sample_id).update(run_accession_number=run_accession_number)
                                Sequence.objects.filter(sample_id=sample_id).update(run_accession_number=run_accession_number)
                            if child.tag == "EXPERIMENT":
                                experiment_accession_number = child.attrib['accession']
                                # read_submission.samples.filter(sample_id=sample_id).first().sequences.filter(sample_id=sample_id).update(experiment_accession_number=experiment_accession_number)
                                Sequence.objects.filter(sample_id=sample_id).update(experiment_accession_number=experiment_accession_number)
                        read_submission.accession_status = 'submitted'
                        read_submission.save()
                        self.message_user(request, "Read submission registered successfully.", messages.SUCCESS)

                except Exception as e:
                    logger.exception(f"Error registering read submission {read_submission.id}: {e}")
                    self.message_user(request, "An error occurred while registering the read submission.", messages.ERROR)
                    
                count = count + 1

    register_sample.short_description = "Register sample with ENA"

admin.site.register(ReadSubmission, ReadSubmissionAdmin)


class ProjectSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_object_xml', 'receipt_xml', 'submission_object_xml', 'accession_status')
    
    actions = ['register_project']

    def project_count(self, obj):
        return obj.projects.count()
    project_count.short_description = 'Number of Projects'

    def register_project(self, request, queryset):
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
                auth = (settings.ENA_USERNAME, settings.ENA_PASSWORD)
                # Make the request
                response = requests.post(
                    "https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/",
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

    register_project.short_description = "Register sample with ENA"

admin.site.register(ProjectSubmission, ProjectSubmissionAdmin)


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

class MagRunAdmin(admin.ModelAdmin):
    list_display = ('magRun_id', 'status')

    actions = ['start_run']

    def start_run(self, request, queryset):
        for mag_run in queryset:
            # Create a new temporary folder for the run
            id = random.randint(1000000, 9999999)
            run_folder = os.path.join(settings.LOCAL_DIR, f"{id}")
            os.makedirs(run_folder)

    start_run.short_description = "Register sample with ENA"

admin.site.register(MagRun, MagRunAdmin)
