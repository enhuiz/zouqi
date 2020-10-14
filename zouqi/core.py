import inspect
import argparse
from functools import partial

from .parsing import ignored, flag
from .utils import print_args


def read_params(f, predicate=lambda p: True):
    params = inspect.signature(f).parameters.values()
    params = [p for p in params if predicate(p)]
    return params


def inherit_signature(f, bases):
    """
    inherit signature
    """
    if isinstance(bases, type):
        bases = [bases]

    empty = inspect.Parameter.empty

    def merge(f_params, g_params):
        i = -1
        for i, p in enumerate(g_params):
            if p.default is not empty:
                i -= 1
                break
        for p in f_params:
            if p.default is empty:
                g_params.insert(i + 1, p)
            else:
                g_params.append(p)
        return g_params

    def not_var(p):
        return p.kind not in [p.VAR_POSITIONAL, p.VAR_KEYWORD]

    def recursively_inherit_signature(f, cls):
        if cls.__bases__:
            for base in cls.__bases__:
                recursively_inherit_signature(f, base)

        g = getattr(cls, f.__name__, None)

        if g is not None:
            f_params = read_params(f, lambda p: not_var(p) and p.name is not "self")
            existed = [p.name for p in f_params]
            g_params = read_params(g, lambda p: not_var(p) and p.name not in existed)
            params = merge(f_params, g_params)
            f.__signature__ = inspect.Signature(params)

    for base in bases:
        recursively_inherit_signature(f, base)

    return f


def normalize_argument_name(name):
    """Use '-' as default instead of '_' for option as it is easier to type."""
    if name.startswith("--"):
        name = name.replace("_", "-")
    return name


def add_arguments_from_function_signature(parser, f):
    empty = inspect.Parameter.empty
    params = read_params(f, lambda p: p.name is not "self")
    existed = {a.dest for a in parser._actions}

    for p in params:
        if p.name in existed:
            raise TypeError(f"{p.name} conflicts with exsiting argument.")

        annotation = None if p.annotation is empty else p.annotation

        if annotation is ignored:
            if p.default is empty:
                raise TypeError(
                    f"An argument {p.name} cannot be ignored, please set an default value to make it an option."
                )
        else:
            name = normalize_argument_name(p.name)
            if annotation is flag:
                if p.default is empty:
                    p.default = False
                parser.add_argument(f"--{name}", action="store_true", default=p.default)
            elif p.default is empty:
                parser.add_argument(name, type=annotation)
            else:
                parser.add_argument(f"--{name}", type=annotation, default=p.default)


def command(f=None, inherit=None):
    if f is not None:
        f._command = dict(inherit=inherit)
        return f
    return partial(command, inherit=inherit)


def call(f, **kwargs):
    """Call with needed kwargs"""
    params = read_params(f)
    names = [p.name for p in params]
    kwargs = {k: v for k, v in kwargs.items() if k in names}
    return f(**kwargs)


def start(cls, default_command=None):
    # extract possible commands
    possible_commands = []
    for command, func in inspect.getmembers(cls, inspect.isfunction):
        if hasattr(func, "_command"):
            possible_commands.append(command)
            if func._command["inherit"]:
                inherit_signature(func, cls.__bases__)

    if default_command is not None and default_command not in possible_commands:
        raise ValueError(
            f'The given default command "{default_command}" is not a command!'
        )

    # force to inherit for __init__
    inherit_signature(cls.__init__, cls.__bases__)

    # initalize parser for the cls
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        type=str,
        nargs="?" if default_command else 1,
        choices=possible_commands,
        default=default_command,
    )
    parser.add_argument("--print-args", action="store_true")
    add_arguments_from_function_signature(parser, cls.__init__)
    args = parser.parse_known_args()[0]
    args.command = args.command[0]

    command_func = getattr(cls, args.command)
    add_arguments_from_function_signature(parser, command_func)
    command_args = parser.parse_args()

    for key in vars(args):
        try:
            delattr(command_args, key)
        except:
            pass

    if args.print_args:
        print_args(args, command_args)

    obj = call(cls, **vars(args))
    call(command_func, self=obj, **vars(command_args))
