from django_q.tasks import async_task, result
from .models import MagRun, MagRunInstance, Assembly, Bin, Order, Alignment, SubMGRun, SubMGRunInstance, Sample, Read, Sampleset, SAMPLE_TYPE_NORMAL, SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG
import re
from pathlib import Path
import glob
import xmltodict
import json
import importlib

def process_mag_result(task):


    mag_run_instance = MagRunInstance.objects.get(uuid=task.id)
    mag_run = MagRun.objects.get(id=mag_run_instance.magRun.id)

    if task.result.returncode != 0:
        mag_run_instance.status = 'failed'
        mag_run.status = 'failed'
    else:
        mag_run_instance.status = 'completed'
        mag_run.status = 'completed'

        run_folder = mag_run_instance.run_folder

        reads = mag_run.reads.all()
        for read in reads:
            # file_name = re.sub(f"_R1.fastq.gz", f"", re.sub(f"_1.fastq.gz", f"", read.file_1.split('/')[-1]))

            sample = read.sample
            order = sample.order
            project = order.project

            assembly_file_path = f"{run_folder}/Assembly/MEGAHIT/MEGAHIT-{sample.sample_id}.contigs.fa.gz"
            assembly_file = Path(assembly_file_path)
            if assembly_file.is_file():
                assembly = Assembly(file=assembly_file, order=order)
                assembly.save()
                assembly.read.add(read)
            else:
                mag_run_instance.status = 'partial'
                mag_run.status = 'partial'

            bin_file_path = f"{run_folder}/GenomeBinning/MaxBin2/Maxbin2_bins/MEGAHIT-MaxBin2-{sample.sample_id}.[0-9][0-9][0-9].fa.gz"
            bin_files = glob.glob(bin_file_path)
            for bin_file in bin_files:
                bin = Bin(file=bin_file, order=order)
                bin.quality_file = f"{run_folder}/GenomeBinning/QC/checkm_summary.tsv"
                bin.save()
                bin.read.add(read)
            if bin_files == []:
                mag_run_instance.status = 'partial'
                mag_run.status = 'partial'

            alignment_file_path = f"{run_folder}/{sample.sample_id}.sorted.bam"
            alignment_files = glob.glob(alignment_file_path)
            for alignment_file in alignment_files:
                alignment = Alignment(file=alignment_file, order=order, assembly=assembly, read=read)
                alignment.save()
            if alignment_files == []:
                mag_run_instance.status = 'partial'
                mag_run.status = 'partial'

        mag_run_instance.save()
        mag_run.save()

def process_submg_result(task):

    returncode = task.result.returncode
    id = task.id
    process_submg_result_inner(returncode, id)



def process_submg_result_inner(returncode, id):

    # Get the SubMGRunInstance and SubMGRun objects
    submg_run_instance = SubMGRunInstance.objects.get(id=id)
    submg_run = SubMGRun.objects.get(id=submg_run_instance.subMGRun.id)

    if returncode != 0:
        submg_run_instance.status = 'failed'
        submg_run.status = 'failed'
    else:
        submg_run_instance.status = 'completed'
        submg_run.status = 'completed'

        run_folder = submg_run_instance.run_folder

        # Get the order and project associated with the SubMGRun
        order = submg_run.order
        project = order.project
        sample_set = order.sampleset_set.filter(sample_type=SAMPLE_TYPE_ASSEMBLY).first()

        # Process biological samples

        # Get aliases and accession numbers from the sample file
        # and update the Sample objects accordingly
        sample_file_path = f"{run_folder}/logging/biological_samples/sample_preliminary_accessions.txt"
        with open(sample_file_path) as sample_file:
            next(sample_file)  # Skip header line
            for line in sample_file:
                sample_alias = line.split()[0]
                sample_title = sample_alias[4:]
                sample_accession_id = line.split()[1]
                sample_external_accession_id = line.split()[2]
                try:
                    sample=Sample.objects.get(order = order, sample_alias=sample_title)
                    sample.sample_accession_number = sample_accession_id
                    sample.sample_biosample_number = sample_external_accession_id
                    sample.save()
                except Sample.DoesNotExist:
                    pass

        # Process reads

        # Get read ID
        read_file_path = f"{run_folder}/logging/reads/reads_*/webin-cli.report"
        read_files = glob.glob(read_file_path)
        for read_file in read_files:
            read_id = read_file.split('/')[-2].replace('reads_', '')

            # Get read file checksums from the submission file
            submission_file_path = f"{run_folder}/logging/reads/reads_{read_id}/reads/{read_id}/submit/run.xml"
            with open(submission_file_path) as submission_file:
                for submission_line in submission_file:
                    if "FILE file" in submission_line:
                        read_file_name = submission_line.split('filename="')[1].split('"')[0].split('/')[-1].replace('.fastq.gz', '').replace('reads_', '')
                        checksum = submission_line.split('checksum="')[1].split('"')[0]
                        if read_file_name.endswith('1'):
                            read_file_checksum_1 = checksum
                        if read_file_name.endswith('2'):
                            read_file_checksum_2 = checksum 

            # Get actual read object using these checksums - was created when actual reads were uploaded
            read = Read.objects.get(read_file_checksum_1 = read_file_checksum_1, read_file_checksum_2 = read_file_checksum_2)

            # Update read accession numbers
            with open(read_file) as read_file_content: 
                for line in read_file_content:
                    if "run accession" in line:
                        run_accession_id = line.split('submission: ')[1].replace('\n', '')
                    if "experiment accession" in line:
                        experiment_accession_id = line.split('submission: ')[1].replace('\n', '')
            read.run_accession_number = run_accession_id
            read.experiment_accession_number = experiment_accession_id
            read.save()

        # Process assemblies

        # Upload (only) assembly for this order with accession id
        assembly_file_path = f"{run_folder}/logging/assembly_fasta/webin-cli.report"
        assembly_files = glob.glob(assembly_file_path)
        for assembly_file in assembly_files:
            assembly = Assembly.objects.get(order=order)
            with open(assembly_file) as assembly_file_content:
                for line in assembly_file_content:
                    if "analysis accession" in line:
                        assembly_accession_id = line.split('submission: ')[1].replace('\n', '')
            assembly.assembly_accession_number = assembly_accession_id
            assembly.save()


        # Process assembly samples

        # Get details of assemly sample constructed by SubMG and convert XML to JSON

        assembly_sample_samplesheet_path = f"{run_folder}/staging/assembly_submission/co_assembly_sample/coassembly_samplesheet.xml"

        assembly_sample_title_dict = {}
        assembly_sample_name_dict = {}
        assembly_sample_attributes_dict = {}
        
        with open(assembly_sample_samplesheet_path) as assembly_sample_samplesheet_content:
            assembly_sample_samplesheet_data = assembly_sample_samplesheet_content.read()
            assembly_sample_samplesheet_xml = xmltodict.parse(assembly_sample_samplesheet_data)
            assembly_sample_samplesheet_json = json.loads(json.dumps(assembly_sample_samplesheet_xml))
            for samplesheet_attribute, samplesheet_value in assembly_sample_samplesheet_json.items():
                for sample_attribute, sample_value in samplesheet_value.items():
                    for attribute, value in sample_value.items():
                        if attribute == '@alias':
                            # string
                            assembly_sample_alias = value
                        if attribute == 'TITLE':
                            # string
                            assembly_sample_title = value
                        if attribute == 'SAMPLE_NAME':
                            # dictionary
                            assembly_sample_name = value
                        if attribute == 'SAMPLE_ATTRIBUTES':
                            # list of dictionaries (with TAG and VALUE)
                            assembly_sample_attributes = value.items()                                
            assembly_sample_title_dict[assembly_sample_alias] = assembly_sample_title
            assembly_sample_name_dict[assembly_sample_alias] = assembly_sample_name
            assembly_sample_attributes_dict[assembly_sample_alias] = assembly_sample_attributes

            # create assembly sample objects
            try:
                sample = Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_ASSEMBLY, sample_alias=assembly_sample_title)
            except Sample.DoesNotExist:
                sample=Sample(order = order, sample_type=SAMPLE_TYPE_ASSEMBLY, sample_alias=assembly_sample_title)
            sample.setFieldsFromSubMG(assembly_sample_title, assembly_sample_title_dict[assembly_sample_alias], assembly_sample_name_dict[assembly_sample_alias], assembly_sample_attributes_dict[assembly_sample_alias])
            sample.sampleset = sample_set
            sample.save()

            checklists = sample_set.checklists

            # create new checklists based on the received data

            for checklist in checklists:
                checklist_name = checklist
                checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
                checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
                try:
                    checklist_item_instance = checklist_item_class.objects.get(sampleset = sample_set, sample = sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                except checklist_item_class.DoesNotExist:
                    checklist_item_instance = checklist_item_class(sampleset = sample_set, sample = sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                checklist_item_instance.setFieldsFromSubMG(assembly_sample_alias, assembly_sample_title_dict[assembly_sample_alias], assembly_sample_name_dict[assembly_sample_alias], assembly_sample_attributes_dict[assembly_sample_alias])
                checklist_item_instance.save()
                unitchecklist_class_name = Sampleset.checklist_structure[checklist_name]['unitchecklist_class_name']
                unitchecklist_item_class =  getattr(importlib.import_module("app.models"), unitchecklist_class_name)
                try:
                    unitchecklist_item_instance = unitchecklist_item_class.objects.get(sampleset = sample_set, sample = sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                except unitchecklist_item_class.DoesNotExist:
                    unitchecklist_item_instance = unitchecklist_item_class(sampleset = sample_set, sample = sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                # unitchecklist_item_instance.setFieldsFromResponse(sample_info)
                unitchecklist_item_instance.save()

        # Update assembly sample accession numbers

        assembly_sample_file_path = f"{run_folder}/logging/co_assembly_sample/assembly_samplesheet_receipt.xml"
        assembly_sample_files = glob.glob(assembly_sample_file_path)
        for assembly_sample_file in assembly_sample_files:
            with open(assembly_sample_file) as assembly_sample_file_content:
                for line in assembly_sample_file_content:
                    if "SAMPLE accession" in line:
                        assembly_sample_alias = line.split('alias="')[1].split('"')[0]
                        assembly_sample_accession_id = line.split('accession="')[1].split('"')[0]
                    if "EXT_ID" in line:
                        assembly_sample_external_accession_id = line.split('accession="')[1].split('"')[0]      

            assembly_sample=Sample.objects.get(order = order, sample_alias=assembly_sample_title)
            assembly_sample.sample_accession_number = sample_accession_id
            assembly_sample.sample_biosample_number = sample_external_accession_id
            assembly_sample.save()


        # Process bins

        bin_file_path = f"{run_folder}/logging/bins/bin_to_preliminary_accession.tsv"
        bin_files = glob.glob(bin_file_path)
        for bin_file in bin_files:
            with open(bin_file) as bin_file_content:
                for line in bin_file_content:
                    bin_id = line.split()[0].rstrip(' ')
                    bin_number = bin_id.split('.')[1]
                    bin_accession_id = line.split()[1].lstrip(' ')
                    bin = Bin.objects.get(order=order, bin_number=bin_number)
                    bin.bin_accession_number = bin_accession_id
                    bin.save()





        # Process bin samples

        # Get details of bin sample constructed by SubMG and convert XML to JSON

        bin_sample_samplesheet_path = f"{run_folder}/staging/bins/bin_samplesheet/bins_samplesheet.xml"

        bin_sample_title_dict = {}
        bin_sample_name_dict = {}
        bin_sample_attributes_dict = {}
        
        with open(bin_sample_samplesheet_path) as bin_sample_samplesheet_content:
            bin_sample_samplesheet_data = bin_sample_samplesheet_content.read()
            bin_sample_samplesheet_xml = xmltodict.parse(bin_sample_samplesheet_data)
            bin_sample_samplesheet_json = json.loads(json.dumps(bin_sample_samplesheet_xml))
            for samplesheet_attribute, samplesheet_value in bin_sample_samplesheet_json.items():
                for sample_attribute, sample_value in samplesheet_value.items():
                    for attribute, value in sample_value.items():
                        if attribute == '@alias':
                            # string
                            bin_sample_alias = value
                        if attribute == 'TITLE':
                            # string
                            bin_sample_title = value
                        if attribute == 'SAMPLE_NAME':
                            # dictionary
                            bin_sample_name = value
                        if attribute == 'SAMPLE_ATTRIBUTES':
                            # list of dictionaries (with TAG and VALUE)
                            bin_sample_attributes = value.items()                                
            bin_sample_title_dict[bin_sample_alias] = bin_sample_title
            bin_sample_name_dict[bin_sample_alias] = bin_sample_name
            bin_sample_attributes_dict[bin_sample_alias] = bin_sample_attributes

            # create bin sample objects
            try:
                sample = Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_BIN, sample_alias=bin_sample_title)
            except Sample.DoesNotExist:
                sample=Sample(order = order, sample_type=SAMPLE_TYPE_BIN, sample_alias=bin_sample_title)
            sample.setFieldsFromSubMG(bin_sample_title, bin_sample_title_dict[bin_sample_alias], bin_sample_name_dict[bin_sample_alias], bin_sample_attributes_dict[bin_sample_alias])
            sample.sampleset = sample_set
            sample.save()

            checklists = sample_set.checklists

            # create new checklists based on the received data

            for checklist in checklists:
                checklist_name = checklist
                checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
                checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
                try:
                    checklist_item_instance = checklist_item_class.objects.get(sampleset = sample_set, sample = sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                except checklist_item_class.DoesNotExist:
                    checklist_item_instance = checklist_item_class(sampleset = sample_set, sample = sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                checklist_item_instance.setFieldsFromSubMG(bin_sample_alias, bin_sample_title_dict[bin_sample_alias], bin_sample_name_dict[bin_sample_alias], bin_sample_attributes_dict[bin_sample_alias])
                checklist_item_instance.save()
                unitchecklist_class_name = Sampleset.checklist_structure[checklist_name]['unitchecklist_class_name']
                unitchecklist_item_class =  getattr(importlib.import_module("app.models"), unitchecklist_class_name)
                try:
                    unitchecklist_item_instance = unitchecklist_item_class.objects.get(sampleset = sample_set, sample = sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                except unitchecklist_item_class.DoesNotExist:
                    unitchecklist_item_instance = unitchecklist_item_class(sampleset = sample_set, sample = sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                # unitchecklist_item_instance.setFieldsFromResponse(sample_info)
                unitchecklist_item_instance.save()

        # Update bin sample accession numbers

        bin_sample_file_path = f"{run_folder}/logging/bins/bin_samplesheet/bins_samplesheet_receipt.xml"
        bin_sample_files = glob.glob(bin_sample_file_path)
        for bin_sample_file in bin_sample_files:
            with open(bin_sample_file) as bin_sample_file_content:
                for line in bin_sample_file_content:
                    if "SAMPLE accession" in line:
                        bin_sample_alias = line.split('alias="')[1].split('"')[0]
                        bin_sample_accession_id = line.split('accession="')[1].split('"')[0]
                    if "EXT_ID" in line:
                        bin_sample_external_accession_id = line.split('accession="')[1].split('"')[0]      

            bin_sample=Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_BIN, sample_alias=bin_sample_title)
            bin_sample.sample_accession_number = sample_accession_id
            bin_sample.sample_biosample_number = sample_external_accession_id
            bin_sample.save()

        # MAG should be created for each bin sample

        # set sample entries as read-only???
