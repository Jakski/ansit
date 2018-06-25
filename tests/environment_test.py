import logging
import hashlib
from os import path, getcwd
from unittest import TestCase

import yaml

from ansit.environment import Environment
from ansit.manifest import Manifest


class TestEnvironment(TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.CRITICAL)
        cls.path = path.join(getcwd(), 'tests')
        cls.env = Environment(Manifest.from_file(
            path.join(cls.path, 'examples/good_manifest.yml')))

    def md5sum(self, f):
        with open(f, 'rb') as src:
            return hashlib.md5(src.read()).hexdigest()

    def load_yaml(self, f):
        with open(f, 'r', encoding='utf-8') as src:
            return yaml.load(src)

    def test_synchronisation(self):
        src = self.md5sum(path.join(
            self.path,
            'examples/good_manifest.yml'))
        dest = self.md5sum(path.join(
            self.env.dir,
            'examples/good_manifest.yml'))
        self.assertEqual(src, dest)

    def test_update(self):
        manifest = self.load_yaml(path.join(
            self.env.dir,
            'examples/good_manifest.yml'))
        self.assertEqual(manifest['root_directory'], 'test')

    def test_add(self):
        manifest = self.load_yaml(path.join(
            self.env.dir,
            'examples/good_manifest.yml'))
        self.assertIn('test', manifest['stages'])

    def test_remove(self):
        manifest = self.load_yaml(path.join(
            self.env.dir,
            'examples/good_manifest.yml'))
        self.assertNotIn('all', manifest['stages'])

    def test_template(self):
        template = self.load_yaml(path.join(
            self.env.dir,
            'examples/template.yml'))
        self.assertEqual('test', template['var1'])
