import inspect
import argparse
from functools import partial
from operator import attrgetter

from .parsing import get_parser
from .typing import Ignored, Flag, get_annotated_data
from .utils import print_args, delete_first, find_first, find_first_index


def change_kind(p, kind):
    return inspect.Parameter(p.name, kind, default=p.default, annotation=p.annotation)


def merge_params(base_params, derived_params):
    param_dict = {}

    # handle *args
    if any(p.kind is p.VAR_POSITIONAL for p in derived_params):
        # remove *args
        delete_first(derived_params, lambda p: p.kind is p.VAR_POSITIONAL)

        # find the first keyword only parameters
        p = find_first(derived_params, lambda p: p.kind is p.KEYWORD_ONLY)

        if p is None:
            stop = len(base_params)
        else:
            stop = find_first_index(base_params, lambda b: b.name == p.name)

        # inherit **kwargs
        for p in base_params[:stop]:
            param_dict[p.name] = change_kind(p, p.POSITIONAL_ONLY)

    # handle **kwargs
    if any(p.kind == p.VAR_KEYWORD for p in derived_params):
        # remove **kwargs
        delete_first(derived_params, lambda p: p.kind is p.VAR_KEYWORD)

        # find the first keyword only parameters
        p = find_first(derived_params, lambda p: p.kind is p.KEYWORD_ONLY)

        if p is None:
            start = 0
        else:
            start = find_first_index(base_params, lambda b: b.name == p.name) + 1

        # inherit **kwargs
        for p in base_params[start:]:
            param_dict[p.name] = change_kind(p, p.KEYWORD_ONLY)

    # update params using derived
    for p in derived_params:
        param_dict[p.name] = p

    # from Python 3.7, dict is now OrderedDict
    return list(param_dict.values())


def inspect_params(cls, name, inherit=True):
    """
    Recursively parse function params.
    Function parameters of the derived class overrides the base class ones.
    """
    if cls is None:
        return []

    f = getattr(cls, name, None)
    if f is None:
        return []

    params = list(inspect.signature(f).parameters.values())

    bases = cls.__bases__ if inherit else []
    for base in bases:
        params = merge_params(inspect_params(base, name), params)

    return params


def normalize_option_name(name):
    """Use '-' as default instead of '_' for option as it is easier to type."""
    if name.startswith("--"):
        name = name.replace("_", "-")
    return name


def add_arguments_from_params(parser, params):
    empty = inspect.Parameter.empty

    for p in params:
        if p.name == "self":
            continue

        if p.annotation is Ignored:
            if p.default is empty:
                msg = f"Argument {p.name} is not ignorable as it is not an option."
                raise TypeError(msg)
            else:
                continue

        if p.default is not empty or p.annotation is Flag:
            name = normalize_option_name(f"--{p.name}")
        else:
            name = p.name

        kwargs = {
            "default": None if p.default is empty else p.default,
            "type": None if p.annotation is empty else get_parser(p.annotation),
        }

        kwargs.update(get_annotated_data(p.annotation))

        if p.annotation is Flag:
            del kwargs["type"]

        parser.add_argument(name, **kwargs)


def command(f=None, inherit=True):
    if f is not None:
        f._zouqi_data = dict(inherit=inherit)
        return f
    return partial(command, inherit=inherit)


def iterate_command_functions(cls):
    for _, func in inspect.getmembers(cls, inspect.isfunction):
        if hasattr(func, "_zouqi_data"):
            yield func


def call(func, args, params: list[inspect.Parameter]):
    read = lambda p: getattr(args, p.name)
    exists = lambda p: hasattr(args, p.name)
    is_pos = lambda p: p.kind in [p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD]
    return func(
        *[read(p) for p in params if exists(p) and is_pos(p)],
        **{p.name: read(p) for p in params if exists(p) and not is_pos(p)},
    )


def start(cls, inherit=True):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    # global params (i.e. params of __init__)
    params = inspect_params(cls, "__init__", inherit)
    for name, command_data in map(
        attrgetter("__name__", "_zouqi_data"),
        iterate_command_functions(cls),
    ):
        # local params (i.e. params of command function)
        command_data["params"] = inspect_params(cls, name, command_data["inherit"])
        subparser = subparsers.add_parser(name)
        command_param_names = {p.name for p in command_data["params"]}
        filtered_params = filter(lambda p: p.name not in command_param_names, params)
        add_arguments_from_params(subparser, filtered_params)
        subparser.add_argument("--print-args", action="store_true")
        add_arguments_from_params(subparser, command_data["params"])

    args = parser.parse_args()

    if args.print_args:
        print_args(args)

    instance = call(cls, args, params)

    # if there is an placeholder, then set args to the instance
    if hasattr(instance, "args") and instance.args is None:
        instance.args = args

    command_func = getattr(instance, args.command)
    command_data = command_func._zouqi_data
    call(command_func, args, command_data["params"])

    return instance
