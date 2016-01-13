#!/usr/bin/python2
# -*- coding: utf-8 -*-

import argparse
import wgetter

from settings.mapzen_settings import MapZenSettings
from utility import utils
from parser import process
import os

argparser = argparse.ArgumentParser(
    description='Exports given OSM data file admin levels for given country id'
)

argparser.add_argument(
    '--settings', default='settings.yaml',
    help='path to the settings file, default: settings.yaml'
)

sub_tasks = argparser.add_subparsers(title='Tasks')

# Initialize folder task
def init_dir(args):
    config = MapZenSettings(args.settings)
    settings = config.get_settings()
    dest = settings.get('sources').get('data_dir')
    input_dir = settings.get('sources').get('input_dir')
    output_dir = settings.get('sources').get('output_dir')

    utils.init_path(dest)
    utils.init_path(output_dir)
    utils.init_path(input_dir)


task_init_dir = sub_tasks.add_parser(
    'init_dir', help='Initializes data directory'
)
task_init_dir.set_defaults(func=init_dir)


# Download OSM data file task
def download_OSM(args):
    config = MapZenSettings(args.settings)
    settings = config.get_settings()
    dest = settings.get('sources').get('data_dir')
    url = settings.get('sources').get('data_url')
    filename = settings.get('sources').get('filename')

    file_path = wgetter.download(url, outdir=dest)
    data_file = os.path.join(dest, filename)
    if file_path:
        os.rename(file_path, data_file)


task_download_osm = sub_tasks.add_parser(
    'download_OSM', help='Downloads OSM data file from given URl'
)
task_download_osm.set_defaults(func=download_OSM)


# Extract geojson from OSM data file using Fences Builder
def extract_admins(args):
    config = MapZenSettings(args.settings)
    settings = config.get_settings()
    input_dir = settings.get('sources').get('input_dir')
    dest = settings.get('sources').get('data_dir')
    filename = settings.get('sources').get('filename')
    data_file = os.path.join(dest, filename)
    cmd = 'fences-builder --inputFile={in_file} --outputDir={out_dir}'.format(in_file=data_file, out_dir=input_dir)

    result = os.system(cmd)
    if result is not 0:
        raise SystemExit('Fence Builder extraction of OSM data file failed with error code: ', result)


task_extract_admin = sub_tasks.add_parser(
    'extract_admins', help='Extract admin levels from given OSM data file'
)
task_extract_admin.set_defaults(func=extract_admins)


# Parse and export a given country geojson
def generate_output(args):
    config = MapZenSettings(args.settings)
    settings = config.get_settings()
    input_dir = settings.get('sources').get('input_dir')
    output_dir = settings.get('sources').get('output_dir')
    country_id = settings.get('country_osm_id')
    admin_levels = sorted(settings.get('admin_levels'))
    tolerance = settings.get('tolerance')

    process.parse(input_dir, output_dir, admin_levels, tolerance, country_id)


task_generate_output = sub_tasks.add_parser(
    'generate_output', help='Read admin level geojsons from input dir and export'
)
task_generate_output.set_defaults(func=generate_output)


# Run all task from start to end
def run_all(args):
    init_dir(args)
    download_OSM(args)
    extract_admins(args)
    generate_output(args)

task_run_all = sub_tasks.add_parser(
    'run_all', help='Run all subtasks from start to finish'
)
task_run_all.set_defaults(func=run_all)


if __name__ == '__main__':
    args = argparser.parse_args()
    args.func(args)

