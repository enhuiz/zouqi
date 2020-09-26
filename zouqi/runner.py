import inspect
import argparse
import functools


def command(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        if kwargs.get("call_as_command", False):
            del kwargs["call_as_command"]
            parameters = inspect.signature(f).parameters.values()
            parameters = [p for p in parameters if p.name != "self"]
            for p in parameters:
                if p.default is inspect.Parameter.empty:
                    self.add_argument(f"{p.name}")
                else:
                    self.add_argument(f"--{p.name}", default=p.default)
            self.update_args()
            for p in parameters:
                kwargs[p.name] = getattr(self.args, p.name)
        return f(self, *args, **kwargs)

    wrapped.is_command = True

    return wrapped


def possible_commands(obj):
    commands = []
    for name in dir(obj):
        try:
            f = getattr(obj, name)
        except:
            # could be a property
            continue
        if getattr(f, "is_command", False):
            commands.append(name)
    return commands


class Runner:
    def __init__(self, print_final_args=False):
        self.print_final_args = print_final_args
        self.update_args(final=False)

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

    def update_args(self, final=True):
        if final:
            self.args = self.parser.parse_args()
            # print when parsing it finally
            if self.print_final_args:
                print(self.args)
        else:
            self.args = self.parser.parse_known_args()[0]
        self.command = self.args.command

    def run(self):
        getattr(self, self.command)(call_as_command=True)

    def autofeed(self, callable, override={}, mapping={}):
        """Priority: 1. override, 2. parsed args 3. parameters' default"""
        parameters = inspect.signature(callable).parameters

        def mapped(key):
            return mapping[key] if key in mapping else key

        def default(key):
            if parameters[key].default is inspect._empty:
                raise RuntimeError(f'No default value is set for "{key}"!')
            return parameters[key].default

        def getval(key):
            if key in override:
                return override[key]
            if hasattr(self.args, mapped(key)):
                return getattr(self.args, mapped(key))
            return default(key)

        return callable(**{key: getval(key) for key in parameters})
