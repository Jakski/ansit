from ansit import drivers


class Provider(drivers.Provider):

    def __init__(self, directory, machines):
        pass

    def up(self, machines):
        pass

    def run(self, machine, cmd):
        pass

    @property
    def exit_code(self):
        pass

    def ssh_config(self):
        pass

    def destroy(self, machines):
        pass

    @property
    def machines(self):
        pass

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