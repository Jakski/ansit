import subprocess
import getpass
import shlex
from abc import (
    abstractmethod,
    abstractproperty,
    ABCMeta)


def get_matching_providers(machines, providers):
    '''Get providers managing machines.

    :return: generator yielding tuples of provides instance and
    machines list'''
    for provider in providers:
        common_machines = list(
            set(provider.machines).intersection(set(machines)))
        if len(common_machines) > 0:
            yield (provider, common_machines)


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
        return list(self._machines.keys())


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


class LocalhostProvider(Provider):
    '''Bogus provider for using localhost as a machine.'''

    def up(self, machines):
        yield 'Using localhost for machines: %s\n' % (machines)

    def destroy(self, machines):
        yield 'Leaving local machine: %s\n' % (machines[0])

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
        machine = self._machines[machine]
        return {
            'address': 'localhost',
            'user': getpass.getuser(),
            'port': machine.get('ssh_port', None),
            'private_key': machine.get('ssh_private_key', None)
        }


class CommandProvisioner(Provisioner):

    def provision(self, provision):
        if provision.get('targets') is None:
            raise ProvisionerError('No targets specified')
        elif provision.get('cmd') is None:
            raise ProvisionerError('No cmd specified')
        for target in provision['targets']:
            provider, _ = list(get_matching_providers(
                [target], self._providers))[0]
            try:
                for line in provider.run(target, provision['cmd']):
                    yield line
            except ProviderError as e:
                raise ProvisionerError(
                    'Failed to provision machine: %s' % (target)) from e


class CommandTester(Tester):
    '''Bogus tester for using localhost.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._status = None

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
        '''Get test status and reset previous one.'''
        old_status = self._status
        self._status = None
        return old_status
