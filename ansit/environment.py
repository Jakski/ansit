import logging
import sys
import collections
import importlib
import subprocess
import shutil
import os
import json
from copy import deepcopy
from pprint import pformat
from collections import defaultdict

import jinja2
import yaml

from ansit.util import (
    read_yaml_file,
    update,
    get_element_by_path)
from ansit import drivers


logger = logging.getLogger(__name__)


class DriverError(Exception):
    pass


class Drivers(collections.abc.Mapping):
    '''Repository for drivers.'''

    def __init__(self, manifest, state_filename='drivers.json'):
        self._drivers = {}
        self._manifest = manifest
        state_dir = os.path.join(
            self._manifest['tmp_dir'],
            os.path.basename(self._manifest['tmp_dir']))
        os.makedirs(state_dir, exist_ok=True)
        self._state_file = os.path.join(state_dir, state_filename)
        self._state = defaultdict(dict)
        try:
            os.stat(self._state_file)
            with open(self._state_file, 'r', encoding='utf-8') as state_src:
                self._state.update(json.load(state_src))
        except FileNotFoundError:
            pass

    def __getitem__(self, key):
        if key not in self._drivers:
            path = '.'.join(key.split('.')[:-1])
            class_name = key.split('.')[-1]
            module = importlib.import_module(path)
            driver = getattr(module, class_name)
            config = deepcopy(self._manifest['drivers']['config'].get(key, {}))
            if issubclass(driver, drivers.Provider):
                machines = {}
                for machine_name, machine in \
                        self._manifest['machines'].items():
                    if machine['driver'] == key:
                        machines[machine_name] = deepcopy(machine)
                self._drivers[key] = driver(
                    self._manifest['directory'], machines, config)
            elif issubclass(driver, drivers.Tester):
                self._drivers[key] = driver(self._manifest['directory'],
                    config)
            elif issubclass(driver, drivers.Provisioner):
                self._drivers[key] = driver(
                    self._manifest['directory'],
                    self.providers, config)
            else:
                raise DriverError(
                    'Class %s(%s) is not instance of any known driver' % (
                        type(driver),
                        key))
            self._drivers[key].state = self._state[key]
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

    def save_state(self):
        '''Save state of drivers to persistent storage.'''
        for path, driver in self._drivers.items():
            self._state[path] = driver.state
        with open(self._state_file, 'w', encoding='utf-8') as state_dest:
            json.dump(self._state, state_dest, sort_keys=True, indent=4)


class EnvironmentError(Exception):
    pass


class Environment:

    def __init__(self, manifest, verbose=False):
        if not os.path.isdir(manifest['tmp_dir']):
            os.mkdir(manifest['tmp_dir'])
        self._manifest = manifest
        self._verbose = verbose
        self._drivers = Drivers(self._manifest)
        rsync = shutil.which('rsync')
        if rsync is None:
            raise EnvironmentError('Couldn\'t find rsync')
        self._cmd = [
            rsync,
            '-avh',
            '--delete',
            '--links',
            self._manifest['directory'] + '/',
            self._manifest['tmp_dir']
        ]
        for exclude in self._manifest['excludes']:
            self._cmd.append('--exclude=%s' % (exclude))
        self._templates = jinja2.Environment(
            loader=jinja2.FileSystemLoader(
                os.path.abspath(self._manifest['directory'])),
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True)
        # Preload providers
        try:
            for machine in self._manifest['machines'].values():
                self._drivers[machine['driver']]
        except Exception as e:
            raise EnvironmentError('Failed to load providers') from e

    def save_state(self):
        self._drivers.save_state()

    def synchronize(self):
        '''Synchronize project catalog.'''
        logger.debug('Synchronizing environment...')
        try:
            subprocess.run(self._cmd,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        except subprocess.SubprocessError as e:
            raise EnvironmentError('Failed to synchronize') from e

    def apply_changes(self):
        '''Apply changes to environment.'''
        logger.debug('Applying changes to environment...')
        for change in self._manifest.get('changes', []):
            changetype = list(change.keys())[0]
            change = change[changetype]
            try:
                getattr(self, '_apply_' + changetype)(change)
            except:
                raise EnvironmentError('Failed to apply change: %s' % (
                    pformat(change))) from sys.exc_info()[1]

    def run(self, machine, cmd):
        provider, _ = list(self._get_matching_providers([machine]))[0]
        for line in provider.run(machine, cmd):
            logger.info(line.rstrip())

    def up(self, machines=[]):
        for match in self._get_matching_providers(machines):
            provider, machines = match
            logger.info('Bringing up machines: %s' % (pformat(machines)))
            try:
                for line in provider.up(machines):
                    logger.info('    ' + line.rstrip())
            except Exception as e:
                raise EnvironmentError(
                    'Failed to bring up machines %s with provider: %s' % (
                        pformat(machines),
                        provider.__module__ + '.'
                        + provider.__class__.__name__)) from e

    def destroy(self, machines=[]):
        for match in self._get_matching_providers(machines):
            provider, machines = match
            logger.info('Destroying machines: %s' % (pformat(machines)))
            for line in provider.destroy(machines):
                logger.info('    ' + line.rstrip())

    def provision(self):
        '''Run all provisioners on environment.'''
        logger.info('Provisioning environment...')
        for cfg in self._manifest['provision']:
            provisioner = self._drivers[cfg['driver']]
            for line in provisioner.provision(cfg):
                logger.info('    ' + line.rstrip())

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
                    logger.debug('Failed test: %s' % (test['name']))
                    results.append((test['name'], False))
                else:
                    results.append((test['name'], True))
            summary[machine_name] = results
        return summary

    def login(self, machine):
        '''Login interactively via remote console to machine.

        :param str machine: machine name'''
        try:
            provider = next(self._get_matching_providers([machine]))[0]
        except StopIteration:
            raise EnvironmentError(
                'Machine \'%s\' not found in any provider' % (machine))
        cfg = provider.ssh_config(machine)
        ssh = shutil.which('ssh')
        if ssh is None:
            raise EnvironmentError('ssh executable not found')
        logger.info('Logging to machine: %s' % (machine))
        subprocess.run(
            [
                ssh,
                '%s@%s' % (cfg['user'], cfg['address']),
                '-p', str(cfg['port']),
                '-i', cfg['private_key'],
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null'
            ],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr)

    def _run_test(self, machine, test):
        logger.info('Running test \'%s\' on machine: %s...' % (
            test['name'], machine))
        provider = self._drivers[self._manifest['machines'][machine]['driver']]
        tester = self._drivers[test['driver']]
        try:
            for line in tester.test(machine, provider, test):
                logger.info('    ' + line.rstrip())
        except Exception as e:
            logger.error('Failed to run test \'%s\' on machine: %s' % (
                test['name'], machine), exc_info=1)
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
            # jinja2.FileSystemLoader don't accept not normalized path
            src = os.path.abspath(change['src'])[
                len(os.path.commonpath([
                        os.path.abspath(change['src']),
                        os.path.abspath(self._manifest['directory'])])
                    ) + 1:]
            dest.write(self._templates.get_template(
                src).render(env))
