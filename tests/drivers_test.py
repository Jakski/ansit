import logging
import os
import getpass
from unittest import (
    TestCase,
    mock)

from ansit import drivers


logging.basicConfig(level=logging.CRITICAL)


class TestLocalhostProvider(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.provider = drivers.LocalhostProvider(
            '.', {
                'localhost': {
                    'driver': 'ansit.drivers.LocalhostProvider',
                    'ssh_port': 22,
                    'ssh_private_key': 'id_rsa',
                }
            })

    def test_config(self):
        self.assertEqual(
            self.provider.ssh_config('localhost'),
            {
                'address': 'localhost',
                'user': getpass.getuser(),
                'port': 22,
                'private_key': 'id_rsa'
            })

    def test_run(self):
        output = list(self.provider.run('localhost', 'pwd'))
        self.assertEqual(
            output[0],
            os.getcwd() + '\n')

class TestCommandTester(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tester = drivers.CommandTester('.')

    @mock.patch('ansit.drivers.LocalhostProvider',
                autospec=True,
                instance=True)
    def test_failed_test(self, mock_provider):
        test = {'cmd': 'some_command'}
        mock_provider.run = mock.Mock(
            side_effect=drivers.ProviderError(''))
        list(self.tester.test('localhost', mock_provider, test))
        self.assertEqual(mock_provider.run.call_count, 1)
        self.assertEqual(
            mock_provider.run.call_args[0][1],
            test['cmd'])
        self.assertFalse(self.tester.status)

    @mock.patch('ansit.drivers.LocalhostProvider',
                autospec=True,
                instance=True)
    def test_passed_test(self, mock_provider):
        def mock_provider_run(machine, cmd):
            yield ''
        test = {'cmd': 'some_command'}
        mock_provider.run = mock.Mock(side_effect=mock_provider_run)
        list(self.tester.test('localhost', mock_provider, test))
        self.assertEqual(mock_provider.run.call_count, 1)
        self.assertEqual(
            mock_provider.run.call_args[0][1],
            test['cmd'])
        self.assertTrue(self.tester.status)
