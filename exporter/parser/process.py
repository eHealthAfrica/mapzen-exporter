#!/usr/bin/python2
# -*- coding: utf-8 -*-


import logging

LOG = logging.getLogger(__file__)

import os
import json
import copy
from osgeo import ogr
import rtree
import shapely.wkb
from shapely.prepared import prep


def format_feature(feature, tolerance, level):
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
            'parent_id': None,
            'is_simplified': None,
            'admin_level': level
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

    feature_id = 0
    while feature is not None:
        if intersects_spatially(feature, child_geom, feature_id):
            properties = json.loads(feature.ExportToJson()).get('properties')
            return {
                'osm_id': properties.get('osm_id'),
                'admin_level': properties.get('admin_level'),
                'parent_id': properties.get('parent_id'),
                'is_in_country': properties.get('is_in_country'),
                'is_simplified': properties.get('is_simplified')
            }

        feature_id += 1
        feature = None
        feature = ancestor_lyr.GetNextFeature()


def parse_features(file_name, ancestor_admin_file,
                   tolerance, lvl_count, country_id):
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
        result = format_feature(feature, tolerance, lvl_count)
        properties = result.get('properties')
        geom = result.get('geometry')
        simplify_geometry = result.get('simplified_geometry')

        feature_json = prepare_feature_json(properties, geom.ExportToJson())

        # prepared simplified json
        simplified_properties = copy.deepcopy(properties)
        simplified_properties['is_simplified'] = True
        simplify_feat_json = prepare_feature_json(
            simplified_properties, simplify_geometry.ExportToJson())

        if lvl_count > 0:
            data_source = ogr.Open(ancestor_admin_file)
            if data_source:
                lyr = data_source.GetLayer(0)
                if lyr:
                    ancestor = get_ancestor(lyr, geom)
                    if ancestor:
                        child = set_ancestor_fields(
                            ancestor, feature_json)

                        simplified_child = set_ancestor_fields(
                            ancestor, simplify_feat_json)

                        feat_collection.get('features').append(child)
                        simplify_feature_collection.get(
                            'features').append(simplified_child)
                    else:
                        LOG.info('Skipping {osm_id} because of unknown ancestor'.format(osm_id=
                                                                                        feature_json.get(
                                                                                            'properties').get(
                                                                                            'osm_id')))
        else:
            # parse if country level and feature osm id is expected country
            if country_id == feature_json.get('properties').get('osm_id'):
                feat_collection.get('features').append(feature_json)
                simplify_feature_collection.get(
                    'features').append(simplify_feat_json)

    yield feat_collection, simplify_feature_collection


def set_ancestor_fields(ancestor_fields, child_json):
    in_country = 'is_in_country'
    ancestor_osm_id = ancestor_fields.get('osm_id')

    if ancestor_fields:
        country_id = ancestor_fields.get(in_country)
        if not country_id and ancestor_fields.get('admin_level') == 0:
            country_id = ancestor_osm_id

        child_json['properties']['parent_id'] = ancestor_osm_id
        child_json['properties'][in_country] = country_id
    return child_json


def parse(dir_path, output_dir, admin_levels, tolerance, country_id):
    file_names = []
    base_file_name = 'admin_level_{level}.geojson'
    for level in admin_levels:
        filename = base_file_name.format(level=level)
        file_names.append(os.path.join(dir_path, filename))

    file_names.sort()
    level_count = 0

    out_base_file = 'admin_level_{level}.json'
    for f_name in file_names:
        ancestor_file = ''
        ancestor_level = level_count - 1
        if ancestor_level >= 0:
            ancestor_file = os.path.join(
                output_dir, out_base_file.format(
                    level=ancestor_level))

        result = parse_features(
            f_name,
            ancestor_file,
            tolerance,
            level_count,
            country_id)
        collection, simplified_collection = result.next()

        file_path = os.path.join(
            output_dir, out_base_file.format(
                level=level_count))
        temp_file = '_'.join([str(level_count), 'simplified'])
        simplify_file_path = os.path.join(
            output_dir, out_base_file.format(
                level=temp_file))

        write(file_path, collection)
        write(simplify_file_path, simplified_collection)
        LOG.info('Complete parsing admin level : {} '.format(level_count))
        level_count += 1

    LOG.info('Completed extraction of files from: {} to {}'.format(
        dir_path, output_dir)
    )


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


def intersects_spatially(ancestor_feat, child_geom, feature_id):
    ancestor_spat_index = rtree.index.Index()
    ancestor_admin = {}
    ancestor_geom = shapely.wkb.loads(ancestor_feat.GetGeometryRef().ExportToWkb())
    ancestor_osm_id = json.loads(ancestor_feat.ExportToJson()).get('properties').get('osm_id')

    ancestor_admin.update({ancestor_osm_id: prep(ancestor_geom)})
    ancestor_spat_index.insert(
        feature_id, ancestor_geom.envelope.bounds, obj=ancestor_osm_id
    )

    child_geom = shapely.wkb.loads(child_geom.ExportToWkb())
    # representative point is guaranteed within polygon
    child_geom_repr = child_geom.representative_point()

    for obj in ancestor_spat_index.intersection(child_geom_repr.bounds, objects=True):
        if ancestor_admin.get(obj.object).contains(child_geom_repr):
            return obj.object
    else:
        return None
