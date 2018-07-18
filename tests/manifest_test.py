import logging
import os
from unittest import TestCase

from jsonschema import ValidationError

from ansit.manifest import Manifest


class TestManifest(TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.CRITICAL)
        cls.path = os.path.join(os.getcwd(), 'tests')

    def from_file(self, src):
        return Manifest.from_file(os.path.join(self.path, src))

    def validation_error(self, src):
        error = None
        try:
            self.from_file(src)
        except Exception as e:
            error = e
        self.assertIsInstance(error, ValidationError)

    def test_good_manifest(self):
        manifest = self.from_file('examples/good_manifest.yml')
        self.assertEqual(manifest['directory'], './tests')
        self.assertEqual(manifest['provision'][0]['driver'],
                         'tests.drivers.Provisioner')
        self.assertEqual(manifest['machines']['localhost']['driver'],
                         'tests.drivers.Provider')
        self.assertEqual(manifest['changes'][0]['update']['dest'],
                         '.ansit/examples/test_yaml.yml')

    def test_bad_machine(self):
        self.validation_error('examples/bad_manifest1.yml')

    def test_bad_change(self):
        self.validation_error('examples/bad_manifest2.yml')
