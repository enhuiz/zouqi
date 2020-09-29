import inspect
import argparse
import functools

from .parsing import ignored
from .utils import print_args


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


def inherit_signature(f, g):
    """
    Args:
        f: dervied member function
        g: base member function
    """
    f_params = inspect.signature(f).parameters.values()
    f_params = [p for p in f_params if p.name not in ["args", "kwargs"]]
    names = set([p.name for p in f_params])
    g_params = inspect.signature(g).parameters.values()
    g_params = [p for p in g_params if p.name not in names]

    for i, p in enumerate(f_params):
        if p.kind != p.POSITIONAL_OR_KEYWORD:
            i -= 1
            break

    for p in g_params:
        if p.kind == p.POSITIONAL_OR_KEYWORD:
            f_params.insert(i + 1, p)
        else:
            f_params.append(p)

    f.__signature__ = inspect.Signature(f_params)

    return f


class command:
    def __init__(self, f):
        self.f = f

    def __set_name__(self, owner, name):
        f = self.f

        parent = getattr(super(owner, owner), name, None)
        if parent is not None:
            inherit_signature(f, parent)

        @functools.wraps(f)
        def wrapped(self, *args, **kwargs):
            if kwargs.get("_call_as_command", False):
                assert len(args) == 0 and len(kwargs) == 1
                wrapped.args = parse_args_from_cli(f, self)
                if self.verbose:
                    print_args(self.args, wrapped.args)
            else:
                wrapped.args = parse_args_from_call(f, self, *args, **kwargs)
            return f(self, **vars(wrapped.args))

        wrapped.is_command = True

        setattr(owner, name, wrapped)


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
    def __init__(self, prevented_arguments=[], verbose=False):
        prevented_arguments = map(self.normalize_argument, prevented_arguments)
        self.prevented_arguments = list(prevented_arguments)
        self.verbose = verbose

    @property
    def parser(self):
        if not hasattr(self, "_Runner__parser"):
            self.__parser = argparse.ArgumentParser(conflict_handler="resolve")
            self.add_argument("command", choices=possible_commands(self))
        return self.__parser

    @staticmethod
    def normalize_argument(name):
        """
        Use '-' as default instead of '_' for option as it is easier to type.
        """
        if name.startswith("--"):
            name = name.replace("_", "-")
        return name

    def add_argument(self, name, **kwargs):
        """
        Add argument, only the first added argument will be recorded.
        """
        name = self.normalize_argument(name)
        if name not in self.prevented_arguments:
            self.parser.add_argument(name, **kwargs)

    def parse_args(self, strict=False):
        if strict:
            self.args = self.parser.parse_args()
        else:
            self.args = self.parser.parse_known_args()[0]
        self.command = self.args.command
        return self.args

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
