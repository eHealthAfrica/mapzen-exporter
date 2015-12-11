import process
import json
import os
import shutil
import unittest

from os.path import expanduser
from osgeo import ogr

class ProcessTestCase(unittest.TestCase):

    def setUp(self):
        cwd = os.path.dirname(os.path.abspath(__file__))
        self.write_file_path = os.path.join(cwd, 'test.geojson')
        fixture = 'fixtures'
        geometry_file_path = os.path.join(cwd, fixture, 'geometry.json')
        with open(geometry_file_path) as data_file:
            self.geometry = data_file.read()

        child_file = os.path.join(cwd, fixture, 'child.json')
        with open(child_file) as data_file:
            self.child_json = json.loads(data_file.read())

        self.fixture_dir = os.path.join(cwd, fixture)
        # get user home dir
        home_dir = expanduser("~")
        # empty string to force creation of output dir
        self.parse_output_dir = os.path.join(home_dir, 'parse_output_dir', '')
        if not os.path.exists(self.parse_output_dir):
            os.makedirs(self.parse_output_dir)

        self.properties = {
            'admin_level': 3,
            'is_in_country': None,
            'name': u'Kolofata',
            'parent_id': None,
            'is_simplified': True,
            'osm_id': 3749358,
            'name_en': None,
            'iso3166': None
        }
        self.tolerance = 0.001
        self.ancestor_fields = {
            'admin_level': 2,
            'is_in_country': 192830,
            'parent_id': 2750662,
            'is_simplified': None,
            'osm_id': 2750416
        }

        self.country = {
            'admin_level': 0,
            'is_in_country': None,
            'parent_id': None,
            'is_simplified': None,
            'osm_id': 192830
        }
        self.ds_file_path = os.path.join(cwd, fixture, 'admin_level_2.geojson')
        self.ds_file_path_2 = os.path.join(cwd, fixture, 'admin_level_4.geojson')
        self.output_ancestor_file_path = os.path.join(cwd, fixture, 'output', 'admin_level_0.json')

    def tearDown(self):
        self.geometry = None
        self.child_json = None
        self.country = None
        self.ancestor_fields = None
        if os.path.exists(self.write_file_path):
            os.remove(self.write_file_path)
        if os.path.exists(self.parse_output_dir):
            shutil.rmtree(self.parse_output_dir)

    def test_write(self):
        assert os.path.isfile(self.write_file_path) is False
        test_data = "test data"
        process.write(self.write_file_path, test_data)
        assert os.path.isfile(self.write_file_path) is True

        with open(self.write_file_path) as data_file:
            file_content = data_file.read()
            assert test_data in file_content

    def test_prepare_feature_json(self):
        assert self.geometry is not None

        expected_geom = json.loads(self.geometry)
        result = process.prepare_feature_json(self.properties, self.geometry)

        assert result['properties'] is self.properties
        assert result['type'] == 'Feature'
        assert result['geometry'] == expected_geom


    def test_set_ancestor_fields(self):
        assert self.child_json['properties']['parent_id'] is None
        assert self.ancestor_fields['osm_id'] is not self.child_json['properties']['parent_id']

        result = process.set_ancestor_fields(self.ancestor_fields, self.child_json)
        assert self.ancestor_fields['osm_id'] is result['properties']['parent_id']
        assert self.ancestor_fields['is_in_country'] is result['properties']['is_in_country']
        assert self.ancestor_fields['is_in_country'] is not result['properties']['parent_id']

    def test_set_ancestor_fields_for_country(self):
        assert self.country['admin_level'] is 0
        assert self.child_json['properties']['is_in_country'] is None

        result = process.set_ancestor_fields(self.country, self.child_json)
        assert self.country['osm_id'] is result['properties']['parent_id']
        assert self.country['osm_id'] is result['properties']['is_in_country']

    def test_read_feature(self):
        features = process.read_feature(self.ds_file_path)
        assert features is not None

    def test_format_feature(self):
        features = process.read_feature(self.ds_file_path)
        name, feature = features.next()

        assert feature is not None

        level = 1
        feature_json = json.loads(feature.ExportToJson())
        result = process.format_feature(feature, self.tolerance, level)

        assert result['properties']['osm_id'] == feature_json['id']
        assert result['properties']['name'] == feature_json['properties'].get('name')
        assert result['properties']['name_en'] == feature_json['properties'].get('name:en')
        assert result['properties']['iso3166'] == feature_json['properties'].get('ISO3166-1')
        assert result['properties']['admin_level'] == level

        assert result['properties']['is_in_country'] is None
        assert result['properties']['parent_id'] is None
        assert result['properties']['is_simplified'] is None

        assert result['geometry'].ExportToJson() == feature.GetGeometryRef().ExportToJson()
        assert result['simplified_geometry'].ExportToJson() == process.simplify_geom(feature, self.tolerance).ExportToJson()

    def test_format_feature_read_iso3166_2(self):
        features = process.read_feature(self.ds_file_path_2)
        name, feature = features.next()

        assert feature is not None

        level = 1
        feature_json = json.loads(feature.ExportToJson())
        result = process.format_feature(feature, self.tolerance, level)

        assert result['properties']['iso3166'] == feature_json['properties'].get('ISO3166-2')

    def test_simplify_geom(self):
        features = process.read_feature(self.ds_file_path_2)
        name, feature = features.next()

        assert feature is not None
        result = process.simplify_geom(feature, self.tolerance).ExportToJson()
        expected = feature.GetGeometryRef().SimplifyPreserveTopology(self.tolerance).ExportToJson()
        assert result == expected

    def test_intersect(self):
        features = process.read_feature(self.ds_file_path)
        name, parent_feature = features.next()

        assert parent_feature is not None

        child_features = process.read_feature(self.ds_file_path_2)
        name1, child_feature1 = child_features.next()
        name2, child_feature2 = child_features.next()

        assert process.intersect(parent_feature, child_feature2)
        assert process.intersect(child_feature1, child_feature2) is False

    def test_get_ancestor(self):
        ancestor = None
        child_features = process.read_feature(self.ds_file_path_2)
        name1, child_feature1 = child_features.next()

        data_source = ogr.Open(self.ds_file_path)
        if data_source:
            lyr = data_source.GetLayer(0)
            if lyr:
                ancestor = process.get_ancestor(lyr, child_feature1.GetGeometryRef())

        assert ancestor is not None

    def test_parse_features(self):
        level = 1
        result = process.parse_features(
            self.ds_file_path_2,
            self.output_ancestor_file_path,
            self.tolerance,
            level)

        collection, simplified_collection = result.next()
        name, expected_ancestor = process.read_feature(self.output_ancestor_file_path).next()
        expected_ancestor_json = json.loads(expected_ancestor.ExportToJson())

        first_feature = collection['features'][0]
        assert first_feature['properties']['is_simplified'] is None
        assert first_feature['properties']['parent_id'] == expected_ancestor_json['properties']['osm_id']

        first_simplified_feature = simplified_collection['features'][0]
        assert first_simplified_feature['properties']['is_simplified'] is True
        assert first_simplified_feature['properties']['parent_id'] == expected_ancestor_json['properties']['osm_id']

    def test_parse(self):
        country_level = 2
        state_level = 4
        admin_levels = [country_level, state_level]
        process.parse(self.fixture_dir, self.parse_output_dir, admin_levels, self.tolerance)

        output_files = os.listdir(self.parse_output_dir)

        assert len(output_files) == (len(admin_levels) * 2)
        assert 'admin_level_0_simplified.json' in output_files
        assert 'admin_level_1_simplified.json' in output_files
        assert 'admin_level_1.json' in output_files
        assert 'admin_level_0.json' in output_files


