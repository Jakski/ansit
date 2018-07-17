import logging
import os
import shutil
import hashlib
from unittest import TestCase

from ansit.environment import Environment
from ansit.manifest import Manifest
from ansit.util import read_yaml_file


class TestEnvironment(TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.CRITICAL)
        cls.env = Environment(
            Manifest.from_file('tests/examples/good_manifest.yml'))
        cls.env.synchronize()
        cls.env.apply_changes()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.env._manifest['tmp_dir'])

    def md5sum(self, path):
        with open(path, 'rb') as src:
            return hashlib.md5(src.read()).hexdigest()

    def test_template(self):
        self.assertEqual(
            self.md5sum('tests/examples/rendered_template.yml'),
            self.md5sum('.ansit/examples/template.yml'))

    def test_copy(self):
        self.assertEqual(
            self.md5sum('tests/examples/copy_src.txt'),
            self.md5sum('.ansit/examples/copy_dest.txt'))

    def test_remove(self):
        content = read_yaml_file('.ansit/examples/test_yaml.yml')
        self.assertEqual(content.get('test_var3'), None)

    def test_add(self):
        content = read_yaml_file('.ansit/examples/test_yaml.yml')
        self.assertEqual(len(content['test_var2']['subvar2']), 4)

    def test_update(self):
        content = read_yaml_file('.ansit/examples/test_yaml.yml')
        self.assertEqual(content['test_var1'], 'val1_test')
