from abc import (
    abstractmethod,
    abstractproperty,
    ABCMeta)

from pprint import pformat


class ProviderError(Exception):
    pass


class Provider(metaclass=ABCMeta):
    '''Interface for machines providers.'''

    def __init__(self, machines, directory):
        '''
        :param list machines: machines definitions from manifest
        :param str directory: directory with project'''
        self.machines = machines
        self.directory = directory

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

    @abstractproperty
    def exit_code(self):
        '''Exit code of last command run.'''
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

    @abstractproperty
    def machines(self):
        '''List of machines managed by provider.'''
        return ['machine1', 'machine2', 'machine3']

    @abstractmethod
    def destroy(self, machines):
        '''Destroy machines.

        :param list machines: names of machines to destroy'''
        pass


class TesterError(Exception):
    pass


class Tester(metaclass=ABCMeta):
    '''Interface for test runners.'''

    def __init__(self, test, machine, directory, provider):
        '''
        :param dict test: test definition from manifest
        :param str machine: name of machine
        :param str directory: directory with project
        :param Provider provider: machine provider'''
        self.test = test
        self.directory = directory
        self.provider = provider
        self.machine = machine

    @abstractmethod
    def test(self):
        '''Run test.

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

    def __init__(self, provisioner, directory, providers):
        '''
        :param dict provisioner: provisioner definition from manifest
        :param str directory: directory with project
        :param dict providers: provider instances hashed by their class path'''
        self.provisioner = provisioner
        self.directory = directory
        self.providers = providers

    @abstractmethod
    def provision(self):
        '''Provision environment machines.
        
        :return: message and change status
        :rtype: tuple'''
        pass


class CommandProvisioner(Provisioner):
    '''Shell command provisioner.'''

    def __init__(self, provisioner, directory, provider):
        super().__init__(provision, directory, provider)
        old_provisioner = self.provisioner
        self.provisioner = {'changed_code': None}
        self.provisioner.update(old_provisioner)

    def provision(self):
        target = self.provisioner['machine']
        cmd = self.provisioner['cmd']
        for line in self.providers['target']['driver'].run(target, cmd):
            yield line
        exit_code = self.providers['target']['driver']['exit_code']
        if exitcode == self.provisioner['changed_code']:
            return message, 'changed'
        elif exitcode == 0:
            return message, 'unchanged'
        else:
            raise ProvisionerError(
                'Provisioning command {cmd} returned exit code: {code}'.format(
                    cmd=self.provisioner['cmd'],
                    code=exitcode))
