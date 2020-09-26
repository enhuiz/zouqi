import inspect
import argparse


def command(f):
    f.registered_as_command = True
    return f


def possible_commands(obj):
    commands = []
    for name in dir(obj):
        try:
            f = getattr(obj, name)
        except:
            # could be a property
            continue
        if getattr(f, "registered_as_command", False):
            commands.append(name)
    return commands


class Runner:
    def __init__(self):
        self.update_args(strict=False)

    @property
    def parser(self):
        if not hasattr(self, "_Runner__parser"):
            self.__parser = argparse.ArgumentParser()
            self.add_argument("command", choices=possible_commands(self))
        return self.__parser

    def add_argument(self, name, **kwargs):
        """
        Add argument, only the first added argument will be recorded.
        """
        name = name.replace("_", "-")
        try:
            self.parser.add_argument(name, **kwargs)
        except argparse.ArgumentError as e:
            if "conflicting option string" not in str(e):
                raise e

    def update_args(self, strict=True):
        if strict:
            self.args = self.parser.parse_args()
        else:
            self.args = self.parser.parse_known_args()[0]
        self.command = self.args.command

    def run(self):
        getattr(self, self.command)()
