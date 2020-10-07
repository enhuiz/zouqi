import inspect
import argparse
import functools

from .parsing import ignored, flag
from .utils import print_args


def read_parameters(f, ignore=["self"]):
    params = inspect.signature(f).parameters.values()
    params = [p for p in params if p.name not in ignore]
    return params


def read_kwargs_from_cli(f, runner):
    empty = inspect.Parameter.empty
    params = read_parameters(f)

    for p in params:
        if hasattr(runner.args, p.name):
            raise TypeError(f"{p.name} conflicts with exsiting args.")

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

        if annotation is flag:
            if p.default is empty:
                p.default = False
            runner.add_argument(f"--{p.name}", action="store_true", default=p.default)
        elif p.default is empty:
            runner.add_argument(f"{p.name}", type=annotation)
        else:
            runner.add_argument(f"--{p.name}", type=annotation, default=p.default)

    # parse args from cli
    runner.parse_args(strict=True)

    if runner.verbose:
        p_names = {p.name for p in params}
        global_args = {k: v for k, v in vars(runner.args).items() if k not in p_names}
        command_args = {k: v for k, v in vars(runner.args).items() if k in p_names}
        print_args(global_args, command_args)

    return {
        p.name: getattr(
            runner.args,
            p.name,
            p.default,
        )
        for p in params
    }


def read_kwargs_from_call(f, runner, *args, **kwargs):
    """
    Call as function, use passed parameters to update args.
    """
    empty = inspect.Parameter.empty
    params = read_parameters(f)

    # args => kwargs
    for p, a in zip(params, args):
        kwargs[p.name] = a

    # default => kwargs
    for p in params:
        if p.name not in kwargs and p.default != empty:
            kwargs[p.name] = p.default

    # update runner.args
    for p in params:
        if p.annotation != ignored:
            setattr(runner.args, p.name, kwargs.get(p.name, p.default))

    return kwargs


class _Command:
    def __init__(self, f, inherit):
        self.f = f
        self.inherit = inherit

    def _inherit_signature(self, owner, name):
        """
        Args:
            f: dervied member function
            g: base member function
        """
        f = self.f
        g = getattr(super(owner, owner), name, None)

        if g is None:
            raise TypeError(
                f'Cannot inherit method "{name}" from the parent class of "{owner.__name__}".'
            )

        f_params = inspect.signature(f).parameters.values()
        f_params = [p for p in f_params if p.name not in ["args", "kwargs"]]
        p_names = set([p.name for p in f_params])
        g_params = inspect.signature(g).parameters.values()
        g_params = [p for p in g_params if p.name not in p_names]

        for i, p in enumerate(f_params):
            if p.kind is not p.POSITIONAL_OR_KEYWORD:
                i -= 1
                break

        for p in g_params:
            if p.kind == p.POSITIONAL_OR_KEYWORD:
                f_params.insert(i + 1, p)
            else:
                f_params.append(p)

        f.__signature__ = inspect.Signature(f_params)

        self.f = f

    def __set_name__(self, owner, name):
        if self.inherit:
            self._inherit_signature(owner, name)

        f = self.f

        @functools.wraps(f)
        def wrapped(runner, *args, **kwargs):
            if kwargs.get("_call_as_command", False):
                assert len(args) == 0 and len(kwargs) == 1
                kwargs = read_kwargs_from_cli(f, runner)
            else:
                kwargs = read_kwargs_from_call(f, runner, *args, **kwargs)
            return f(runner, **kwargs)

        wrapped.is_command = True

        setattr(owner, name, wrapped)


def command(f=None, inherit=False):
    if f is None:
        return lambda f: _Command(f, inherit)
    return _Command(f, inherit)


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
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.parse_args()

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
        self.parser.add_argument(name, **kwargs)

    def parse_args(self, strict=False):
        if strict:
            self.args = self.parser.parse_args()
        else:
            self.args = self.parser.parse_known_args()[0]
        self.command = self.args.command
        return self.args

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
