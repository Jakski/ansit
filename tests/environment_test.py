import logging
import os
import shutil
import hashlib
from unittest import TestCase
from unittest import mock

from ansit.environment import (
    Environment,
    Drivers)
from ansit.manifest import Manifest
from ansit.util import read_yaml_file
from ansit import drivers


logging.basicConfig(level=logging.CRITICAL)


class TestDrivers(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.drivers = Drivers(
            Manifest.from_file('tests/examples/good_manifest.yml'))

    def test_loading_provider(self):
        self.assertTrue(isinstance(
            self.drivers['tests.drivers.Provider'],
            drivers.Provider))

    def test_loading_provisioner(self):
        self.assertTrue(isinstance(
            self.drivers['tests.drivers.Provisioner'],
            drivers.Provisioner))

    def test_loading_tester(self):
        self.assertTrue(isinstance(
            self.drivers['tests.drivers.Tester'],
            drivers.Tester))


class TestEnvironmentChanges(TestCase):

    @classmethod
    def setUpClass(cls):
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
        self.assertIsNone(content.get('test_var3'))

    def test_add(self):
        content = read_yaml_file('.ansit/examples/test_yaml.yml')
        self.assertEqual(len(content['test_var2']['subvar2']), 4)

    def test_update(self):
        content = read_yaml_file('.ansit/examples/test_yaml.yml')
        self.assertEqual(content['test_var1'], 'val1_test')

    def test_creating_machines(self):
        with mock.patch('tests.drivers.Provider.up'):
            self.env.up(['localhost'])
            self.assertEqual(
                self.env._drivers[
                    'tests.drivers.Provider'
                ].up.call_count, 1)
            self.assertIn(
                'localhost',
                self.env._drivers[
                    'tests.drivers.Provider'
                ].up.call_args[0][0])

    def test_destroying_machines(self):
        with mock.patch('tests.drivers.Provider.destroy'):
            self.env.destroy(['localhost'])
            self.assertEqual(
                self.env._drivers[
                    'tests.drivers.Provider'
                ].destroy.call_count, 1)
            self.assertIn(
                'localhost',
                self.env._drivers[
                    'tests.drivers.Provider'
                ].destroy.call_args[0][0])
