import inspect
import argparse
import functools

from .parsing import ignored


def extract_parameters(f, ignore=["self"]):
    params = inspect.signature(f).parameters.values()
    params = [p for p in params if p.name not in ignore]
    return params


def parse_args_from_cli(f, self):
    empty = inspect.Parameter.empty
    params = extract_parameters(f)

    for p in params:
        if hasattr(self.args, p.name):
            raise argparse.ArgumentError(f"{p.name} conflicts with exsiting args.")

        annotation = p.annotation
        if annotation is empty:
            annotation = None
        elif annotation is ignored:
            if p.default is empty:
                raise TypeError(
                    f"An argument {p.name} cannot be ignored, "
                    "please set an default value to make it an option."
                )
            else:
                continue

        if p.default is empty:
            self.add_argument(f"{p.name}", type=annotation)
        else:
            self.add_argument(f"--{p.name}", type=annotation, default=p.default)

    # parse args from cli
    self.parse_args(strict=True)

    kwargs = {p.name: getattr(self.args, p.name, p.default) for p in params}

    # remove parsed args from self.args
    for p in params:
        if p.annotation is not ignored:
            delattr(self.args, p.name)

    return argparse.Namespace(**kwargs)


def parse_args_from_call(f, self, *args, **kwargs):
    """
    Call as function, use passed parameters to update args.
    """
    params = extract_parameters(f)

    # args => kwargs
    for p, a in zip(params, args):
        kwargs[p.name] = a
    del args

    kwargs = {p.name: kwargs.get(p.name, p.default) for p in params}

    return argparse.Namespace(**kwargs)


def command(f):
    @functools.wraps(f)
    def wrapped(self, *args, **kwargs):
        if kwargs.get("_call_as_command", False):
            assert len(args) == 0 and len(kwargs) == 1
            wrapped.args = parse_args_from_cli(f, self)
            if self.print_parsed_args:
                print(self.args)
                print(wrapped.args)
        else:
            wrapped.args = parse_args_from_call(f, self, *args, **kwargs)
        return f(self, **vars(wrapped.args))

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
    def __init__(self, print_parsed_args=False):
        self.print_parsed_args = print_parsed_args
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
        self.args = argparse.Namespace(**{**vars(self.args), **vars(args)})

    def run(self):
        command = getattr(self, self.command)
        command(_call_as_command=True)

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
