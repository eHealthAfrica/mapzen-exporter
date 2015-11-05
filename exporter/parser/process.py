#!/usr/bin/python2
# -*- coding: utf-8 -*-


import logging
LOG = logging.getLogger(__file__)

import os
import json
from osgeo import ogr


def format_feature(feature):
    feat_json = json.loads(feature.ExportToJson())
    properties = feat_json.get('properties')
    return {
        'properties': {
            'osm_id': feat_json.get('id'),
            'name': feat_json.get('name'),
            'name_en': properties.get('name:en'),
            'iso3166': properties.get('ISO3166-1'),
            'is_in_country': None,
            'is_in_state': None,
            'is_in_lga': None,
            'is_in_ward': None
        },
        'geometry': feature.GetGeometryRef()
    }


def read_feature(filename):
    data_source = ogr.Open(filename)
    lyr_count = data_source.GetLayerCount()
    is_data_in_layer = True
    feature_count = 0

    while is_data_in_layer:
        is_data_in_layer = False
        for iLayer in xrange(lyr_count):
            lyr = data_source.GetLayer(iLayer)
            feat = lyr.GetNextFeature()
            while feat is not None:
                feature_count += 1
                yield (lyr.GetName(), feat)
                feat = None
                feat = lyr.GetNextFeature()

    LOG.info('Total features read: %s', feature_count)


def parse(dir_path, admin_levels):
    filenames = []
    base_file_name = 'admin_level_{level}.geojson'
    for level in admin_levels:
        filename = base_file_name.format(level=level)
        filenames.append(os.path.join(dir_path, filename))

    filenames.sort()
    level_count = 0
    feat_1 = None
    feat_2 = None


    for f_name in filenames:
        for (name, feature) in read_feature(f_name):
            if not feat_1:
                feat_1 = feature
                result = format_feature(feat_1)
                write('/home/jofomah/mapzen-data/output/admin_level_2_simplified.geojson', result)
            if feat_1 and not feat_2:
                feat_2 = feature
                #print intersect(feat_1, feat_2)
                #print format_feature(feature)
                break

        level_count += 1


def simplify_geom(feature, tolerance=0.001):
    return feature.GetGeometryRef().SimplifyPreserveTopology(tolerance)


def prepare_feature_json(data):
    return {
        'type': 'Feature',
        'properties': data.get
        ('properties'),
        'geometry': json.loads(data.get('geometry').ExportToJson())
    }


def write(full_path, data):
    record = {
        'type': 'FeatureCollection',
        'crs': {
            'type': 'name',
            'properties': {
                'name': 'urn:ogc:def:crs:OGC:1.3:CRS84'
            }
        },
        'features': []
    }
    feature_json = prepare_feature_json(data)
    record.get('features').append(feature_json)

    with open(full_path, "w") as outfile:
        json.dump(record, outfile)


def intersect(ancestor_feat, child_feat):
    return ancestor_feat.GetGeometryRef().Intersects(child_feat.GetGeometryRef())
