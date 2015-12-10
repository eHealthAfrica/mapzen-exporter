import utils
import os
import json
import unittest
import shutil
import tarfile
from os.path import expanduser


class UtilsTestCase(unittest.TestCase):

    def setUp(self):
        # get user home dir
        home_dir = expanduser("~")
        # empty string to force creation of output dir
        self.base_dir = os.path.join(home_dir, 'mapzen_test_dir')
        self.output_dir = os.path.join(self.base_dir, 'output', '')
        self.test_file = os.path.join(self.output_dir, 'test.json')

        cwd = os.path.dirname(os.path.abspath(__file__))
        self.archive_file = os.path.join(cwd, 'test-data', 'test-archive.tar.gz')

        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)

    def test_init_path(self):
        assert os.path.exists(self.output_dir) is False
        utils.init_path(self.output_dir)
        assert os.path.exists(self.output_dir) is True

    def test_init_path_clear_non_empty_dir(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        data = 'hello world! test data'
        with open(self.test_file, "w") as outfile:
            json.dump(data, outfile)
        assert os.path.exists(self.test_file) is True
        utils.init_path(self.output_dir)
        assert os.path.exists(self.test_file) is False

    def test_extract(self):
        #empty output directory
        utils.init_path(self.output_dir)
        utils.extract(self.archive_file, self.output_dir)
        files = os.listdir(self.output_dir)

        with tarfile.open(self.archive_file) as f:
            for file in files:
                assert file in f.getnames()






