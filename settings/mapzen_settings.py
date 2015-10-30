import logging
logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger('mapzen_settings.log')

import sys
import yaml
import os


class MapZenSettings():
    settings = {}
    admin_levels = {}

    def __init__(self, settings_file, verbose=False):
        self.settingsFile = settings_file
        self._readSettings()
        self.verbose = verbose

    def _readSettings(self):
        LOG.debug('Reading settings from %s', self.settingsFile)
        if not(self.is_file_readable(self.settingsFile)):
            LOG.error('File "%s" is not readable', self.settingsFile)
            sys.exit(99)

        with open(self.settingsFile, 'r') as tmpfile:
            self.settings.update(yaml.load(tmpfile))

    def is_file_readable(self, path):
        if os.path.isfile(path):
            if os.access(path, os.R_OK):
                return True
            else:
                LOG.error('Missing read permission: %s', path)
        else:
            LOG.error('File not found: %s', path)

    def get_settings(self):
        return self.settings