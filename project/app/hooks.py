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


def process_single_assembly_file(assembly, assembly_path, order):
    """Process a single assembly file and update the assembly object."""
    try:
        assembly_accession_id = None
        logger.info(f"Reading assembly file: {assembly_path}")
        with open(assembly_path) as assembly_file_content:
            lines = assembly_file_content.readlines()
            logger.info(f"Assembly file has {len(lines)} lines")
            
            for i, line in enumerate(lines):
                line = line.strip()
                logger.debug(f"Line {i}: {line}")
                
                # Try multiple patterns for assembly accession
                if 'analysis accession' in line:
                    if 'submission:' in line:
                        assembly_accession_id = line.split('submission: ')[1].strip()
                    elif 'accession:' in line:
                        assembly_accession_id = line.split('accession: ')[1].strip()
                    else:
                        # Try to extract accession ID from the line
                        parts = line.split()
                        for part in parts:
                            if part.startswith('ERZ') or part.startswith('GCA_') or part.startswith('GCF_'):
                                assembly_accession_id = part
                                break
                    logger.info(f"Found assembly accession ID: {assembly_accession_id}")
                    break
                elif 'accession' in line.lower():
                    logger.debug(f"Line contains 'accession': {line}")
                    # Try to extract accession ID from lines containing 'accession'
                    if 'ERZ' in line or 'GCA_' in line or 'GCF_' in line:
                        parts = line.split()
                        for part in parts:
                            if part.startswith('ERZ') or part.startswith('GCA_') or part.startswith('GCF_'):
                                assembly_accession_id = part
                                logger.info(f"Extracted assembly accession ID from line: {assembly_accession_id}")
                                break
                        if assembly_accession_id:
                            break
        
        if assembly_accession_id:
            # Debug: Log existing bin accession numbers for this order
            existing_bin_accessions = list(Bin.objects.filter(order=order).values_list('bin_accession_number', flat=True))
            logger.info(f"Existing bin accession numbers for order {order.id}: {existing_bin_accessions}")
            logger.info(f"Processing assembly {assembly.id} with accession ID: {assembly_accession_id}")
            
            # Note: We don't check for conflicts with bin accession IDs because:
            # 1. Assembly accession IDs are analysis accession IDs (ERZ prefix)
            # 2. Bin accession IDs are preliminary accession IDs (ERS prefix)
            # 3. They are different types of accession IDs and can legitimately have the same base number
            
            logger.info(f"Updating assembly {assembly.id} with accession ID: {assembly_accession_id}")
            assembly.assembly_accession_number = assembly_accession_id
            assembly.save()
            logger.info(f"Successfully updated assembly {assembly.id}")
        else:
            logger.warning(f"No assembly accession ID found in {assembly_path}")
            # Log first few lines for debugging
            with open(assembly_path) as debug_file:
                debug_lines = debug_file.readlines()[:10]
                logger.warning(f"First 10 lines of {assembly_path}:")
                for i, line in enumerate(debug_lines):
                    logger.warning(f"  {i}: {line.strip()}")
    except FileNotFoundError:
        logger.error('Assembly file not found: %s', assembly_path)
    except Exception as e:
        logger.error('Error processing assembly file %s: %s', assembly_path, str(e))


def _process_single_logging_directory(logging_dir: Path, order, project, sample_set, submg_run):
    """Process all samples, assemblies, bins etc. for a single logging directory."""
    
    # Determine the matching staging directory
    # If logging_dir is something like "logging_0", staging should be "staging_0"
    # If logging_dir is "logging", staging should be "staging"
    logging_name = logging_dir.name
    if logging_name.startswith('logging_'):
        # Extract the suffix (e.g., "0" from "logging_0")
        suffix = logging_name[len('logging_'):]
        staging_dir_name = f'staging_{suffix}'
        staging_dir = logging_dir.parent / staging_dir_name
    else:
        staging_dir = logging_dir.parent / 'staging'
    
    # Process biological samples for this directory
    sample_file_path = logging_dir / 'biological_samples' / 'sample_preliminary_accessions.txt'
    samplesheet_path = staging_dir / 'biological_samples' / 'samplesheet.xml'
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

    # Track reads processed in this directory to filter assemblies later
    reads_in_this_directory = []
    
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
            # Filter by checksums first, then narrow down to reads associated with this SubMGRun
            # to handle cases where multiple reads have the same checksum pair
            read_query = Read.objects.filter(
                read_file_checksum_1=read_file_checksum_1,
                read_file_checksum_2=read_file_checksum_2
            )
            # If SubMGRun has reads associated, filter by them to get the correct one
            if submg_run.reads.exists():
                read_query = read_query.filter(id__in=submg_run.reads.values_list('id', flat=True))
            
            # Check count before getting first to avoid multiple queries
            read_count = read_query.count()
            if read_count == 0:
                logger.warning('Read with checksums %s / %s not found for SubMG run %s', 
                            read_file_checksum_1, read_file_checksum_2, submg_run.id)
                continue
            
            if read_count > 1:
                logger.warning('Multiple reads (%d) found with checksums %s / %s for SubMG run %s, using first match', 
                           read_count, read_file_checksum_1, read_file_checksum_2, submg_run.id)
            
            read = read_query.first()
            
        except Exception as e:
            logger.error('Error finding read with checksums %s / %s for SubMG run %s: %s', 
                        read_file_checksum_1, read_file_checksum_2, submg_run.id, str(e))
            continue

        # Track this read as being in this directory
        reads_in_this_directory.append(read)

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
    # Try multiple patterns for assembly files in both logging and staging directories
    assembly_files = []
    assembly_patterns = [
        'assembly_fasta/webin-cli.report',

    ]
    

        #     'assembly_fasta/*/webin-cli.report',
        # 'assembly_fasta/**/webin-cli.report',
        # '**/assembly_fasta/webin-cli.report',
        # '**/webin-cli.report',
        # 'assembly_submission/**/webin-cli.report',
        # '**/assembly_submission/**/webin-cli.report'
        
    # Search in logging directory
    for pattern in assembly_patterns:
        files = sorted(logging_dir.glob(pattern))
        if files:
            assembly_files.extend(files)
            logger.info(f"Found {len(files)} assembly files with pattern '{pattern}' in {logging_dir}")
    
    # Also search in staging directory (already determined above)
    if staging_dir.exists():
        for pattern in assembly_patterns:
            files = sorted(staging_dir.glob(pattern))
            if files:
                assembly_files.extend(files)
                logger.info(f"Found {len(files)} assembly files with pattern '{pattern}' in {staging_dir}")
    
    # Remove duplicates while preserving order
    assembly_files = list(dict.fromkeys(assembly_files))
    logger.info(f"Total assembly files found: {len(assembly_files)}")
    
    if not assembly_files:
        logger.warning(f"No assembly files found in {logging_dir} or {staging_dir}")
        # List all files in the directories for debugging
        logger.info(f"Files in {logging_dir}:")
        for file in sorted(logging_dir.rglob('*')):
            if file.is_file():
                logger.info(f"  {file}")
        if staging_dir.exists():
            logger.info(f"Files in {staging_dir}:")
            for file in sorted(staging_dir.rglob('*')):
                if file.is_file():
                    logger.info(f"  {file}")
    
    # Get assemblies for reads processed in this directory only
    read_ids_in_this_directory = [read.id for read in reads_in_this_directory]
    if read_ids_in_this_directory:
        assemblies = Assembly.objects.filter(order=order, read_id__in=read_ids_in_this_directory)
        logger.info(f"Found {assemblies.count()} assemblies for {len(read_ids_in_this_directory)} reads in this directory")
    else:
        logger.warning('No reads found in this directory, skipping assembly processing')
        assemblies = Assembly.objects.none()
    
    if assemblies.count() == 0:
        logger.error('No assembly found for reads in this directory (order %s)', order.id)
    elif assemblies.count() == 1 and len(assembly_files) == 1:
        # Simple case: one assembly, one file
        assembly = assemblies.first()
        assembly_path = Path(assembly_files[0])
        logger.info(f"Processing single assembly {assembly.id} with single file {assembly_path}")
        process_single_assembly_file(assembly, assembly_path, order)
    else:
        # Multiple assemblies and/or multiple files - need to match them properly
        logger.warning(f"Multiple assemblies ({assemblies.count()}) and/or files ({len(assembly_files)}) found")
        logger.warning(f"Assemblies: {[a.id for a in assemblies]}")
        logger.warning(f"Files: {[str(f) for f in assembly_files]}")
        
        # For now, process each assembly with the first available file
        # This is a temporary solution - ideally we'd match files to assemblies more intelligently
        for i, assembly in enumerate(assemblies):
            if i < len(assembly_files):
                assembly_path = Path(assembly_files[i])
                logger.info(f"Processing assembly {assembly.id} with file {assembly_path}")
                process_single_assembly_file(assembly, assembly_path, order)
            else:
                logger.warning(f"No file available for assembly {assembly.id}")

    # Process assembly samples for this directory
    assembly_sample_samplesheet_path = staging_dir / 'assembly_submission' / 'co_assembly_sample' / 'coassembly_samplesheet.xml'
    if assembly_sample_samplesheet_path and assembly_sample_samplesheet_path.exists():
        assembly_sample_title_dict = {}
        assembly_sample_name_dict = {}
        assembly_sample_attributes_dict = {}

        # Initialize variables to avoid UnboundLocalError
        assembly_sample_alias = None
        assembly_sample_title = None
        assembly_sample_name = None
        assembly_sample_attributes = []
        
        with open(assembly_sample_samplesheet_path) as assembly_sample_samplesheet_content:
            assembly_sample_samplesheet_data = assembly_sample_samplesheet_content.read()
            assembly_sample_samplesheet_xml = xmltodict.parse(assembly_sample_samplesheet_data)
            assembly_sample_samplesheet_json = json.loads(json.dumps(assembly_sample_samplesheet_xml))
            for samplesheet_attribute, samplesheet_value in assembly_sample_samplesheet_json.items():
                if not isinstance(samplesheet_value, dict):
                    continue
                for sample_attribute, sample_value in samplesheet_value.items():
                    if not isinstance(sample_value, dict):
                        continue
                    for attribute, value in sample_value.items():
                        if attribute == '@alias':
                            assembly_sample_alias = value
                        if attribute == 'TITLE':
                            assembly_sample_title = value
                        if attribute == 'SAMPLE_NAME':
                            assembly_sample_name = value
                        if attribute == 'SAMPLE_ATTRIBUTES':
                            if isinstance(value, dict):
                                assembly_sample_attributes = value.items()
                            elif isinstance(value, list):
                                assembly_sample_attributes = []
                                for item in value:
                                    if isinstance(item, dict):
                                        assembly_sample_attributes.extend(item.items())
                            else:
                                assembly_sample_attributes = []                                
            
            # Check if we found the required data
            if not assembly_sample_alias or not assembly_sample_title:
                logger.warning('Incomplete assembly sample data found in samplesheet for order %s', order.id)
                return
                
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

    # Process bins for this directory
    bin_files = sorted(logging_dir.glob('bins/bin_to_preliminary_accession.tsv'))
    logger.info(f"Found {len(bin_files)} bin files: {[str(f) for f in bin_files]}")
    
    # Process each bin file only once to avoid duplicate processing
    processed_bins = set()  # Track which bins we've already processed
    
    for bin_file in bin_files:
        logger.info(f"Processing bin file: {bin_file}")
        with open(bin_file) as bin_file_content:
            for line in bin_file_content:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                    
                parts = line.split()
                if len(parts) < 2:
                    logger.warning(f"Skipping malformed line in {bin_file}: {line}")
                    continue
                    
                bin_id = parts[0].rstrip(' ')
                bin_number = bin_id.split('.')[1]
                bin_accession_id = parts[1].lstrip(' ')
                
                # Create a unique key for this bin to avoid duplicate processing
                # Include the file path to distinguish between bins from different assemblies
                bin_key = f"{order.id}_{bin_number}_{bin_file.name}"
                if bin_key in processed_bins:
                    logger.warning(f"Bin {bin_number} from file {bin_file.name} for order {order.id} already processed, skipping")
                    continue
                    
                processed_bins.add(bin_key)
                logger.info(f"Processing bin {bin_number} with accession ID {bin_accession_id} from file {bin_file.name}")
                
                try:
                    # Debug: Log existing assembly accession numbers for this order
                    existing_assembly_accessions = list(Assembly.objects.filter(order=order).values_list('assembly_accession_number', flat=True))
                    logger.info(f"Existing assembly accession numbers for order {order.id}: {existing_assembly_accessions}")
                    
                    # Debug: Log existing bin accession numbers for this order
                    existing_bin_accessions = list(Bin.objects.filter(order=order).values_list('bin_accession_number', flat=True))
                    logger.info(f"Existing bin accession numbers for order {order.id}: {existing_bin_accessions}")
                    
                    # Debug: Log the current bin accession ID being processed
                    logger.info(f"Processing bin {bin_number} with accession ID: {bin_accession_id}")
                    
                    # First check if this accession ID is already assigned to ANY bin
                    # If it is, this means this bin has already been processed
                    existing_bin_with_accession = Bin.objects.filter(
                        order=order,
                        bin_accession_number=bin_accession_id
                    ).first()
                    
                    if existing_bin_with_accession:
                        logger.info(f"Bin accession ID {bin_accession_id} is already assigned to bin {existing_bin_with_accession.id} (bin_number: {existing_bin_with_accession.bin_number}). Skipping duplicate processing.")
                        continue  # Skip this processing - already done
                    
                    # Note: We don't check for conflicts with assembly accession IDs because:
                    # 1. Assembly accession IDs are analysis accession IDs (ERZ prefix)
                    # 2. Bin accession IDs are preliminary accession IDs (ERS prefix) 
                    # 3. They are different types of accession IDs and can legitimately have the same base number
                    
                    # Find bins that match this bin_number - the suffix alone is not unique
                    # We need to find the bin that doesn't have an accession number yet
                    bins = Bin.objects.filter(order=order, bin_number=bin_number)
                    
                    if bins.count() > 1:
                        # Multiple bins with same suffix (001, 002, etc.)
                        # Find one that doesn't have an accession number yet
                        target_bin = None
                        for bin in bins:
                            if not bin.bin_accession_number:
                                target_bin = bin
                                break
                        
                        if target_bin:
                            target_bin.bin_accession_number = bin_accession_id
                            target_bin.save()
                            logger.info(f"Updated bin {target_bin.id} with accession ID {bin_accession_id} from file {bin_file.name}")
                        else:
                            # All bins with this suffix already have accession numbers assigned
                            logger.warning('All bins with suffix %s for order %s already have accession numbers. File: %s', bin_number, order.id, bin_file.name)
                    elif bins.count() == 1:
                        bin = bins.first()
                        if not bin.bin_accession_number:
                            bin.bin_accession_number = bin_accession_id
                            bin.save()
                            logger.info(f"Updated bin {bin.id} with accession ID {bin_accession_id} from file {bin_file.name}")
                        else:
                            logger.warning('Bin %s for order %s already has accession number %s, skipping. File: %s', bin_number, order.id, bin.bin_accession_number, bin_file.name)
                    else:
                        logger.warning('Bin with suffix %s not found for order %s', bin_number, order.id)
                        continue
                except Exception as e:
                    logger.error('Error processing bin %s for order %s: %s', bin_number, order.id, str(e))
                    continue

    # Process bin samples for this directory
    bin_sample_samplesheet_path = staging_dir / 'bins' / 'bin_samplesheet' / 'bins_samplesheet.xml'
    if bin_sample_samplesheet_path and bin_sample_samplesheet_path.exists():
        bin_sample_title_dict = {}
        bin_sample_name_dict = {}
        bin_sample_attributes_dict = {}

        # Initialize variables to avoid UnboundLocalError
        bin_sample_alias = None
        bin_sample_title = None
        bin_sample_name = None
        bin_sample_attributes = []

        with open(bin_sample_samplesheet_path) as bin_sample_samplesheet_content:
            bin_sample_samplesheet_data = bin_sample_samplesheet_content.read()
            logger.info(f"Processing bin samplesheet: {bin_sample_samplesheet_path}")
            logger.debug(f"XML content length: {len(bin_sample_samplesheet_data)} characters")
            
            bin_sample_samplesheet_xml = xmltodict.parse(bin_sample_samplesheet_data)
            bin_sample_samplesheet_json = json.loads(json.dumps(bin_sample_samplesheet_xml))
            
            logger.info(f"Parsed XML structure keys: {list(bin_sample_samplesheet_json.keys())}")
            
            for samplesheet_attribute, samplesheet_value in bin_sample_samplesheet_json.items():
                logger.debug(f"Processing samplesheet attribute: {samplesheet_attribute}")
                logger.debug(f"Samplesheet value type: {type(samplesheet_value)}")
                
                if not isinstance(samplesheet_value, dict):
                    logger.debug(f"Skipping non-dict samplesheet_value: {samplesheet_value}")
                    continue
                    
                logger.debug(f"Samplesheet value keys: {list(samplesheet_value.keys())}")
                
                for sample_attribute, sample_value in samplesheet_value.items():
                    logger.debug(f"Processing sample attribute: {sample_attribute}")
                    logger.debug(f"Sample value type: {type(sample_value)}")
                    
                    if not isinstance(sample_value, dict):
                        logger.debug(f"Skipping non-dict sample_value: {sample_value}")
                        continue
                        
                    logger.debug(f"Sample value keys: {list(sample_value.keys())}")
                    
                    for attribute, value in sample_value.items():
                        logger.debug(f"Processing attribute: {attribute} = {value}")
                        if attribute == '@alias':
                            bin_sample_alias = value
                            logger.info(f"Found bin_sample_alias: {bin_sample_alias}")
                        if attribute == 'TITLE':
                            bin_sample_title = value
                            logger.info(f"Found bin_sample_title: {bin_sample_title}")
                        if attribute == 'SAMPLE_NAME':
                            bin_sample_name = value
                            logger.info(f"Found bin_sample_name: {bin_sample_name}")
                        if attribute == 'SAMPLE_ATTRIBUTES':
                            if isinstance(value, dict):
                                bin_sample_attributes = value.items()
                            elif isinstance(value, list):
                                bin_sample_attributes = []
                                for item in value:
                                    if isinstance(item, dict):
                                        bin_sample_attributes.extend(item.items())
                            else:
                                bin_sample_attributes = []
                            logger.info(f"Found bin_sample_attributes: {len(bin_sample_attributes)} items")
            
            # Check if we found the required data
            if not bin_sample_alias or not bin_sample_title:
                logger.warning('Incomplete bin sample data found in samplesheet for order %s', order.id)
                return
                
            bin_sample_title_dict[bin_sample_alias] = bin_sample_title
            bin_sample_name_dict[bin_sample_alias] = bin_sample_name
            bin_sample_attributes_dict[bin_sample_alias] = bin_sample_attributes

            # Extract the bin identifier from the title
            # Original title might be like "coasm_bin_MEGAHIT-MaxBin2-sample_1.001" or "sample_1.001"
            bin_sample_full_title = re.sub('_virtual_sample', '', re.sub('.*coasm_bin_MEGAHIT-MaxBin2-', '', bin_sample_title))
            bin_sample_prefix = bin_sample_full_title.split('.')[0]  # e.g., "sample_1"
            bin_sample_number = bin_sample_full_title.split('.')[1]  # e.g., "001"
            
            # bin_sample_title is used later as the sample alias, so use the full title
            bin_sample_title = bin_sample_full_title
            
            logger.info(f"Looking for bin with prefix '{bin_sample_prefix}' and suffix '{bin_sample_number}'")

            # Handle multiple bins with same suffix (001, 002, etc.)
            # The suffix alone is not unique - we need to match based on the sample prefix
            # by checking if the bin's file path contains the sample prefix
            bins = Bin.objects.filter(order=order, bin_number=bin_sample_number)
            
            if bins.count() > 1:
                # Multiple bins with same suffix - need to match by checking the file path
                bin = None
                for b in bins:
                    # Check if this bin's file path contains the sample prefix
                    if b.file and bin_sample_prefix in b.file:
                        # Also check if it doesn't already have a sample
                        if not Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_BIN, bin=b).exists():
                            bin = b
                            logger.info(f"Matched bin {b.id} based on file path containing '{bin_sample_prefix}'")
                            break
                
                # If still not found, try any bin that matches the file path
                if not bin:
                    for b in bins:
                        if b.file and bin_sample_prefix in b.file:
                            bin = b
                            logger.info(f"Matched bin {b.id} based on file path (already has sample)")
                            break
                
                # If still not found, use the first one without a sample
                if not bin:
                    for b in bins:
                        if not Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_BIN, bin=b).exists():
                            bin = b
                            logger.warning(f"Multiple bins found for suffix {bin_sample_number}, using bin {bin.id} without sample")
                            break
                
                # Last resort: use the first one
                if not bin:
                    bin = bins.first()
                    logger.warning(f"Multiple bins found for suffix {bin_sample_number}, using first one (bin {bin.id})")
            elif bins.count() == 1:
                bin = bins.first()
            else:
                logger.error(f"No bins found for suffix {bin_sample_number} in order {order.id}")
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
        # Get the mag_run_id from the instance to fetch fresh from DB
        mag_run_id = mag_run_instance.magRun_id
    except MagRunInstance.DoesNotExist:
        logger.error(f"MagRunInstance with id {id} does not exist")
        raise ValueError(f"MagRunInstance with id {id} does not exist")
    
    # Fetch MagRun fresh from database to ensure relationships are properly initialized
    try:
        mag_run = MagRun.objects.get(id=mag_run_id)
    except MagRun.DoesNotExist:
        logger.error(f"MagRun for MagRunInstance {id} does not exist")
        raise ValueError(f"MagRun for MagRunInstance {id} does not exist")

    # Query reads directly through the ManyToMany through table to avoid manager issues
    # This is more reliable than accessing via the manager
    through_model = MagRun.reads.through
    # Get the field names from the through model
    # Django uses <lowercase_model_name>_id for the fields
    magrun_field = f'{MagRun._meta.model_name}_id'
    read_field = f'{Read._meta.model_name}_id'
    read_ids = through_model.objects.filter(**{magrun_field: mag_run.id}).values_list(read_field, flat=True)
    project_ids = set(
        Read.objects.filter(id__in=read_ids).values_list('sample__order__project_id', flat=True)
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
                    if sample_ids and existing_assembly.read:
                        # read is a ForeignKey (single Read object), not a ManyToMany
                        read_id = existing_assembly.read.id
                        assembly_map.setdefault(read_id, set()).update(sample_ids)

            assembly = None  # Initialize assembly variable
            assembly_file_path = f"{run_folder}/Assembly/MEGAHIT/MEGAHIT-{sample.sample_id}.contigs.fa.gz"
            assembly_file = Path(assembly_file_path)
            if assembly_file.is_file():
                try:
                    assembly = Assembly(file=str(assembly_file), order=order, read=read)
                    assembly.save()
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
