import inspect
import argparse
import functools


def command(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        parameters = inspect.signature(f).parameters.values()
        parameters = [p for p in parameters if p.name != "self"]

        if kwargs.get("call_as_command", False):
            # call from cli, a main command
            # use cli parameters to update args
            assert len(args) == 0

            del kwargs["call_as_command"]

            empty = inspect.Parameter.empty

            for p in parameters:
                # does not resolve command's parameters conflicts
                if hasattr(self.args, p.name):
                    raise argparse.ArgumentError(
                        f"{p.name} conflicts with exsiting args."
                    )

                # use annotation as type, a little bit abuse
                if p.annotation is empty:
                    parser = None
                else:
                    parser = p.annotation

                if p.default is empty:
                    self.add_argument(f"{p.name}", type=parser)
                else:
                    self.add_argument(f"--{p.name}", type=parser, default=p.default)

            self.parse_args(strict=True)

            for p in parameters:
                kwargs[p.name] = getattr(self.args, p.name)
                delattr(self.args, p.name)

            wrapped.args = argparse.Namespace(**kwargs)

            if self.print_final_args:
                print(self.args)
                print(wrapped.args)
        else:
            # call from other function, a minion command
            # use passed parameters to update args
            for p, a in zip(parameters, args):
                kwargs[p.name] = a

            kwargs = {
                p.name: kwargs[p.name] if p.name in kwargs else p.default
                for p in parameters
            }

            wrapped.args = argparse.Namespace(**kwargs)

        return f(self, **kwargs)

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
        self.parse_args()

    @property
    def parser(self):
        if not hasattr(self, "_Runner__parser"):
            self.__parser = argparse.ArgumentParser(conflict_handler="resolve")
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

    def parse_args(self, strict=False):
        if strict:
            self.args = self.parser.parse_args()
        else:
            self.args = self.parser.parse_known_args()[0]
        self.command = self.args.command

    def update_args(self, args):
        self.args = argparse.Namespace(**vars(self.args), **vars(args))

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
