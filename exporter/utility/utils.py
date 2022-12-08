import logging
LOG = logging.getLogger(__file__)

import os
import tarfile
import shutil


def init_path(full_path):
    """
    Initializes full path and recreate if already exists
    """
    dir_path = os.path.dirname(full_path)
    LOG.info('Initializing data folder:  %s ...', full_path)
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)
    LOG.info('Completed setting up data folder:  %s ...', full_path)


def extract(filename, output_dir):
    LOG.info('Extracting %s into folder %s', filename, output_dir)
    with tarfile.open(filename) as f:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(f, path=output_dir)
    LOG.info('File extraction completed!')
