import json
import logging
from pprint import pprint
from os import path

import yaml
from jsonschema import (
    Draft4Validator,
    ValidationError,
    RefResolver)


logger = logging.getLogger(__name__)


class Manifest:

    def __init__(self, manifest, schema_base=None):
        if schema_base is None:
            schema_base = path.abspath(path.join(__file__, 'schemas'))
        self.schema_base = schema_base
        self.validate(manifest)
        self.manifest = manifest

    def validate(self, schema, document):
        schema_path = path.join(self.schema_base, schema)
        with open(schema_path) as schema_f:
            schema = json.load(schema_f)
        resolver = RefResolver('file://' + schema_path, schema)
        try:
            Draft4Validator(schema, resolver=resolver).validate(document)
        except ValidationError as e:
            logger.error('%s: %s' % (
                e.message,
                pprint(list(e.path))))
            raise

    def __getitem__(self, key):
        return self.manifest[key]

    @classmethod
    def from_file(cls, path, schema_base=None):
        with open(path, encoding='utf-8') as src:
            manifest = yaml.load(src)
        return cls(manifest, schema_base)
