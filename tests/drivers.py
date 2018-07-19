from ansit import drivers


class Provider(drivers.Provider):

    def __init__(self, directory, machines):
        self._machines = machines

    def up(self, machines):
        yield ''

    def run(self, machine, cmd):
        pass

    @property
    def exit_code(self):
        pass

    def ssh_config(self):
        pass

    def destroy(self, machines):
        yield ''

    @property
    def machines(self):
        return list(self._machines.keys())

class Tester(drivers.Tester):

    def __init__(self, directory):
        pass

    def test(self, machine, provider):
        pass

    def status(self):
        pass


class Provisioner(drivers.Provisioner):

    def __init__(self, directory, providers):
        pass

    def provision(self, provision):
        pass

    def status(self):
        pass
