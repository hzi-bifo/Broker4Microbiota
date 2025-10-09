import os
from django_q.tasks import async_task, result
from .models import MagRun, MagRunInstance, Assembly, Bin, Order, Alignment, SubMGRun, SubMGRunInstance, Sample, Read, Sampleset, SAMPLE_TYPE_NORMAL, SAMPLE_TYPE_ASSEMBLY, SAMPLE_TYPE_BIN, SAMPLE_TYPE_MAG
import re
from pathlib import Path
import glob
import xmltodict
import json
import importlib
import logging

logger = logging.getLogger(__name__)

def process_mag_result(task):
    try:
        returncode = task.result.returncode
        uuid = task.id
        mag_run_instance = MagRunInstance.objects.get(uuid=uuid)
        process_mag_result_inner(returncode, mag_run_instance.id)
    except Exception as e:
        logger.error(f"Error processing MAG result for task {task.id}: {str(e)}")
        raise


def process_mag_result_inner(returncode, id):
    try:
        mag_run_instance = MagRunInstance.objects.get(id=id)
        mag_run = MagRun.objects.get(id=mag_run_instance.magRun.id)
    except MagRunInstance.DoesNotExist:
        logger.error(f"MagRunInstance with id {id} does not exist")
        raise ValueError(f"MagRunInstance with id {id} does not exist")
    except MagRun.DoesNotExist:
        logger.error(f"MagRun for MagRunInstance {id} does not exist")
        raise ValueError(f"MagRun for MagRunInstance {id} does not exist")

    if returncode != 0:
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

            assembly = None  # Initialize assembly variable
            assembly_file_path = f"{run_folder}/Assembly/MEGAHIT/MEGAHIT-{sample.sample_id}.contigs.fa.gz"
            assembly_file = Path(assembly_file_path)
            if assembly_file.is_file():
                try:
                    assembly = Assembly(file=str(assembly_file), order=order)
                    assembly.save()
                    assembly.read.add(read)
                except Exception as e:
                    logger.error(f"Error creating assembly for sample {sample.sample_id}: {str(e)}")
                    mag_run_instance.status = 'partial'
                    mag_run.status = 'partial'
            else:
                mag_run_instance.status = 'partial'
                mag_run.status = 'partial'

            bin_file_path = f"{run_folder}/GenomeBinning/MaxBin2/Maxbin2_bins/MEGAHIT-MaxBin2-{sample.sample_id}.[0-9][0-9][0-9].fa"
            try:
                bin_files = glob.glob(bin_file_path)
                for bin_file in bin_files:
                    try:
                        bin_number = bin_file.split('.')[-2]
                        bin = Bin(file=bin_file, order=order)
                        bin.quality_file = f"{run_folder}/GenomeBinning/QC/checkm_summary.tsv"
                        bin.bin_number = bin_number
                        bin.save()
                        bin.read.add(read)
                    except Exception as e:
                        logger.error(f"Error creating bin from {bin_file}: {str(e)}")
                        mag_run_instance.status = 'partial'
                        mag_run.status = 'partial'
                if not bin_files:
                    mag_run_instance.status = 'partial'
                    mag_run.status = 'partial'
            except Exception as e:
                logger.error(f"Error processing bin files: {str(e)}")

            alignment_file_path = f"{run_folder}/{sample.sample_id}.sorted.bam"
            try:
                alignment_files = glob.glob(alignment_file_path)
                for alignment_file in alignment_files:
                    if assembly:  # Only create alignment if assembly exists
                        try:
                            alignment = Alignment(file=alignment_file, order=order, assembly=assembly, read=read)
                            alignment.save()
                        except Exception as e:
                            logger.error(f"Error creating alignment from {alignment_file}: {str(e)}")
                            mag_run_instance.status = 'partial'
                            mag_run.status = 'partial'
                if not alignment_files:
                    mag_run_instance.status = 'partial'
                    mag_run.status = 'partial'
            except Exception as e:
                logger.error(f"Error processing alignment files: {str(e)}")

        try:
            mag_run_instance.save()
            mag_run.save()
        except Exception as e:
            logger.error(f"Error saving MAG run status: {str(e)}")

def process_submg_result(task):

    returncode = task.result.returncode
    uuid = task.id
    submgrun_instance = SubMGRunInstance.objects.get(uuid=uuid)
    process_submg_result_inner(returncode, submgrun_instance.id)



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
                sample_accession_id = line.split()[1]
                sample_external_accession_id = line.split()[2]

                # use the alias to look up the alias in staging/biological_samples/samplesheet.xml and get the title


                biological_sample_samplesheet_path = f"{run_folder}/staging/biological_samples/samplesheet.xml"

                with open(biological_sample_samplesheet_path) as biological_sample_samplesheet_content:
                    biological_sample_samplesheet_data = biological_sample_samplesheet_content.read()
                    biological_sample_samplesheet_xml = xmltodict.parse(biological_sample_samplesheet_data)
                    biological_sample_samplesheet_json = json.loads(json.dumps(biological_sample_samplesheet_xml))
                    for sampleset_attribute, sampleset_value in biological_sample_samplesheet_json.items():
                        for sample_attribute, sample_value in sampleset_value.items():                     
                            biological_sample_alias = sample_value['@alias']
                            biological_sample_title = sample_value['TITLE']

                            if biological_sample_alias == sample_alias:

                                try:
                                    sample=Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_NORMAL, sample_title=biological_sample_title)
                                    sample.sample_accession_number = sample_accession_id
                                    sample.sample_biosample_number = sample_external_accession_id
                                    sample.save()
                                except Sample.DoesNotExist:
                                    pass
                                break


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
            try:
                assembly = Assembly.objects.get(order=order)
                with open(assembly_file) as assembly_file_content:
                    for line in assembly_file_content:
                        if "analysis accession" in line:
                            assembly_accession_id = line.split('submission: ')[1].replace('\n', '')
                assembly.assembly_accession_number = assembly_accession_id
                assembly.save()
            except Assembly.DoesNotExist:
                logger.error(f"No assembly found for order {order.id}")
            except FileNotFoundError:
                logger.error(f"Assembly file not found: {assembly_file}")
            except Exception as e:
                logger.error(f"Error processing assembly file {assembly_file}: {str(e)}")


        # Process assembly samples

        # Get details of assemly sample constructed by SubMG and convert XML to JSON

        # Only present if multiple samples were co-assembled
        assembly_sample_samplesheet_path = f"{run_folder}/staging/assembly_submission/co_assembly_sample/coassembly_samplesheet.xml"

        if os.path.exists(assembly_sample_samplesheet_path):

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
                    sample = Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_ASSEMBLY)
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

                assembly_sample=Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_ASSEMBLY, sample_alias=assembly_sample_title)
                assembly_sample.sample_accession_number = assembly_sample_accession_id
                assembly_sample.sample_biosample_number = assembly_sample_external_accession_id
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

        # Get details of assemly sample constructed by SubMG and convert XML to JSON

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

            bin_sample_full_title = re.sub("_virtual_sample", "", re.sub(".*coasm_bin_MEGAHIT-MaxBin2-", "", bin_sample_title))  
            bin_sample_title = bin_sample_full_title.split('.')[0]  # Remove the extension if present
            bin_sample_number = bin_sample_full_title.split('.')[1]

            bin = Bin.objects.get(order=order, bin_number=bin_sample_number)

            # create bin sample objects
            try:
                sample = Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_BIN, bin=bin)
            except Sample.DoesNotExist:
                sample=Sample(order = order, sample_type=SAMPLE_TYPE_BIN, sample_alias=bin_sample_title, bin=bin)
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

            bin_sample=Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_BIN, sample_title=bin_sample_alias)
            bin_sample.sample_accession_number = bin_sample_accession_id
            bin_sample.sample_biosample_number = bin_sample_external_accession_id
            bin_sample.save()




        # MAG should be created for each bin sample

        # set sample entries as read-only???

        try:
            submg_run_instance.save()
            submg_run.save()
        except Exception as e:
            logger.error(f"Error saving SubMG run status: {str(e)}")        
