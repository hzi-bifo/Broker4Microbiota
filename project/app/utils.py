import hashlib
import shutil
import gzip
import os
import glob
from pathlib import Path
from django.conf import settings

def calculate_md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def gzip_file(input, output):
    with open(input, 'rb') as f_in:
        with gzip.open(output, 'wb', compresslevel=5) as f_out:
            f_out.writelines(f_in)


def get_ena_credentials():
    """
    Get ENA credentials from SiteSettings or fall back to environment variables.
    Returns a tuple of (username, password, test_mode, center_name).
    """
    from .models import SiteSettings
    
    try:
        site_settings = SiteSettings.get_settings()
        
        # Get credentials from database first
        username = site_settings.ena_username
        password = site_settings.get_ena_password()
        test_mode = site_settings.ena_test_mode
        center_name = site_settings.ena_center_name
        
        # Fall back to environment variables if not set in database
        if not username:
            username = settings.ENA_USERNAME or ''
        if not password:
            password = settings.ENA_PASSWORD or ''
            
        return username, password, test_mode, center_name
        
    except Exception:
        # If anything goes wrong, fall back to environment variables
        return (
            settings.ENA_USERNAME or '',
            settings.ENA_PASSWORD or '',
            True,  # Default to test mode
            ''     # No center name by default
        )


def discover_sequencing_files(order, data_path):
    """
    Discover FASTQ files for samples in an order by searching a directory.
    
    Args:
        order: Order instance containing samples to search for
        data_path: Directory path to search for sequencing files
    
    Returns:
        Dictionary mapping sample IDs to found file paths:
        {
            sample_id: {
                'sample': Sample instance,
                'file_1': path to first/forward read file,
                'file_2': path to second/reverse read file (optional),
                'errors': list of any errors encountered
            }
        }
    """
    from .models import Sample, Read, SAMPLE_TYPE_NORMAL
    
    results = {}
    
    if not os.path.exists(data_path):
        return {'error': f'Sequencing data path does not exist: {data_path}'}
    
    if not os.path.isdir(data_path):
        return {'error': f'Sequencing data path is not a directory: {data_path}'}
    
    # Get all samples without reads
    samples = Sample.objects.filter(order=order, sample_type=SAMPLE_TYPE_NORMAL)
    
    for sample in samples:
        # Try sample_id first (like SAMPLE_1753087065861), then fall back to sample_alias
        sample_identifier = None
        if hasattr(sample, 'sample_id') and sample.sample_id:
            sample_identifier = sample.sample_id
        elif sample.sample_alias:
            sample_identifier = sample.sample_alias
            
        result = {
            'sample': sample,
            'file_1': None,
            'file_2': None,
            'errors': []
        }
        
        # Skip if sample has no identifier
        if not sample_identifier:
            result['errors'].append(f'Sample has no sample_id or alias defined')
            results[sample.id] = result
            continue
        
        # Search for files with exact identifier match
        # Support multiple naming patterns but ensure exact match
        patterns = [
            f"{sample_identifier}_1.fastq.gz",
            f"{sample_identifier}_2.fastq.gz",
            f"{sample_identifier}_R1.fastq.gz",
            f"{sample_identifier}_R2.fastq.gz",
            f"{sample_identifier}.fastq.gz",
            # Also support patterns with additional suffixes (e.g., lane info)
            f"{sample_identifier}_*_1.fastq.gz",
            f"{sample_identifier}_*_2.fastq.gz",
            f"{sample_identifier}_*_R1.fastq.gz",
            f"{sample_identifier}_*_R2.fastq.gz"
        ]
        
        found_files = []
        for pattern in patterns:
            matches = glob.glob(os.path.join(data_path, pattern))
            found_files.extend(matches)
        
        # Remove duplicates
        found_files = list(set(found_files))
        
        if not found_files:
            result['errors'].append(f'No FASTQ files found for sample {sample_identifier}')
        else:
            # Try to identify paired files
            file_1_candidates = []
            file_2_candidates = []
            
            for file_path in found_files:
                filename = os.path.basename(file_path)
                # Check if it's a forward/R1 read
                if '_1.fastq.gz' in filename or '_R1.fastq.gz' in filename:
                    file_1_candidates.append(file_path)
                # Check if it's a reverse/R2 read
                elif '_2.fastq.gz' in filename or '_R2.fastq.gz' in filename:
                    file_2_candidates.append(file_path)
                # If neither pattern matches, could be single-end
                else:
                    file_1_candidates.append(file_path)
            
            # Select the best candidates
            if file_1_candidates:
                # Filter to ensure exact sample alias match (not substring)
                exact_matches = []
                for f in file_1_candidates:
                    basename = os.path.basename(f)
                    # Check if filename starts with sample_identifier followed by _ or .
                    if basename.startswith(f"{sample_identifier}_") or basename == f"{sample_identifier}.fastq.gz":
                        exact_matches.append(f)
                
                if exact_matches:
                    # Prefer the simplest naming pattern
                    for pattern in [f"{sample_identifier}_1.fastq.gz", f"{sample_identifier}_R1.fastq.gz"]:
                        for f in exact_matches:
                            if os.path.basename(f) == pattern:
                                result['file_1'] = f
                                break
                        if result['file_1']:
                            break
                    # If no simple pattern found, use the first exact match
                    if not result['file_1']:
                        result['file_1'] = exact_matches[0]
                else:
                    result['errors'].append(f'Found FASTQ files but none with exact match for {sample_identifier}')
                
                # Validate the file if we found one
                if result['file_1'] and not validate_fastq_gz_file(result['file_1']):
                    result['errors'].append(f"File {result['file_1']} is not a valid gzipped FASTQ file")
                    result['file_1'] = None
            
            if file_2_candidates:
                # Filter to ensure exact sample alias match (not substring)
                exact_matches = []
                for f in file_2_candidates:
                    basename = os.path.basename(f)
                    # Check if filename starts with sample_identifier followed by _ or .
                    if basename.startswith(f"{sample_identifier}_") or basename == f"{sample_identifier}.fastq.gz":
                        exact_matches.append(f)
                
                if exact_matches:
                    # Prefer the simplest naming pattern
                    for pattern in [f"{sample_identifier}_2.fastq.gz", f"{sample_identifier}_R2.fastq.gz"]:
                        for f in exact_matches:
                            if os.path.basename(f) == pattern:
                                result['file_2'] = f
                                break
                        if result['file_2']:
                            break
                    # If no simple pattern found, use the first exact match
                    if not result['file_2']:
                        result['file_2'] = exact_matches[0]
                else:
                    result['errors'].append(f'Found FASTQ files but none with exact match for {sample_identifier}')
                
                # Validate the file if we found one
                if result['file_2'] and not validate_fastq_gz_file(result['file_2']):
                    result['errors'].append(f"File {result['file_2']} is not a valid gzipped FASTQ file")
                    result['file_2'] = None
            
            # Check if we have at least one valid file
            if not result['file_1'] and not result['file_2']:
                result['errors'].append(f'No valid FASTQ files found for sample {sample_identifier}')
        
        results[sample.id] = result
    
    return results


def validate_fastq_gz_file(file_path):
    """
    Validate that a file exists and appears to be a gzipped FASTQ file.
    
    Args:
        file_path: Path to the file to validate
    
    Returns:
        bool: True if file appears valid, False otherwise
    """
    if not os.path.exists(file_path):
        return False
    
    if not os.path.isfile(file_path):
        return False
    
    # Check file extension
    if not file_path.endswith('.fastq.gz') and not file_path.endswith('.fq.gz'):
        return False
    
    # Try to read the first few bytes to verify it's gzipped
    try:
        with gzip.open(file_path, 'rb') as f:
            # Try to read first line - should start with @ for FASTQ
            first_line = f.readline()
            if not first_line.startswith(b'@'):
                return False
        return True
    except Exception:
        return False
