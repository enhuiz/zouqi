import inspect
import argparse
from functools import partial

from .parsing import ignored, flag, custom, choices
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

        if p.annotation is ignored:
            if p.default is empty:
                raise TypeError(
                    f"An argument {name} cannot be ignored, "
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
        elif type(p.annotation) is choices:
            kwargs.update(dict(choices=p.annotation))
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
    obj = cls(
        **{
            key: postprocess_value(value)
            for key, value in vars(args).items()
            if key in acceptees
        }
    )

    acceptees = {p.name for p in read_params(cmdfn)}
    cmdfn(
        obj,
        **{
            key: postprocess_value(value)
            for key, value in vars(command_args).items()
            if key in acceptees
        },
    )


def postprocess_value(value):
    if isinstance(value, str) and value.lower() in ["null", "none"]:
        value = None
    return value
