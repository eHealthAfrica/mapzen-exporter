import os
import unittest
import yaml

from mock import MagicMock, patch
from mapzen_settings import MapZenSettings

class MapZenSettingsTestCase(unittest.TestCase):

    def setUp(self):
        cwd = os.path.dirname(os.path.abspath(__file__))
        fixture = 'fixtures'
        self.test_settings_file = os.path.join(cwd, fixture, 'test_settings.yaml')
        self.non_file_path = os.path.join(cwd, fixture)

        with open(self.test_settings_file, 'r') as tmpfile:
            self.expected_settings = yaml.load(tmpfile)

    def test_init(self):
        mapzen_settings = MapZenSettings(self.test_settings_file)
        assert mapzen_settings.settings != {}

        assert self.expected_settings is not None
        assert self.expected_settings == mapzen_settings.settings

    def test_init_with_wrong_file(self):
        with self.assertRaises(SystemExit):
            MapZenSettings(self.non_file_path)

    def test_is_file_readable_for_non_file(self):
        mapzen_settings = MapZenSettings(self.test_settings_file)
        assert mapzen_settings.is_file_readable(self.non_file_path) is not True

    def test_is_file_readble_for_readable_file(self):
        mapzen_settings = MapZenSettings(self.test_settings_file)
        assert mapzen_settings.is_file_readable(self.test_settings_file) is True

    def test_is_file_readble_for_permission(self):
        mapzen_settings = MapZenSettings(self.test_settings_file)
        # simluate file permission status and set to False
        p = patch("os.access", new = MagicMock(return_value=False))
        p.start()
        assert mapzen_settings.is_file_readable(self.test_settings_file) is not True
        p.stop()

    def test_get_settings(self):
        mapzen_settings = MapZenSettings(self.test_settings_file)
        assert mapzen_settings.settings == mapzen_settings.get_settings()



