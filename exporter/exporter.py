#!/usr/bin/python2
# -*- coding: utf-8 -*-

import argparse
import wgetter

from settings.mapzen_settings import MapZenSettings
from utility import utils
from parser import process

argparser = argparse.ArgumentParser(
    description='Exports given MapZen extracts .zip file'
)

argparser.add_argument(
    '--settings', default='settings.yaml',
    help='path to the settings file, default: settings.yaml'
)

if __name__ == '__main__':
    args = argparser.parse_args()
    config = MapZenSettings(args.settings)
    settings = config.get_settings()

    url = settings.get('sources').get('mapzen_file_url')
    dest = settings.get('sources').get('data_dir')
    extracted_geojson_dir = settings.get('sources').get('geojson_dir_name')
    output_dir = settings.get('sources').get('output_dir')
    admin_levels = sorted(settings.get('admin_levels'))
    tolerance = settings.get('tolerance')

    # set up data file, extract file and
    utils.init_path(dest)
    utils.init_path(output_dir)
    file_path = wgetter.download(url, outdir=dest)
    utils.extract(file_path, dest)

    process.parse(extracted_geojson_dir, output_dir, admin_levels, tolerance)
