import collections
import json

import yaml


def read_json_file(path):
    with open(path, 'r', encoding='utf-8') as src:
        return json.load(src)

def read_yaml_file(path):
    with open(path, 'r', encoding='utf-8') as src:
        return yaml.load(src)

def update(d, u):
    '''Recursive dictionary update.'''
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def get_element_by_path(structure, path):
    '''Retrive element from structure with index keys path.'''
    for i in path:
        structure = structure[i]
    return structure
