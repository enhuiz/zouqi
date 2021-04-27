import inspect
import argparse
from functools import partial

from .parsing import ignored, flag, custom
from .utils import print_args


def parse_params(f, predicate=lambda _: True):
    params = inspect.signature(f).parameters.values()
    params = [p for p in params if predicate(p)]
    return params


def inherit_signature(f, bases):
    """
    inherit signature
    """
    if isinstance(bases, type):
        bases = [bases]

    POSITIONAL_ONLY = inspect.Parameter.POSITIONAL_ONLY
    POSITIONAL_OR_KEYWORD = inspect.Parameter.POSITIONAL_OR_KEYWORD
    VAR_POSITIONAL = inspect.Parameter.VAR_POSITIONAL
    KEYWORD_ONLY = inspect.Parameter.KEYWORD_ONLY
    VAR_KEYWORD = inspect.Parameter.VAR_KEYWORD

    def merge(fps, gps):
        if any([p.kind in [VAR_KEYWORD, VAR_POSITIONAL] for p in gps]):
            raise TypeError("Parent class contains uncertain parameters.")

        indices = {}
        params = []

        def add(p):
            indices[p.name] = len(params)
            params.append(p)

        i, j = 0, 0
        while i < len(fps):
            fp = fps[i]
            if fp.kind is VAR_POSITIONAL:
                # replace the var positional with parent's PO and P/W
                while j < len(gps):
                    gp = gps[j]
                    if gp.name not in indices and gp.kind in [
                        POSITIONAL_ONLY,
                        POSITIONAL_OR_KEYWORD,
                    ]:
                        add(gp)
                    j += 1
            elif fp.kind is VAR_KEYWORD:
                # replace the var positional with parent's PO and P/W
                while j < len(gps):
                    gp = gps[j]
                    if gp.name not in indices and gp.kind in [
                        POSITIONAL_OR_KEYWORD,
                        KEYWORD_ONLY,
                    ]:
                        add(gp)
                    j += 1
            elif fp.name in indices:
                # override
                del params[indices[fp.name]]
                add(fp)
            else:
                add(fp)

            i += 1

        return params

    def recursively_inherit_signature(f, cls):
        if cls is object:
            return

        g = getattr(cls, f.__name__, None)

        if g is not None:
            if cls.__bases__:
                for base in cls.__bases__:
                    recursively_inherit_signature(g, base)
            params = merge(parse_params(f), parse_params(g))
            f.__signature__ = inspect.Signature(params)

    for base in bases:
        recursively_inherit_signature(f, base)

    return f


def normalize_option_name(name):
    """Use '-' as default instead of '_' for option as it is easier to type."""
    if name.startswith("--"):
        name = name.replace("_", "-")
    return name


def add_arguments_from_function_signature(parser, f):
    empty = inspect.Parameter.empty
    params = parse_params(f, lambda p: p.name != "self")
    existed = {a.dest for a in parser._actions}

    for p in params:
        if p.name in existed:
            raise TypeError(f"{p.name} conflicts with exsiting argument.")

        if p.annotation is ignored:
            if p.default is empty:
                raise TypeError(
                    f"An argument {p.name} cannot be ignored, "
                    "please set an default value to make it an option."
                )
            else:
                continue

        if p.default is not empty or p.annotation is flag:
            name = normalize_option_name(f"--{p.name}")
        else:
            name = p.name

        default = None if p.default is empty else p.default

        kwargs = dict(default=default)

        if p.annotation is flag:
            default = False if default is None else default
            kwargs.update(dict(default=default, action="store_true"))
        elif type(p.annotation) is custom:
            kwargs.update(**p.annotation)
        elif p.annotation is not empty:
            kwargs.update(dict(type=p.annotation))

        parser.add_argument(name, **kwargs)


def command(f=None, inherit=True):
    if f is not None:
        f._command = dict(inherit=inherit)
        return f
    return partial(command, inherit=inherit)


def start(cls):
    # extract possible commands
    command_names = []
    for name, func in inspect.getmembers(cls, inspect.isfunction):
        if hasattr(func, "_command"):
            command_names.append(name)
            # inherit the command
            if func._command["inherit"]:
                inherit_signature(func, cls.__bases__)

    # inherit __init__
    inherit_signature(cls.__init__, cls.__bases__)

    # initalize parser for the cls
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers = {name: subparsers.add_parser(name) for name in command_names}

    for subparser in subparsers.values():
        add_arguments_from_function_signature(subparser, cls.__init__)
        subparser.add_argument("--print-args", action="store_true")

    for name in command_names:
        add_arguments_from_function_signature(subparsers[name], getattr(cls, name))

    args = parser.parse_args()

    if args.print_args:
        print_args(args)

    params = {p.name for p in parse_params(cls.__init__)}
    obj = cls(**{key: value for key, value in vars(args).items() if key in params})

    command_func = getattr(obj, args.command)
    params = {p.name for p in parse_params(command_func)}
    command_func(**{key: value for key, value in vars(args).items() if key in params})
