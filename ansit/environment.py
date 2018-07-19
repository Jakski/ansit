import logging
import collections
import importlib
import subprocess
import shutil
import os
from copy import deepcopy
from pprint import pformat

import jinja2
import yaml

from ansit.util import (
    read_yaml_file,
    get_element_by_path)
from ansit import drivers

logger = logging.getLogger(__name__)


class DriverError(Exception):
    pass


class Drivers(collections.abc.Mapping):
    '''Repository for drivers.'''

    def __init__(self, manifest):
        self._drivers = {}
        self._manifest = manifest

    def __getitem__(self, key):
        if key not in self._drivers:
            path = '.'.join(key.split('.')[:-1])
            class_name = key.split('.')[-1]
            module = importlib.import_module(path)
            driver = getattr(module, class_name)
            if issubclass(driver, drivers.Provider):
                machines = {}
                for machine_name, machine in \
                    self._manifest['machines'].items():
                    if machine['driver'] == key:
                        machines[machine_name] = deepcopy(machine)
                self._drivers[key] = driver(
                    self._manifest['directory'], machines)
            elif issubclass(driver, drivers.Tester):
                self._drivers[key] = driver(self._manifest['directory'])
            elif issubclass(driver, drivers.Provisioner):
                self._drivers[key] = driver(
                    self._manifest['directory'],
                    self.providers)
            else:
                raise DriverError(
                    'Class %s(%s) is not instance of any known driver' % (
                        type(driver),
                        key))
        return self._drivers[key]

    def __iter__(self):
        return iter(self._drivers)

    def __len__(self):
        return len(self._drivers)

    @property
    def providers(self):
        '''
        :return: all currently loaded providers
        :rtype: list'''
        return [d for d in self._drivers.values()
                if isinstance(d, drivers.Provider)]


class EnvironmentError(Exception):
    pass


class Environment:

    def __init__(self, manifest):
        if not os.path.isdir(manifest['tmp_dir']):
            os.mkdir(manifest['tmp_dir'])
        self._manifest = manifest
        self._drivers = Drivers(self._manifest)
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
        # Preload providers
        try:
            for machine in self._manifest['machines'].values():
                self._drivers[machine['driver']]
        except Exception as e:
            raise EnvironmentError('Failed to load providers') from e

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

    def run(self, machine, cmd):
        provider, _ = list(self._get_matching_providers([machine]))[0]
        for line in provider.run(machine, cmd):
            logger.info(line)

    def up(self, machines=[]):
        for match in self._get_matching_providers(machines):
            provider, machines = match
            for line in provider.up(machines):
                logger.info(line)

    def destroy(self, machines=[]):
        for match in self._get_matching_providers(machines):
            provider, machines = match
            for line in provider.destroy(machines):
                logger.info(line)

    def test(self, machines=[]):
        '''Run tests on machines

        :return: tests run summary
        :rtype: dict'''
        summary = {}
        if len(machines) == 0:
            machines = list(self._manifest['machines'].keys())
        for machine_name in machines:
            results = []
            machine = self._manifest['machines'][machine_name]
            for test in machine.get('tests', []):
                if not self._run_test(machine_name, test):
                    logging.info('Failed test: %s' % (test['name']))
                    results.append((test['name'], False))
                else:
                    results.append((test['name'], True))
            summary[machine_name] = results
        return summary

    def _run_test(self, machine, test):
        provider = self._drivers[self._manifest['machines'][machine]['driver']]
        tester = self._drivers[test['driver']]
        for line in tester.test(machine, provider, test):
            logger.info(line)
        return tester.status

    def _get_matching_providers(self, machines):
        if len(machines) == 0:
            machines = list(self._manifest['machines'].keys())
        for match in drivers.get_matching_providers(
            machines, self._drivers.providers):
            yield match

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

    @property
    def _ssh_configs(self):
        r = {}
        for name, machine in self._manifest['machines'].items():
            r[name] = self._drivers[machine['driver']].ssh_config(name)
        return r

    def _apply_template(self, change):
        with open(change['dest'], 'w') as dest:
            env = {'machines': self._ssh_configs}
            env.update(change.get('vars', {}))
            dest.write(self._templates.get_template(
                change['src']).render(env))
