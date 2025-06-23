import hashlib
import shutil
import gzip

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
