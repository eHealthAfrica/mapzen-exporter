import logging
LOG = logging.getLogger(__file__)

import os
import wgetter
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


def download(url, output_dir):
    filename = wgetter.download(url, outdir=output_dir)
    if filename:
        LOG.info('Downloaded file is at %s ...', filename)
    return filename


def extract(filename, output_dir):
    LOG.info('Extracting %s into folder %s', filename, output_dir)
    with tarfile.open(filename) as f:
        f.extractall(path=output_dir)
    LOG.info('File extraction completed!')
