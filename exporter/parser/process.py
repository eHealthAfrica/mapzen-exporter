#!/usr/bin/python2
# -*- coding: utf-8 -*-


import logging

LOG = logging.getLogger(__file__)

import os
import json
import copy
from osgeo import ogr


def format_feature(feature, tolerance):
    feat_json = json.loads(feature.ExportToJson())
    properties = feat_json.get('properties')
    iso_code = properties.get('ISO3166-1')
    if not iso_code:
        iso_code = properties.get('ISO3166-2')

    result = {
        'properties': {
            'osm_id': feat_json.get('id'),
            'name': properties.get('name'),
            'name_en': properties.get('name:en'),
            'iso3166': iso_code,
            'is_in_country': None,
            'is_in_state': None,
            'is_in_lga': None,
            'is_in_ward': None,
            'admin_level': properties.get('admin_level')
        },
        'geometry': feature.GetGeometryRef(),
        'simplified_geometry': simplify_geom(feature, tolerance)
    }
    return result


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


def get_ancestor(ancestor_lyr, child_geom):
    feature = ancestor_lyr.GetNextFeature()
    if feature is None or child_geom is None:
        return
    properties = json.loads(feature.ExportToJson()).get('properties')
    while feature is not None:
        if feature.GetGeometryRef().Intersects(child_geom):
            return {
                'osm_id': properties.get('osm_id'),
                'admin_level': properties.get('admin_level'),
                'is_in_country': properties.get('is_in_country'),
                'is_in_state': properties.get('is_in_state'),
                'is_in_lga': properties.get('is_in_lga'),
                'is_in_ward': properties.get('is_in_ward'),
            }
        feature = None
        feature = ancestor_lyr.GetNextFeature()


def parse_features(file_name, ancestor_admin_file, tolerance, lvl_count):
    temp = {
        'type': 'FeatureCollection',
        'crs': {
            'type': 'name',
            'properties': {
                'name': 'urn:ogc:def:crs:OGC:1.3:CRS84'
            }
        },
        'features': []
    }

    feat_collection = copy.deepcopy(temp)
    simplify_feature_collection = copy.deepcopy(temp)
    for (name, feature) in read_feature(file_name):
        result = format_feature(feature, tolerance)
        properties = result.get('properties')
        geom = result.get('geometry')
        simplify_geometry = result.get('simplified_geometry')

        feature_json = prepare_feature_json(properties, geom.ExportToJson())
        simplify_feat_json = prepare_feature_json(
            properties, simplify_geometry.ExportToJson())

        if lvl_count > 0:
            data_source = ogr.Open(ancestor_admin_file)
            if data_source:
                lyr = data_source.GetLayer(0)
                if lyr:
                    ancestor = get_ancestor(lyr, geom)
                    if ancestor:
                        child = set_ancestor_fields(ancestor, feature_json)
                        simplified_child = set_ancestor_fields(
                            ancestor, simplify_feat_json)

                        feat_collection.get('features').append(child)
                        simplify_feature_collection.get(
                            'features').append(simplified_child)
        else:
            feat_collection.get('features').append(feature_json)
            simplify_feature_collection.get(
                'features').append(simplify_feat_json)

    yield feat_collection, simplify_feature_collection


def set_ancestor_fields(ancestor_fields, child_json):
    in_country = 'is_in_country'
    in_state = 'is_in_state'
    in_lga = 'is_in_lga'

    if ancestor_fields:
        # TODO: read 2, 4, 6, dynamically from settings.yaml
        ancestor_level = ancestor_fields.get('admin_level')
        if ancestor_level == str(2):
            # state, set is_in_country
            child_json['properties'][
                in_country] = ancestor_fields.get('osm_id')
        elif ancestor_level == str(4):
            # LGA, set is_in_country and is_in_state
            child_json['properties'][
                in_country] = ancestor_fields.get(in_country)
            child_json['properties'][in_state] = ancestor_fields.get('osm_id')
        elif ancestor_level == str(6):
            child_json['properties'][
                in_country] = ancestor_fields.get(in_country)
            child_json['properties'][in_state] = ancestor_fields.get(in_state)
            child_json['properties'][in_lga] = ancestor_fields.get('osm_id')
    return child_json


def parse(dir_path, output_dir, admin_levels, tolerance):
    file_names = []
    base_file_name = 'admin_level_{level}.geojson'
    for level in admin_levels:
        filename = base_file_name.format(level=level)
        file_names.append(os.path.join(dir_path, filename))

    file_names.sort()
    level_count = 0

    for f_name in file_names:
        ancestor_file = ''
        ancestor_level = level_count - 1
        if ancestor_level >= 0:
            ancestor_file = os.path.join(
                output_dir, base_file_name.format(
                    level=ancestor_level))

        result = parse_features(f_name, ancestor_file, tolerance, level_count)
        collection, simplified_collection = result.next()

        file_path = os.path.join(
            output_dir, base_file_name.format(
                level=level_count))
        temp_file = '_'.join([str(level_count), 'simplified'])
        simplify_file_path = os.path.join(
            output_dir, base_file_name.format(
                level=temp_file))

        write(file_path, collection)
        write(simplify_file_path, simplified_collection)
        LOG.info('Complete parsing admin level : {} '.format(level_count))
        level_count += 1


def simplify_geom(feature, tolerance=0.001):
    return feature.GetGeometryRef().SimplifyPreserveTopology(tolerance)


def prepare_feature_json(properties, geometry):
    return {
        'type': 'Feature',
        'properties': properties,
        'geometry': json.loads(geometry)
    }


def write(full_path, data):
    with open(full_path, "w") as outfile:
        json.dump(data, outfile)


def intersect(ancestor_feat, child_feat):
    return ancestor_feat.GetGeometryRef().Intersects(child_feat.GetGeometryRef())
