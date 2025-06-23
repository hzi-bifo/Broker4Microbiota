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
from .models import Order, Sample, SampleSubmission, ReadSubmission, Pipelines, Read, Project, ProjectSubmission, MagRun, SubMGRun, Bin, Assembly, SAMPLE_TYPE_NORMAL, SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG, Alignment, Mag

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
    list_display = ('id', 'name', 'date', 'quote_no', 'billing_address', 'ag_and_hzi', 'contact_phone', 'email', 'data_delivery', 'signature', 'experiment_title', 'dna', 'rna', 'method', 'buffer', 'organism', 'isolated_from', 'isolation_method')

admin.site.register(Order, OrderAdmin)


class ReadAdmin(admin.ModelAdmin):
    list_display = ('id', 'sample', 'file_1', 'file_2')

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
        mag_run.samplesheet_content = samplesheet_content

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
    list_display = ('id', 'user', 'title', 'alias', 'description', 'study_accession_id', 'alternative_accession_id')

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

            yaml.extend(Read.getSubMGYAMLHeader())
            for read in reads:
                yaml.extend(read.getSubMGYAML())
            if assemblys:
                yaml.extend(Assembly.getSubMGYAMLHeader())
            for assembly in assemblys:
                yaml.extend(assembly.getSubMGYAML())
            if len(assembly_samples) != 1:
                raise Exception(f"Multiple assembly samples found for assembly")
            for assembly_sample in assembly_samples:
                yaml.extend(assembly_sample.getSubMGYAML(SAMPLE_TYPE_ASSEMBLY))
            yaml.extend(Assembly.getSubMGYAMLFooter())

            if bins:
                yaml.extend(Bin.getSubMGYAMLHeader())
            for bin in bins:
                yaml.extend(bin.getSubMGYAML())
                break
            tax_ids = {}
            for bin_sample in bin_samples:
                bin = bin_sample.bin
                tax_ids[bin.file.split('/')[-1].replace(".fa.gz", "")] = [bin_sample.scientific_name, bin_sample.tax_id]
            for bin in bins:
                yaml.extend(bin.getSubMGYAMLTaxIDYAML(tax_ids))
                break 
            for bin_sample in bin_samples:
                yaml.extend(bin_sample.getSubMGYAML(SAMPLE_TYPE_BIN))
                break
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
            subMG_run.yaml = output
 
            output_file_path = "/tmp/output.txt"

            with open(output_file_path, 'w') as output_file:
                print(output, file=output_file)
 
            subMG_run.save()

        return
    
    generate_submg_run_including_children.short_description = 'Generate SubMG run for this object, all dependencies, and all child objects'

admin.site.register(Project, ProjectAdmin)


class SampleAdmin(admin.ModelAdmin):
    list_display = ('id', 'sample_type','assembly', 'bin') + (tuple(Sample().getFields().keys()))
    list_filter = ('sample_type',)

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
    list_display = ('id', 'sample_count', 'accession_status', 'sampleSubmission_object_xml')
    
    actions = ['register_samples']

    def sample_count(self, obj):
        return obj.samples.count()
    sample_count.short_description = 'Number of Samples'

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
    list_display = ('id', 'sample_count', 'accession_status', 'read_object_txt_list')
    
    actions = ['register_reads']

    def sample_count(self, obj):
        return obj.samples.count()
    sample_count.short_description = 'Number of Samples'

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

    register_projects.short_description = "Register sample with ENA"

admin.site.register(ProjectSubmission, ProjectSubmissionAdmin)


class MagRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'samplesheet_content', 'status')

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
    list_display = ('id', 'type', 'status')

    actions = ['start_run']

    def start_run(self, request, queryset):
        for submg_run in queryset:

            # chedck there is no other instance of this run running

            # Create a new temporary folder for the run
            id = random.randint(1000000, 9999999)
            run_folder = os.path.join(settings.LOCAL_DIR, f"{id}")
            os.makedirs(run_folder)

            with open(os.path.join(run_folder, 'submg.yaml'), 'w') as file:
                print(submg_run.yaml, file=file)

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