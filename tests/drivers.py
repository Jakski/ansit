from ansit import drivers


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
