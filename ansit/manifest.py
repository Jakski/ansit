import logging
import collections
import os
from pprint import pformat

from jsonschema import (
    Draft4Validator,
    ValidationError,
    RefResolver)

from ansit.util import (
    read_json_file,
    read_yaml_file,
    update)


logger = logging.getLogger(__name__)


class Manifest(collections.abc.Mapping):

    def __init__(self, manifest,
                 schema_base='schemas', manifest_schema_file='manifest.json'):
        self._schema_base = os.path.join(
            os.path.dirname(__file__),
            schema_base)
        self._manifest_schema_file = manifest_schema_file
        self._manifest_schema = read_json_file(
            os.path.join(
                self._schema_base, self._manifest_schema_file))
        self._manifest = {
            'drivers': {
                'provider': 'ansit.drivers.VagrantProvider',
                'provisioner': 'ansit.drivers.CommandProvisioner',
                'tester': 'ansit.drivers.CommandTester'
            },
            'tmp_dir': '.ansit',
            'excludes': [
                'test',
                'tests',
                '.ansit',
                '.git',
                '.tox'
            ]
        }
        update(self._manifest, manifest)
        self._validate(
            self._manifest,
            self._manifest_schema)
        self._apply_defaults()
        for machine in self['machines'].values():
            self._validate(
                machine,
                self._manifest_schema['definitions']['machine'])
            for test in machine.get('tests', []):
                self._validate(
                    test,
                    self._manifest_schema['definitions']['test'])
        for provisioner in self['provision']:
            self._validate(
                provisioner,
                self._manifest_schema['definitions']['provisioner'])
        self._mangle_paths()

    def __getitem__(self, key):
        return self._manifest[key]

    def __iter__(self):
        return iter(self._manifest)

    def __len__(self):
        return len(self._manifest)

    def _mangle_paths(self):
        '''Join relative paths in change definitions.'''
        for change in self.get('changes', []):
            change = change[list(change.keys())[0]]
            if 'dest' in change:
                change['dest'] = os.path.join(
                    self['tmp_dir'], change['dest'])
            if 'src' in change:
                change['src'] = os.path.join(
                    self['directory'], change['src'])

    def _apply_defaults(self):
        for machine in self['machines'].values():
            if machine.get('driver') is None:
                machine['driver'] = self['drivers']['provider']
            for test in machine.get('tests', []):
                if test.get('driver') is None:
                    test['driver'] = self['drivers']['tester']
        for provisioner in self['provision']:
            if provisioner.get('driver') is None:
                provisioner['driver'] = self['drivers']['provisioner']

    def _validate(self, document, schema):
        resolver = RefResolver(
            'file://' + os.path.join(
                self._schema_base, self._manifest_schema_file),
            document)
        validator = Draft4Validator(schema, resolver=resolver)
        try:
            validator.validate(document)
        except ValidationError as e:
            logger.error('%s: %s' % (pformat(list(e.path)), e.message))
            raise

    @classmethod
    def from_file(cls, path, schema_base='schemas'):
        return cls(read_yaml_file(path),
                   schema_base=schema_base)
