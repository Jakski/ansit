from ansit import drivers


class FaultyTester(drivers.CommandTester):

    def test(self, machine, provider, test):
        raise Exception('Test error')


class FaultyProvisioner(drivers.CommandProvisioner):

    def provision(self, provision):
        raise Exception('Test error')


class FaultyProvider(drivers.LocalhostProvider):

    def up(self, machines):
        raise Exception('Test error')

    def destroy(self, machines):
        raise Exception('Test error')


class FaultyTester2(drivers.CommandTester):

    def __init__(self, *args, **kwargs):
        raise Exception('Test error')
