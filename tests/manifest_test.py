from os import path, getcwd
from unittest import TestCase

from ansit.manifest import Manifest


class TestManifest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path = path.join(getcwd(), 'tests')

    def test_lel(self):
        self.assertTrue(True)
