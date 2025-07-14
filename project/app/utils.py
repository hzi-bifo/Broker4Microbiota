import hashlib
import shutil
import gzip
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
