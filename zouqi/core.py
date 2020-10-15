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

    POSITIONAL_ONLY = inspect.Parameter.POSITIONAL_ONLY
    POSITIONAL_OR_KEYWORD = inspect.Parameter.POSITIONAL_OR_KEYWORD
    VAR_POSITIONAL = inspect.Parameter.VAR_POSITIONAL
    KEYWORD_ONLY = inspect.Parameter.KEYWORD_ONLY
    VAR_KEYWORD = inspect.Parameter.VAR_KEYWORD

    empty = inspect.Parameter.empty

    def merge(fps, gps):
        if any([p.kind in [VAR_KEYWORD, VAR_POSITIONAL] for p in gps]):
            raise TypeError("Parent class contains uncertain parameters.")

        names = set()
        params = []

        def add(p):
            names.add(p.name)
            params.append(p)

        i, j = 0, 0
        while i < len(fps):
            fp = fps[i]
            if fp.kind is VAR_POSITIONAL:
                # replace the var positional with parent's PO and P/W
                while j < len(gps):
                    gp = gps[j]
                    if gp.name not in names and gp.kind in [
                        POSITIONAL_ONLY,
                        POSITIONAL_OR_KEYWORD,
                    ]:
                        add(gp)
                    j += 1
            elif fp.kind is VAR_KEYWORD:
                # replace the var positional with parent's PO and P/W
                while j < len(gps):
                    gp = gps[j]
                    if gp.name not in names and gp.kind in [
                        POSITIONAL_OR_KEYWORD,
                        KEYWORD_ONLY,
                    ]:
                        add(gp)
                    j += 1
            elif fp.name not in names:
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
            params = merge(read_params(f), read_params(g))
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
            if annotation is flag:
                parser.add_argument(
                    normalize_option_name(f"--{p.name}"),
                    action="store_true",
                    default=False if p.default is empty else p.default,
                )
            elif p.default is empty:
                parser.add_argument(
                    p.name,
                    type=annotation,
                )
            else:
                parser.add_argument(
                    normalize_option_name(f"--{p.name}"),
                    type=annotation,
                    default=p.default,
                )


def command(f=None, inherit=None):
    if f is not None:
        f._command = dict(inherit=inherit)
        return f
    return partial(command, inherit=inherit)


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

    cmdfn = getattr(cls, args.command)
    add_arguments_from_function_signature(parser, cmdfn)
    command_args = parser.parse_args()

    for key in vars(args):
        try:
            delattr(command_args, key)
        except:
            pass

    if args.print_args:
        print_args(args, command_args)

    acceptees = {p.name for p in read_params(cls.__init__)}
    obj = cls(**{k: v for k, v in vars(args).items() if k in acceptees})

    acceptees = {p.name for p in read_params(cmdfn)}
    cmdfn(obj, **{k: v for k, v in vars(command_args).items() if k in acceptees})
