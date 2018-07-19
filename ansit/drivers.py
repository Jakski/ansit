import subprocess
import getpass
import shlex
from abc import (
    abstractmethod,
    abstractproperty,
    ABCMeta)

from pprint import pformat


class ProviderError(Exception):
    pass


class Provider(metaclass=ABCMeta):
    '''Interface for machines providers.'''

    def __init__(self, directory, machines):
        '''
        :param dict machines: machines definitions from manifest
        :param str directory: directory with project'''
        self._machines = machines
        self._directory = directory

    @abstractmethod
    def up(self, machines):
        '''Setup machines.

        :param list machines: names of machines to start'''
        pass

    @abstractmethod
    def run(self, machine, cmd):
        '''Run shell command in machine.

        :return: generator yielding each line of output'''
        pass

    @abstractmethod
    def ssh_config(self, machine):
        '''Rertieve SSH access credentials.

        :param machine: machine name
        :return: IP address, user, port, private key
        :rtype: dict'''
        return {
            'address': '10.10.10.10',
            'user': 'vagrant',
            'port': 22,
            'private_key': '/id_rsa'
        }

    @abstractmethod
    def destroy(self, machines):
        '''Destroy machines.

        :param list machines: names of machines to destroy
        :return: generator yielding each line of output'''
        pass

    @property
    def machines(self):
        '''List of machines administered by provider.'''
        return self._machines.keys()


class TesterError(Exception):
    pass


class Tester(metaclass=ABCMeta):
    '''Interface for test runners.'''

    def __init__(self, directory):
        '''
        :param str directory: directory with project'''
        self._directory = directory

    @abstractmethod
    def test(self, machine, provider, test):
        '''Run test.

        :param dict machine: machine definition from manifest
        :param Provider provider: provider instance
        :return: generator yielding test output lines'''
        pass

    @abstractproperty
    def status(self):
        '''Boolean indicating, if test passed or failed.'''
        return True


class ProvisionerError(Exception):
    pass


class Provisioner(metaclass=ABCMeta):
    '''Interface for environment provisioners.'''

    def __init__(self, directory, providers):
        '''
        :param dict provisioner: provisioner definition from manifest
        :param str directory: directory with project
        :param dict providers: provider instances hashed by their class path'''
        self._directory = directory
        self._providers = providers

    @abstractmethod
    def provision(self, provision):
        '''Provision environment machines. Yield provision output
        line by line.'''
        pass

    @abstractproperty
    def status(self):
        '''Return
        - 'failed', if provisioning was unsuccessfull
        - 'changed', if provisioning successfully changed machines
        - 'unchanged', if provisioning was successfull, but didn't
          change anything

        :rtype: str'''
        pass


class LocalhostProvider(Provider):
    '''Bogus provider for using localhost as a machine.'''

    def up(self, machine):
        yield 'Using localhost for machine: %s\n' % (machine)

    def destroy(self, machines):
        yield 'Leaving local machine: %s\n' % (machine)

    def run(self, machine, cmd):
        process = subprocess.Popen(
            shlex.split(cmd),
            bufsize=1,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        for line in process.stdout:
            yield line
        process.communicate()
        if process.returncode != 0:
            raise ProviderError('Command \'%s\' returned code %s' % (
                cmd, str(process.returncode)))

    def ssh_config(self, machine):
        return {
            'address': 'localhost',
            'user': getpass.getuser(),
            'port': self._machines[machine]['ssh_port'],
            'private_key': self._machines[machine]['ssh_private_key']
        }


class LocalhostTester(Tester):
    '''Bogus tester for using localhost.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._status = True

    def test(self, machine, provider, test):
        try:
            for line in provider.run(machine, test['cmd']):
                yield line
        except ProviderError as e:
            self._status = False
        else:
            self._status = True

    @property
    def status(self):
        return self._status
