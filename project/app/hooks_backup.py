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
from collections import defaultdict

from typing import Optional

logger = logging.getLogger(__name__)

def _suffix_sort_key(path: Path, base_name: str) -> float:
    suffix = path.name[len(base_name):]
    if suffix.startswith("_"):
        suffix = suffix[1:]
    try:
        return int(suffix)
    except ValueError:
        return float("inf")


def _iter_named_directories(run_folder: str, base_name: str):
    """Yield directories like logging, logging_0, logging_1 in order."""
    root = Path(run_folder)
    seen = set()
    directories = []

    def add(path: Path):
        if not path.exists():
            return
        try:
            key = path.resolve()
        except OSError:
            key = path
        if key not in seen:
            directories.append(path)
            seen.add(key)

    for candidate in sorted(root.glob(f"{base_name}_*"), key=lambda p: _suffix_sort_key(p, base_name)):
        if candidate.is_dir():
            add(candidate)

    add(root / base_name)
    return directories


def _find_first_relative(run_folder: str, base_name: str, relative_path: Path) -> Optional[Path]:
    for directory in _iter_named_directories(run_folder, base_name):
        candidate = directory / relative_path
        if candidate.exists():
            return candidate
    return None


def _glob_relative(run_folder: str, base_name: str, pattern: str):
    matches = []
    for directory in _iter_named_directories(run_folder, base_name):
        matches.extend(sorted(directory.glob(pattern)))
    return matches


def _process_single_logging_directory(logging_dir: Path, order, project, sample_set, submg_run):
    """Process all samples, assemblies, bins etc. for a single logging directory."""
    
    # Process biological samples for this directory
    sample_file_path = logging_dir / 'biological_samples' / 'sample_preliminary_accessions.txt'
    samplesheet_path = logging_dir.parent / 'staging' / 'biological_samples' / 'samplesheet.xml'
    samplesheet_lookup = {}

    if samplesheet_path and samplesheet_path.exists():
        try:
            with open(samplesheet_path) as biological_sample_samplesheet_content:
                biological_sample_samplesheet_data = biological_sample_samplesheet_content.read()
                biological_sample_samplesheet_xml = xmltodict.parse(biological_sample_samplesheet_data)
                biological_sample_samplesheet_json = json.loads(json.dumps(biological_sample_samplesheet_xml))
            for sampleset_value in biological_sample_samplesheet_json.values():
                if not isinstance(sampleset_value, dict):
                    continue
                for sample_value in sampleset_value.values():
                    if not sample_value:
                        continue
                    sample_entries = sample_value if isinstance(sample_value, list) else [sample_value]
                    for entry in sample_entries:
                        alias = entry.get('@alias') if isinstance(entry, dict) else None
                        if alias:
                            samplesheet_lookup[alias] = entry
        except Exception as exc:
            logger.error('Error parsing biological samplesheet for SubMG run %s: %s', submg_run.id, exc)

    if sample_file_path and sample_file_path.exists():
        with open(sample_file_path) as sample_file:
            next(sample_file, None)  # Skip header line
            for line in sample_file:
                parts = line.split()
                if len(parts) < 3:
                    continue
                sample_alias, sample_accession_id, sample_external_accession_id = parts[:3]
                sample_info = samplesheet_lookup.get(sample_alias)
                if not sample_info:
                    continue
                biological_sample_title = sample_info.get('TITLE') if isinstance(sample_info, dict) else None
                if not biological_sample_title:
                    continue
                try:
                    sample = Sample.objects.get(order=order, sample_type=SAMPLE_TYPE_NORMAL, sample_title=biological_sample_title)
                    sample.sample_accession_number = sample_accession_id
                    sample.sample_biosample_number = sample_external_accession_id
                    sample.save()
                except Sample.DoesNotExist:
                    pass

    # Process reads for this directory
    read_files = sorted(logging_dir.glob('reads/reads_*/webin-cli.report'))
    for read_file in read_files:
        read_file_path = Path(read_file)
        read_directory = read_file_path.parent
        read_id = read_directory.name.replace('reads_', '')

        submission_file_path = read_directory / 'reads' / read_id / 'submit' / 'run.xml'
        if not submission_file_path.exists():
            logger.warning('Submission file not found for read %s in SubMG run %s', read_id, submg_run.id)
            continue

        read_file_checksum_1 = None
        read_file_checksum_2 = None
        with open(submission_file_path) as submission_file:
            for submission_line in submission_file:
                if "FILE file" in submission_line:
                    read_file_name = submission_line.split('filename="')[1].split('"')[0].split('/')[-1].replace('.fastq.gz', '').replace('reads_', '')
                    checksum = submission_line.split('checksum="')[1].split('"')[0]
                    if read_file_name.endswith('1'):
                        read_file_checksum_1 = checksum
                    if read_file_name.endswith('2'):
                        read_file_checksum_2 = checksum

        if not (read_file_checksum_1 and read_file_checksum_2):
            logger.warning('Could not determine read checksum pair for read %s in SubMG run %s', read_id, submg_run.id)
            continue

        try:
            read = Read.objects.get(read_file_checksum_1=read_file_checksum_1, read_file_checksum_2=read_file_checksum_2)
        except Read.DoesNotExist:
            logger.warning('Read with checksums %s / %s not found for SubMG run %s', read_file_checksum_1, read_file_checksum_2, submg_run.id)
            continue

        run_accession_id = None
        experiment_accession_id = None
        with open(read_file_path) as read_file_content:
            for line in read_file_content:
                if 'run accession' in line:
                    run_accession_id = line.split('submission: ')[1].strip()
                if 'experiment accession' in line:
                    experiment_accession_id = line.split('submission: ')[1].strip()

        if run_accession_id:
            read.run_accession_number = run_accession_id
        if experiment_accession_id:
            read.experiment_accession_number = experiment_accession_id
        read.save()

    # Process assemblies for this directory
    assembly_files = sorted(logging_dir.glob('assembly_fasta/webin-cli.report'))
    for assembly_file in assembly_files:
        assembly_path = Path(assembly_file)
        try:
            assembly = Assembly.objects.get(order=order)
        except Assembly.DoesNotExist:
            logger.error('No assembly found for order %s', order.id)
            continue

        try:
            assembly_accession_id = None
            with open(assembly_path) as assembly_file_content:
                for line in assembly_file_content:
                    if 'analysis accession' in line:
                        assembly_accession_id = line.split('submission: ')[1].strip()
            if assembly_accession_id:
                assembly.assembly_accession_number = assembly_accession_id
                assembly.save()
        except FileNotFoundError:
            logger.error('Assembly file not found: %s', assembly_path)
        except Exception as e:
            logger.error('Error processing assembly file %s: %s', assembly_path, str(e))

    # Process assembly samples for this directory
    assembly_sample_samplesheet_path = logging_dir.parent / 'staging' / 'assembly_submission' / 'co_assembly_sample' / 'coassembly_samplesheet.xml'
    if assembly_sample_samplesheet_path and assembly_sample_samplesheet_path.exists():
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
                            assembly_sample_alias = value
                        if attribute == 'TITLE':
                            assembly_sample_title = value
                        if attribute == 'SAMPLE_NAME':
                            assembly_sample_name = value
                        if attribute == 'SAMPLE_ATTRIBUTES':
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
                unitchecklist_item_instance.save()

        # Update assembly sample accession numbers
        assembly_sample_files = sorted(logging_dir.glob('co_assembly_sample/assembly_samplesheet_receipt.xml'))
        for assembly_sample_file in assembly_sample_files:
            with open(assembly_sample_file) as assembly_sample_file_content:
                for line in assembly_sample_file_content:
                    if "SAMPLE accession" in line:
                        assembly_sample_alias = line.split('alias="')[1].split('"')[0]
                        assembly_sample_accession_id = line.split('accession="')[1].split('"')[0]
                    if "EXT_ID" in line:
                        assembly_sample_external_accession_id = line.split('accession="')[1].split('"')[0]      

            try:
                assembly_sample=Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_ASSEMBLY, sample_alias=assembly_sample_title)
                assembly_sample.sample_accession_number = assembly_sample_accession_id
                assembly_sample.sample_biosample_number = assembly_sample_external_accession_id
                assembly_sample.save()
            except Sample.DoesNotExist:
                logger.warning(f"Assembly sample with alias {assembly_sample_title} not found for order {order.id}")
            assembly_sample.save()

    # Process bins for this directory
    bin_files = sorted(logging_dir.glob('bins/bin_to_preliminary_accession.tsv'))
    for bin_file in bin_files:
        with open(bin_file) as bin_file_content:
            for line in bin_file_content:
                bin_id = line.split()[0].rstrip(' ')
                bin_number = bin_id.split('.')[1]
                bin_accession_id = line.split()[1].lstrip(' ')
                # Handle multiple bins with same bin_number (assembly-specific structure)
                bins = Bin.objects.filter(order=order, bin_number=bin_number)
                if bins.count() > 1:
                    # Multiple bins with same number - use the first one without accession number
                    bin = None
                    for b in bins:
                        if not b.bin_accession_number:
                            bin = b
                            break
                    if not bin:
                        # All bins already have accession numbers - skip processing to avoid duplicates
                        logger.warning('All bins with number %s for order %s already have accession numbers. Skipping to avoid duplicate processing.', bin_number, order.id)
                        # Log the existing accession numbers for debugging
                        for b in bins:
                            logger.warning(f"Bin {b.id} already has accession number: {b.bin_accession_number}")
                        continue  # Skip this bin processing
                elif bins.count() == 1:
                    bin = bins.first()
                    if not bin.bin_accession_number:
                        bin.bin_accession_number = bin_accession_id
                        bin.save()
                        logger.info(f"Updated bin {bin.id} with accession ID {bin_accession_id}")
                    else:
                        logger.warning(f"Bin {bin.id} already has accession number {bin.bin_accession_number}. Skipping to avoid duplicate processing.")
                        continue
                else:
                    logger.error(f"No bins found for bin_number {bin_number} in order {order.id}")
                    return

    # Process bin samples for this directory
    bin_sample_samplesheet_path = logging_dir.parent / 'staging' / 'bins' / 'bin_samplesheet' / 'bins_samplesheet.xml'
    if bin_sample_samplesheet_path and bin_sample_samplesheet_path.exists():
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
                            bin_sample_alias = value
                        if attribute == 'TITLE':
                            bin_sample_title = value
                        if attribute == 'SAMPLE_NAME':
                            bin_sample_name = value
                        if attribute == 'SAMPLE_ATTRIBUTES':
                            bin_sample_attributes = value.items()
            bin_sample_title_dict[bin_sample_alias] = bin_sample_title
            bin_sample_name_dict[bin_sample_alias] = bin_sample_name
            bin_sample_attributes_dict[bin_sample_alias] = bin_sample_attributes

            bin_sample_full_title = re.sub('_virtual_sample', '', re.sub('.*coasm_bin_MEGAHIT-MaxBin2-', '', bin_sample_title))
            bin_sample_title = bin_sample_full_title.split('.')[0]
            bin_sample_number = bin_sample_full_title.split('.')[1]

            # Handle multiple bins with same bin_number (assembly-specific structure)
            bins = Bin.objects.filter(order=order, bin_number=bin_sample_number)
            if bins.count() > 1:
                # Multiple bins with same number - need to identify which one
                # For now, use the first one that doesn't have a sample assigned
                bin = None
                for b in bins:
                    if not Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_BIN, bin=b).exists():
                        bin = b
                        break
                if not bin:
                    # If all bins already have samples, use the first one
                    bin = bins.first()
                    logger.warning(f"Multiple bins found for bin_number {bin_sample_number}, using first one (bin {bin.id})")
            elif bins.count() == 1:
                bin = bins.first()
            else:
                logger.error(f"No bins found for bin_number {bin_sample_number} in order {order.id}")
                return

            try:
                sample = Sample.objects.get(order=order, sample_type=SAMPLE_TYPE_BIN, bin=bin)
            except Sample.DoesNotExist:
                sample = Sample(order=order, sample_type=SAMPLE_TYPE_BIN, sample_alias=bin_sample_title, bin=bin)
            sample.setFieldsFromSubMG(bin_sample_title, bin_sample_title_dict[bin_sample_alias], bin_sample_name_dict[bin_sample_alias], bin_sample_attributes_dict[bin_sample_alias])
            sample.sampleset = sample_set
            sample.save()

            checklists = sample_set.checklists
            for checklist in checklists:
                checklist_name = checklist
                checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']
                checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                checklist_item_class = getattr(importlib.import_module('app.models'), checklist_class_name)
                try:
                    checklist_item_instance = checklist_item_class.objects.get(sampleset=sample_set, sample=sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                except checklist_item_class.DoesNotExist:
                    checklist_item_instance = checklist_item_class(sampleset=sample_set, sample=sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                checklist_item_instance.setFieldsFromSubMG(bin_sample_alias, bin_sample_title_dict[bin_sample_alias], bin_sample_name_dict[bin_sample_alias], bin_sample_attributes_dict[bin_sample_alias])
                checklist_item_instance.save()
                unitchecklist_class_name = Sampleset.checklist_structure[checklist_name]['unitchecklist_class_name']
                unitchecklist_item_class = getattr(importlib.import_module('app.models'), unitchecklist_class_name)
                try:
                    unitchecklist_item_instance = unitchecklist_item_class.objects.get(sampleset=sample_set, sample=sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                except unitchecklist_item_class.DoesNotExist:
                    unitchecklist_item_instance = unitchecklist_item_class(sampleset=sample_set, sample=sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                unitchecklist_item_instance.save()

        # Update bin sample accession numbers
        bin_sample_files = sorted(logging_dir.glob('bins/bin_samplesheet/bins_samplesheet_receipt.xml'))
        for bin_sample_file in bin_sample_files:
            with open(bin_sample_file) as bin_sample_file_content:
                for line in bin_sample_file_content:
                    if "SAMPLE accession" in line:
                        bin_sample_alias = line.split('alias="')[1].split('"')[0]
                        bin_sample_accession_id = line.split('accession="')[1].split('"')[0]
                    if "EXT_ID" in line:
                        bin_sample_external_accession_id = line.split('accession="')[1].split('"')[0]      

            try:
                bin_sample=Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_BIN, sample_title=bin_sample_alias)
                bin_sample.sample_accession_number = bin_sample_accession_id
                bin_sample.sample_biosample_number = bin_sample_external_accession_id
                bin_sample.save()
            except Sample.DoesNotExist:
                logger.warning(f"Bin sample with title {bin_sample_alias} not found for order {order.id}")
            bin_sample.save()

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

    project_ids = set(
        mag_run.reads.values_list('sample__order__project_id', flat=True)
    )
    project_ids.discard(None)
    if project_ids:
        if mag_run.project_id and mag_run.project_id not in project_ids:
            logger.warning(
                'MAG run %s has project %s but includes reads from projects %s',
                mag_run.id,
                mag_run.project_id,
                sorted(project_ids)
            )
        elif not mag_run.project_id and len(project_ids) == 1:
            mag_run.project_id = project_ids.pop()
    
    if returncode != 0:
        mag_run_instance.status = 'failed'
        mag_run.status = 'failed'
    else:
        mag_run_instance.status = 'completed'
        mag_run.status = 'completed'

        run_folder = mag_run_instance.run_folder

        existing_assemblies = {}
        existing_bins = {}
        existing_alignments = {}
        assembly_sample_links = defaultdict(dict)
        bin_sample_links = defaultdict(dict)
        used_bin_sample_ids = defaultdict(set)
        created_assemblies = defaultdict(list)
        created_bins = defaultdict(list)
        created_alignments = defaultdict(list)
        processed_orders = set()

        reads = mag_run.reads.all()
        for read in reads:
            # file_name = re.sub(f"_R1.fastq.gz", f"", re.sub(f"_1.fastq.gz", f"", read.file_1.split('/')[-1]))

            sample = read.sample
            order = sample.order
            project = order.project

            processed_orders.add(order.id)
            if order.id not in existing_assemblies:
                existing_assemblies[order.id] = list(order.assembly_set.values_list('id', flat=True))
                existing_bins[order.id] = list(order.bin_set.values_list('id', flat=True))
                existing_alignments[order.id] = list(order.alignment_set.values_list('id', flat=True))
                assembly_map = assembly_sample_links.setdefault(order.id, {})
                bin_map = bin_sample_links.setdefault(order.id, {})
                for bin_sample in Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_BIN).select_related('bin'):
                    if bin_sample.bin and bin_sample.bin.bin_number:
                        bin_map.setdefault(bin_sample.bin.bin_number, []).append(bin_sample.id)
                for existing_assembly in order.assembly_set.all():
                    sample_ids = list(Sample.objects.filter(assembly=existing_assembly).values_list('id', flat=True))
                    if sample_ids:
                        for read_id in existing_assembly.read.values_list('id', flat=True):
                            assembly_map.setdefault(read_id, set()).update(sample_ids)


            assembly = None  # Initialize assembly variable
            assembly_file_path = f"{run_folder}/Assembly/MEGAHIT/MEGAHIT-{sample.sample_id}.contigs.fa.gz"
            assembly_file = Path(assembly_file_path)
            if assembly_file.is_file():
                try:
                    assembly = Assembly(file=str(assembly_file), order=order)
                    assembly.save()
                    assembly.read.add(read)
                    created_assemblies[order.id].append(assembly.id)
                    linked_sample_ids = assembly_sample_links.get(order.id, {}).get(read.id)
                    if linked_sample_ids:
                        Sample.objects.filter(id__in=linked_sample_ids).update(assembly=assembly)
                except Exception as e:
                    logger.error(f"Error creating assembly for sample {sample.sample_id}: {str(e)}")
                    mag_run_instance.status = 'partial'
                    mag_run.status = 'partial'
            else:
                mag_run_instance.status = 'partial'
                mag_run.status = 'partial'

            # Create assembly-specific MaxBin2 directory structure
            assembly_specific_dir = f"{run_folder}/GenomeBinning/MaxBin2/Assembly_{assembly.id}/Maxbin2_bins"
            os.makedirs(assembly_specific_dir, exist_ok=True)
            bin_file_path = f"{assembly_specific_dir}/MEGAHIT-MaxBin2-{sample.sample_id}.[0-9][0-9][0-9].fa"
            
            # Also check for stub-created directories (Assembly_1, Assembly_2, etc.)
            # This handles the case where stub mode creates directories with sequential numbers
            stub_assembly_dirs = glob.glob(f"{run_folder}/GenomeBinning/MaxBin2/Assembly_*/Maxbin2_bins")
            stub_bin_files = []
            for stub_dir in stub_assembly_dirs:
                stub_pattern = f"{stub_dir}/MEGAHIT-MaxBin2-{sample.sample_id}.[0-9][0-9][0-9].fa"
                stub_bin_files.extend(glob.glob(stub_pattern))
            
            try:
                bin_files = glob.glob(bin_file_path)
                # If no files found in assembly-specific directory, try stub directories
                if not bin_files:
                    bin_files = stub_bin_files
                for bin_file in bin_files:
                    try:
                        bin_number = bin_file.split('.')[-2]
                        bin = Bin(file=bin_file, order=order, assembly=assembly)
                        # Try assembly-specific quality file first, then fallback to stub-created files
                        assembly_specific_file = f"{run_folder}/GenomeBinning/QC/checkm_summary_assembly_{assembly.id}.tsv"
                        if os.path.exists(assembly_specific_file):
                            bin.quality_file = assembly_specific_file
                        else:
                            # Fallback to stub-created files (checkm_summary_assembly_1.tsv, etc.)
                            # Find the stub file that contains this bin
                            stub_files = glob.glob(f"{run_folder}/GenomeBinning/QC/checkm_summary_assembly_*.tsv")
                            quality_file_found = False
                            for stub_file in stub_files:
                                try:
                                    with open(stub_file, 'r') as f:
                                        content = f.read()
                                        bin_name = Path(bin_file).name.replace('.fa', '')
                                        if bin_name in content:
                                            bin.quality_file = stub_file
                                            quality_file_found = True
                                            break
                                except:
                                    continue
                            
                            if not quality_file_found:
                                # Final fallback to the assembly-specific path (will be created later)
                                bin.quality_file = assembly_specific_file
                        bin.bin_number = bin_number
                        bin.save()
                        created_bins[order.id].append(bin.id)
                        linked_bin_samples = bin_sample_links.get(order.id, {}).get(bin.bin_number, [])
                        if linked_bin_samples:
                            Sample.objects.filter(id__in=linked_bin_samples).update(bin=bin)
                            used_bin_sample_ids[order.id].update(linked_bin_samples)
                        else:
                            unmatched_samples = list(
                                Sample.objects.filter(
                                    order=order, sample_type=SAMPLE_TYPE_BIN
                                ).exclude(id__in=used_bin_sample_ids[order.id])
                            )
                            bin_stem = Path(bin.file or "").stem
                            matched_bin_ids = [
                                sample.id for sample in unmatched_samples
                                if bin_stem and sample.sample_alias and sample.sample_alias in bin_stem
                            ]
                            if len(matched_bin_ids) < len(unmatched_samples):
                                matched_bin_ids.extend([
                                    sample.id for sample in unmatched_samples
                                    if sample.bin_id == bin.id and sample.id not in matched_bin_ids
                                ])
                            if len(matched_bin_ids) < len(unmatched_samples):
                                matched_bin_ids.extend([
                                    sample.id for sample in unmatched_samples
                                    if sample.bin_id is None and sample.id not in matched_bin_ids
                                ])
                            if matched_bin_ids:
                                Sample.objects.filter(id__in=matched_bin_ids).update(bin=bin)
                                used_bin_sample_ids[order.id].update(matched_bin_ids)
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
                            created_alignments[order.id].append(alignment.id)
                        except Exception as e:
                            logger.error(f"Error creating alignment from {alignment_file}: {str(e)}")
                            mag_run_instance.status = 'partial'
                            mag_run.status = 'partial'
                if not alignment_files:
                    mag_run_instance.status = 'partial'
                    mag_run.status = 'partial'
            except Exception as e:
                logger.error(f"Error processing alignment files: {str(e)}")

        for order_id in processed_orders:
            if not (created_assemblies.get(order_id) or created_bins.get(order_id) or created_alignments.get(order_id)):
                continue
            old_alignment_ids = existing_alignments.get(order_id, [])
            if old_alignment_ids:
                Alignment.objects.filter(id__in=old_alignment_ids).delete()
            old_bin_ids = existing_bins.get(order_id, [])
            if old_bin_ids:
                Bin.objects.filter(id__in=old_bin_ids).delete()
            old_assembly_ids = existing_assemblies.get(order_id, [])
            if old_assembly_ids:
                Assembly.objects.filter(id__in=old_assembly_ids).delete()

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

        # Process each logging directory sequentially
        logging_directories = _iter_named_directories(run_folder, 'logging')
        for logging_dir in logging_directories:
            logger.info(f"Processing logging directory: {logging_dir}")
            _process_single_logging_directory(logging_dir, order, project, sample_set, submg_run)

        # Save the SubMG run status
        try:
            submg_run_instance.save()
            submg_run.save()
        except Exception as e:
            logger.error(f"Error saving SubMG run status: {str(e)}")


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

    project_ids = set(
        mag_run.reads.values_list('sample__order__project_id', flat=True)
    )
    project_ids.discard(None)
    if project_ids:
        if mag_run.project_id and mag_run.project_id not in project_ids:
            logger.warning(
                'MAG run %s has project %s but includes reads from projects %s',
                mag_run.id,
                mag_run.project_id,
                sorted(project_ids)
            )
        elif not mag_run.project_id and len(project_ids) == 1:
            mag_run.project_id = project_ids.pop()
    
    if returncode != 0:
        mag_run_instance.status = 'failed'
        mag_run.status = 'failed'
    else:
        mag_run_instance.status = 'completed'
        mag_run.status = 'completed'

        run_folder = mag_run_instance.run_folder

        existing_assemblies = {}
        existing_bins = {}
        existing_alignments = {}
        assembly_sample_links = defaultdict(dict)
        bin_sample_links = defaultdict(dict)
        used_bin_sample_ids = defaultdict(set)
        created_assemblies = defaultdict(list)
        created_bins = defaultdict(list)
        created_alignments = defaultdict(list)
        processed_orders = set()

        reads = mag_run.reads.all()
        for read in reads:
            sample = read.sample
            order = sample.order
            project = order.project

            processed_orders.add(order.id)
            if order.id not in existing_assemblies:
                existing_assemblies[order.id] = list(order.assembly_set.values_list('id', flat=True))
                existing_bins[order.id] = list(order.bin_set.values_list('id', flat=True))
                existing_alignments[order.id] = list(order.alignment_set.values_list('id', flat=True))
                assembly_map = assembly_sample_links.setdefault(order.id, {})
                bin_map = bin_sample_links.setdefault(order.id, {})
                for bin_sample in Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_BIN).select_related('bin'):
                    if bin_sample.bin and bin_sample.bin.bin_number:
                        bin_map.setdefault(bin_sample.bin.bin_number, []).append(bin_sample.id)
                for existing_assembly in order.assembly_set.all():
                    sample_ids = list(Sample.objects.filter(assembly=existing_assembly).values_list('id', flat=True))
                    if sample_ids:
                        for read_id in existing_assembly.read.value_list('id', flat=True):
                            assembly_map.setdefault(read_id, set()).update(sample_ids)

            assembly = None  # Initialize assembly variable
            assembly_file_path = f"{run_folder}/Assembly/MEGAHIT/MEGAHIT-{sample.sample_id}.contigs.fa.gz"
            assembly_file = Path(assembly_file_path)
            if assembly_file.is_file():
                try:
                    assembly = Assembly(file=str(assembly_file), order=order)
                    assembly.save()
                    assembly.read.add(read)
                    created_assemblies[order.id].append(assembly.id)
                    linked_sample_ids = assembly_sample_links.get(order.id, {}).get(read.id)
                    if linked_sample_ids:
                        Sample.objects.filter(id__in=linked_sample_ids).update(assembly=assembly)
                except Exception as e:
                    logger.error(f"Error creating assembly for sample {sample.sample_id}: {str(e)}")
                    mag_run_instance.status = 'partial'
                    mag_run.status = 'partial'
            else:
                mag_run_instance.status = 'partial'
                mag_run.status = 'partial'

            # Create assembly-specific MaxBin2 directory structure
            assembly_specific_dir = f"{run_folder}/GenomeBinning/MaxBin2/Assembly_{assembly.id}/Maxbin2_bins"
            os.makedirs(assembly_specific_dir, exist_ok=True)
            bin_file_path = f"{assembly_specific_dir}/MEGAHIT-MaxBin2-{sample.sample_id}.[0-9][0-9][0-9].fa"
            
            # Also check for stub-created directories (Assembly_1, Assembly_2, etc.)
            # This handles the case where stub mode creates directories with sequential numbers
            stub_assembly_dirs = glob.glob(f"{run_folder}/GenomeBinning/MaxBin2/Assembly_*/Maxbin2_bins")
            stub_bin_files = []
            for stub_dir in stub_assembly_dirs:
                stub_pattern = f"{stub_dir}/MEGAHIT-MaxBin2-{sample.sample_id}.[0-9][0-9][0-9].fa"
                stub_bin_files.extend(glob.glob(stub_pattern))
            
            try:
                bin_files = glob.glob(bin_file_path)
                # If no files found in assembly-specific directory, try stub directories
                if not bin_files:
                    bin_files = stub_bin_files
                for bin_file in bin_files:
                    try:
                        bin_number = bin_file.split('.')[-2]
                        bin = Bin(file=bin_file, order=order, assembly=assembly)
                        # Try assembly-specific quality file first, then fallback to stub-created files
                        assembly_specific_file = f"{run_folder}/GenomeBinning/QC/checkm_summary_assembly_{assembly.id}.tsv"
                        if os.path.exists(assembly_specific_file):
                            bin.quality_file = assembly_specific_file
                        else:
                            # Fallback to stub-created files (checkm_summary_assembly_1.tsv, etc.)
                            # Find the stub file that contains this bin
                            stub_files = glob.glob(f"{run_folder}/GenomeBinning/QC/checkm_summary_assembly_*.tsv")
                            quality_file_found = False
                            for stub_file in stub_files:
                                try:
                                    with open(stub_file, 'r') as f:
                                        content = f.read()
                                        bin_name = Path(bin_file).name.replace('.fa', '')
                                        if bin_name in content:
                                            bin.quality_file = stub_file
                                            quality_file_found = True
                                            break
                                except:
                                    continue
                            
                            if not quality_file_found:
                                # Final fallback to the assembly-specific path (will be created later)
                                bin.quality_file = assembly_specific_file
                        bin.bin_number = bin_number
                        bin.save()
                        created_bins[order.id].append(bin.id)
                        linked_bin_samples = bin_sample_links.get(order.id, {}).get(bin.bin_number, [])
                        if linked_bin_samples:
                            Sample.objects.filter(id__in=linked_bin_samples).update(bin=bin)
                            used_bin_sample_ids[order.id].update(linked_bin_samples)
                        else:
                            unmatched_samples = list(
                                Sample.objects.filter(
                                    order=order, sample_type=SAMPLE_TYPE_BIN
                                ).exclude(id__in=used_bin_sample_ids[order.id])
                            )
                            bin_stem = Path(bin.file or "").stem
                            matched_bin_ids = [
                                sample.id for sample in unmatched_samples
                                if bin_stem and sample.sample_alias and sample.sample_alias in bin_stem
                            ]
                            if len(matched_bin_ids) < len(unmatched_samples):
                                matched_bin_ids.extend([
                                    sample.id for sample in unmatched_samples
                                    if sample.bin_id == bin.id and sample.id not in matched_bin_ids
                                ])
                            if len(matched_bin_ids) < len(unmatched_samples):
                                matched_bin_ids.extend([
                                    sample.id for sample in unmatched_samples
                                    if sample.bin_id is None and sample.id not in matched_bin_ids
                                ])
                            if matched_bin_ids:
                                Sample.objects.filter(id__in=matched_bin_ids).update(bin=bin)
                                used_bin_sample_ids[order.id].update(matched_bin_ids)
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
                            created_alignments[order.id].append(alignment.id)
                        except Exception as e:
                            logger.error(f"Error creating alignment from {alignment_file}: {str(e)}")
                            mag_run_instance.status = 'partial'
                            mag_run.status = 'partial'
                if not alignment_files:
                    mag_run_instance.status = 'partial'
                    mag_run.status = 'partial'
            except Exception as e:
                logger.error(f"Error processing alignment files: {str(e)}")

        for order_id in processed_orders:
            if not (created_assemblies.get(order_id) or created_bins.get(order_id) or created_alignments.get(order_id)):
                continue
            old_alignment_ids = existing_alignments.get(order_id, [])
            if old_alignment_ids:
                Alignment.objects.filter(id__in=old_alignment_ids).delete()
            old_bin_ids = existing_bins.get(order_id, [])
            if old_bin_ids:
                Bin.objects.filter(id__in=old_bin_ids).delete()
            old_assembly_ids = existing_assemblies.get(order_id, [])
            if old_assembly_ids:
                Assembly.objects.filter(id__in=old_assembly_ids).delete()

        try:
            mag_run_instance.save()
            mag_run.save()
        except Exception as e:
            logger.error(f"Error saving MAG run status: {str(e)}")

            try:
                assembly_accession_id = None
                with open(assembly_path) as assembly_file_content:
                    for line in assembly_file_content:
                        if 'analysis accession' in line:
                            assembly_accession_id = line.split('submission: ')[1].strip()
                if assembly_accession_id:
                    assembly.assembly_accession_number = assembly_accession_id
                    assembly.save()
            except FileNotFoundError:
                logger.error('Assembly file not found: %s', assembly_path)
            except Exception as e:
                logger.error('Error processing assembly file %s: %s', assembly_path, str(e))


        # Process assembly samples

        # Get details of assemly sample constructed by SubMG and convert XML to JSON

        # Only present if multiple samples were co-assembled
        assembly_sample_samplesheet_files = _glob_relative(run_folder, 'staging', 'assembly_submission/co_assembly_sample/coassembly_samplesheet.xml')

        for assembly_sample_samplesheet_path in assembly_sample_samplesheet_files:
            if assembly_sample_samplesheet_path and assembly_sample_samplesheet_path.exists():

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

        assembly_sample_files = _glob_relative(run_folder, 'logging', 'co_assembly_sample/assembly_samplesheet_receipt.xml')
        for assembly_sample_file in assembly_sample_files:
            with open(assembly_sample_file) as assembly_sample_file_content:
                for line in assembly_sample_file_content:
                    if "SAMPLE accession" in line:
                        assembly_sample_alias = line.split('alias="')[1].split('"')[0]
                        assembly_sample_accession_id = line.split('accession="')[1].split('"')[0]
                    if "EXT_ID" in line:
                        assembly_sample_external_accession_id = line.split('accession="')[1].split('"')[0]      

            try:
                assembly_sample=Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_ASSEMBLY, sample_alias=assembly_sample_title)
                assembly_sample.sample_accession_number = assembly_sample_accession_id
                assembly_sample.sample_biosample_number = assembly_sample_external_accession_id
                assembly_sample.save()
            except Sample.DoesNotExist:
                logger.warning(f"Assembly sample with alias {assembly_sample_title} not found for order {order.id}")
            assembly_sample.save()


        # Process bins

        bin_files = _glob_relative(run_folder, 'logging', 'bins/bin_to_preliminary_accession.tsv')
        for bin_file in bin_files:
            with open(bin_file) as bin_file_content:
                for line in bin_file_content:
                    bin_id = line.split()[0].rstrip(' ')
                    bin_number = bin_id.split('.')[1]
                    bin_accession_id = line.split()[1].lstrip(' ')
                    # Handle multiple bins with same bin_number (assembly-specific structure)
                bins = Bin.objects.filter(order=order, bin_number=bin_number)
                if bins.count() > 1:
                    # Multiple bins with same number - use the first one without accession number
                    bin = None
                    for b in bins:
                        if not b.bin_accession_number:
                            bin = b
                            break
                    if not bin:
                        # All bins already have accession numbers - skip processing to avoid duplicates
                        logger.warning('All bins with number %s for order %s already have accession numbers. Skipping to avoid duplicate processing.', bin_number, order.id)
                        # Log the existing accession numbers for debugging
                        for b in bins:
                            logger.warning(f"Bin {b.id} already has accession number: {b.bin_accession_number}")
                        continue  # Skip this bin processing
                elif bins.count() == 1:
                    bin = bins.first()
                    if not bin.bin_accession_number:
                        bin.bin_accession_number = bin_accession_id
                        bin.save()
                        logger.info(f"Updated bin {bin.id} with accession ID {bin_accession_id}")
                    else:
                        logger.warning(f"Bin {bin.id} already has accession number {bin.bin_accession_number}. Skipping to avoid duplicate processing.")
                        continue
                else:
                    logger.error(f"No bins found for bin_number {bin_number} in order {order.id}")
                    return


        # Process bin samples

        bin_sample_samplesheet_files = _glob_relative(run_folder, 'staging', 'bins/bin_samplesheet/bins_samplesheet.xml')

        if not bin_sample_samplesheet_files:
            logger.warning('Bin samplesheet not found for SubMG run %s', submg_run.id)
        else:
            for bin_sample_samplesheet_path in bin_sample_samplesheet_files:
                if not bin_sample_samplesheet_path or not bin_sample_samplesheet_path.exists():
                    continue
                
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
                                    bin_sample_alias = value
                                if attribute == 'TITLE':
                                    bin_sample_title = value
                                if attribute == 'SAMPLE_NAME':
                                    bin_sample_name = value
                                if attribute == 'SAMPLE_ATTRIBUTES':
                                    bin_sample_attributes = value.items()
                    bin_sample_title_dict[bin_sample_alias] = bin_sample_title
                    bin_sample_name_dict[bin_sample_alias] = bin_sample_name
                    bin_sample_attributes_dict[bin_sample_alias] = bin_sample_attributes

                    bin_sample_full_title = re.sub('_virtual_sample', '', re.sub('.*coasm_bin_MEGAHIT-MaxBin2-', '', bin_sample_title))
                    bin_sample_title = bin_sample_full_title.split('.')[0]
                    bin_sample_number = bin_sample_full_title.split('.')[1]

                    # Handle multiple bins with same bin_number (assembly-specific structure)
            bins = Bin.objects.filter(order=order, bin_number=bin_sample_number)
            if bins.count() > 1:
                # Multiple bins with same number - need to identify which one
                # For now, use the first one that doesn't have a sample assigned
                bin = None
                for b in bins:
                    if not Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_BIN, bin=b).exists():
                        bin = b
                        break
                if not bin:
                    # If all bins already have samples, use the first one
                    bin = bins.first()
                    logger.warning(f"Multiple bins found for bin_number {bin_sample_number}, using first one (bin {bin.id})")
            elif bins.count() == 1:
                bin = bins.first()
            else:
                logger.error(f"No bins found for bin_number {bin_sample_number} in order {order.id}")
                return

                    try:
                        sample = Sample.objects.get(order=order, sample_type=SAMPLE_TYPE_BIN, bin=bin)
                    except Sample.DoesNotExist:
                        sample = Sample(order=order, sample_type=SAMPLE_TYPE_BIN, sample_alias=bin_sample_title, bin=bin)
                    sample.setFieldsFromSubMG(bin_sample_title, bin_sample_title_dict[bin_sample_alias], bin_sample_name_dict[bin_sample_alias], bin_sample_attributes_dict[bin_sample_alias])
                    sample.sampleset = sample_set
                    sample.save()

                    checklists = sample_set.checklists
                    for checklist in checklists:
                        checklist_name = checklist
                    checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']
                    checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
                    checklist_item_class = getattr(importlib.import_module('app.models'), checklist_class_name)
                    try:
                        checklist_item_instance = checklist_item_class.objects.get(sampleset=sample_set, sample=sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                    except checklist_item_class.DoesNotExist:
                        checklist_item_instance = checklist_item_class(sampleset=sample_set, sample=sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                    checklist_item_instance.setFieldsFromSubMG(bin_sample_alias, bin_sample_title_dict[bin_sample_alias], bin_sample_name_dict[bin_sample_alias], bin_sample_attributes_dict[bin_sample_alias])
                    checklist_item_instance.save()
                    unitchecklist_class_name = Sampleset.checklist_structure[checklist_name]['unitchecklist_class_name']
                    unitchecklist_item_class = getattr(importlib.import_module('app.models'), unitchecklist_class_name)
                    try:
                        unitchecklist_item_instance = unitchecklist_item_class.objects.get(sampleset=sample_set, sample=sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                    except unitchecklist_item_class.DoesNotExist:
                        unitchecklist_item_instance = unitchecklist_item_class(sampleset=sample_set, sample=sample, sample_type=SAMPLE_TYPE_ASSEMBLY)
                    unitchecklist_item_instance.save()


        # Update bin sample accession numbers

        bin_sample_files = _glob_relative(run_folder, 'logging', 'bins/bin_samplesheet/bins_samplesheet_receipt.xml')
        for bin_sample_file in bin_sample_files:
            with open(bin_sample_file) as bin_sample_file_content:
                for line in bin_sample_file_content:
                    if "SAMPLE accession" in line:
                        bin_sample_alias = line.split('alias="')[1].split('"')[0]
                        bin_sample_accession_id = line.split('accession="')[1].split('"')[0]
                    if "EXT_ID" in line:
                        bin_sample_external_accession_id = line.split('accession="')[1].split('"')[0]      

            try:
                bin_sample=Sample.objects.get(order = order, sample_type=SAMPLE_TYPE_BIN, sample_title=bin_sample_alias)
                bin_sample.sample_accession_number = bin_sample_accession_id
                bin_sample.sample_biosample_number = bin_sample_external_accession_id
                bin_sample.save()
            except Sample.DoesNotExist:
                logger.warning(f"Bin sample with title {bin_sample_alias} not found for order {order.id}")
            bin_sample.save()




        # MAG should be created for each bin sample

        # set sample entries as read-only???

        try:
            submg_run_instance.save()
            submg_run.save()
        except Exception as e:
            logger.error(f"Error saving SubMG run status: {str(e)}")        
