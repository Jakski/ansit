import logging
import subprocess
import shutil
import os
from pprint import pformat

import jinja2
import yaml

from ansit.util import (
    read_yaml_file,
    get_element_by_path)


logger = logging.getLogger(__name__)


class Drivers:
    '''Repository for drivers.'''
    pass


class EnvironmentError(Exception):
    pass


class Environment:

    def __init__(self, manifest):
        if not os.path.isdir(manifest['tmp_dir']):
            os.mkdir(manifest['tmp_dir'])
        self._manifest = manifest
        rsync = shutil.which('rsync')
        if rsync is None:
            raise EnvironmentError('Couldn\'t find rsync')
        self._cmd = [
            rsync,
            '-avh',
            '--delete',
            self._manifest['directory'] + '/',
            self._manifest['tmp_dir']
        ]
        for exclude in self._manifest['excludes']:
            self._cmd.append('--exclude=%s' % (exclude))
        self._templates = jinja2.Environment(
            loader=jinja2.FileSystemLoader('.'),
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True)

    def synchronize(self):
        '''Synchronize project catalog.'''
        try:
            subprocess.run(self._cmd,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        except subprocess.SubprocessError as e:
            raise EnvironmentError('Failed to synchronize') from e

    def apply_changes(self):
        '''Apply changes to environment.'''
        for change in self._manifest.get('changes', []):
            changetype = list(change.keys())[0]
            change = change[changetype]
            try:
                getattr(self, '_apply_' + changetype)(change)
            except Exception as e:
                logging.error(str(e))
                raise EnvironmentError('Failed to apply change: %s' % (
                    pformat(change)))

    def _apply_update(self, change):
        content = read_yaml_file(change['dest'])
        parent = get_element_by_path(content, change['path'][:-1])
        parent[change['path'][-1]] = change['value']
        with open(change['dest'], 'w', encoding='utf-8') as dest:
            yaml.dump(content, stream=dest)

    def _apply_remove(self, change):
        content = read_yaml_file(change['dest'])
        parent = get_element_by_path(content, change['path'][:-1])
        del parent[change['path'][-1]]
        with open(change['dest'], 'w', encoding='utf-8') as dest:
            yaml.dump(content, stream=dest)

    def _apply_copy(self, change):
        shutil.copy2(change['src'], change['dest'])

    def _apply_add(self, change):
        content = read_yaml_file(change['dest'])
        parent = get_element_by_path(content, change['path'][:-1])
        parent[change['path'][-1]].append(change['value'])
        with open(change['dest'], 'w', encoding='utf-8') as dest:
            yaml.dump(content, stream=dest)

    def _apply_template(self, change):
        with open(change['dest'], 'w') as dest:
            # TODO: pass environment variables to changes
            dest.write(self._templates.get_template(change['src']).render(change.get('vars', {})))
