import logging
import sys
import os
import shutil
import hashlib
import json
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
        os.mkdir(cls.drivers._manifest['tmp_dir'])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.drivers._manifest['tmp_dir'])

    def test_loading_provider(self):
        self.assertTrue(isinstance(
            self.drivers['ansit.drivers.LocalhostProvider'],
            drivers.Provider))

    def test_loading_provisioner(self):
        self.assertTrue(isinstance(
            self.drivers['ansit.drivers.CommandProvisioner'],
            drivers.Provisioner))

    def test_loading_tester(self):
        self.assertTrue(isinstance(
            self.drivers['ansit.drivers.CommandTester'],
            drivers.Tester))

    def test_saving_state(self):
        # ensure loading CommandTester is loaded
        self.drivers['ansit.drivers.CommandTester']
        self.drivers.save_state()
        state_file = os.path.join(
            self.drivers._manifest['tmp_dir'],
            os.path.basename(self.drivers._manifest['tmp_dir']),
            self.drivers.STATE_FILE)
        with open(state_file, 'r', encoding='utf-8') as state_src:
            state = json.load(state_src)
        self.assertDictEqual(
            state['drivers']['ansit.drivers.CommandTester'],
            {})


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
            self.md5sum('tests/examples/rendered_template.txt'),
            self.md5sum('.ansit/examples/template.txt'))

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

    @mock.patch('ansit.drivers.LocalhostProvider.up')
    def test_creating_machines(self, up):
        def mock_up(*args, **kwargs):
            yield ''
        up.side_effect = mock_up
        self.env.up(['localhost'])
        self.assertEqual(up.call_count, 1)
        self.assertIn('localhost', up.call_args[0][0])

    @mock.patch('ansit.drivers.LocalhostProvider.destroy')
    def test_destroying_machines(self, destroy):
        def mock_destroy(*args, **kwargs):
            yield ''
        destroy.side_effect = mock_destroy
        self.env.destroy(['localhost'])
        self.assertEqual(destroy.call_count, 1)
        self.assertIn('localhost', destroy.call_args[0][0])

    @mock.patch('ansit.drivers.LocalhostProvider.run')
    def test_run_command(self, run):
        def mock_run(*args, **kwargs):
            yield ''
        run.side_effect = mock_run
        self.env.run('localhost', 'pwd')
        self.assertEqual(run.call_count, 1)

    @mock.patch('ansit.drivers.CommandTester.status',
                new_callable=mock.PropertyMock)
    @mock.patch('ansit.drivers.CommandTester.test')
    def test_passed_tests(self, test_run, test_status):
        def mock_test_run(*args, **kwargs):
            yield ''
        test_run.side_effect = mock_test_run
        test_status.return_value = True
        summary = self.env.test(['localhost'])
        self.assertEqual(test_run.call_count, 2)
        self.assertEqual(test_status.call_count, 2)
        self.assertEqual(
            summary,
            {
                'localhost': [
                    ('Test 1', True),
                    ('Test 2', True)
                ]
            })

    @mock.patch('ansit.drivers.CommandTester.status',
                new_callable=mock.PropertyMock)
    @mock.patch('ansit.drivers.CommandTester.test')
    def test_passed_tests(self, test_run, test_status):
        def mock_test_run(*args, **kwargs):
            yield ''
        test_run.side_effect = mock_test_run
        test_status.return_value = False
        summary = self.env.test(['localhost'])
        self.assertEqual(test_run.call_count, 2)
        self.assertEqual(test_status.call_count, 2)
        self.assertEqual(
            summary,
            {
                'localhost': [
                    ('Test 1', False),
                    ('Test 2', False)
                ]
            })

    @mock.patch('subprocess.run')
    def test_loging(self, subprocess_run):
        self.env.login('localhost')
        self.assertEqual(subprocess_run.call_count, 1)
        self.assertIn(
            'id_rsa',
            subprocess_run.call_args[0][0])
        self.assertEqual(sys.stdin.fileno(),
                      subprocess_run.call_args[1]['stdin'].fileno())
        self.assertEqual(sys.stdout.fileno(),
                      subprocess_run.call_args[1]['stdout'].fileno())
        self.assertEqual(sys.stderr.fileno(),
                      subprocess_run.call_args[1]['stderr'].fileno())

    @mock.patch('ansit.drivers.CommandProvisioner.provision')
    def test_provision(self, provision):
        self.env.provision()
        self.assertEqual(provision.call_count, 1)
