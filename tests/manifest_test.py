import logging
from os import path, getcwd
from unittest import TestCase

from jsonschema import ValidationError

from ansit.manifest import Manifest


class TestManifest(TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.CRITICAL)
        cls.path = path.join(getcwd(), 'tests')

    def from_file(self, src):
        return Manifest.from_file(path.join(self.path, src))

    def validation_error(self, src):
        error = None
        try:
            self.from_file(src)
        except Exception as e:
            error = e
        self.assertIsInstance(error, ValidationError)

    def test_good_manifest(self):
        manifest = self.from_file('examples/good_manifest.yml')
        self.assertEqual(manifest['root_directory'], '../')
        self.assertEqual(manifest['driver'], 'vagrant')

    def test_bad_machine(self):
        self.validation_error('examples/bad_manifest1.yml')

    def test_bad_change(self):
        self.validation_error('examples/bad_manifest2.yml')
