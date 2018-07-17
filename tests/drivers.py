from ansit import drivers


class Provider(drivers.Provider):

    def __init__(self, machines, directory):
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

    def machines(self):
        pass

    def destroy(self, machines):
        pass
