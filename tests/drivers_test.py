import logging
import os
import getpass
from unittest import TestCase

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
