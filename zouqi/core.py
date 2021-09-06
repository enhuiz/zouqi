import sys
import inspect
import argparse
from operator import attrgetter
from pathlib import Path
from abc import ABC

from .parsing import get_parser
from .typing import Ignored, Flag, get_annotated_data
from .utils import print_args, yaml2argv


def inspect_params(cls, name):
    """
    Recursively parse function params.
    Function parameters of the derived class overrides the base class ones.
    """
    params = []

    not_var_kind = lambda p: p.kind not in [p.VAR_POSITIONAL, p.VAR_KEYWORD]

    mro = filter(lambda c: c not in [object, ABC], cls.mro())
    for i, the_cls in enumerate(mro):
        fn = getattr(the_cls, name, None)

        if fn is not None:
            the_params = inspect.signature(fn).parameters.values()

            if any(p.kind is p.VAR_POSITIONAL for p in the_params):
                raise RuntimeError(
                    "Variable positional argument is no longer supported after zouqi==1.10, "
                    f"but found in {the_cls.__name__}.{name}."
                )

            params.extend([p for p in the_params if not_var_kind(p)])

            if i == 0 and all(p.kind is not p.VAR_KEYWORD for p in the_params):
                # if the derived method does not has **kwargs
                # no params from base method will be parsed from command line
                break

    # keep only the first param of the params with the same name
    unique_indices = {}
    for i, p in enumerate(params):
        if p.name not in unique_indices:
            unique_indices[p.name] = i
    params = [params[i] for i in unique_indices.values()]

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


def command(fn):
    fn._zouqi = {}
    return fn


def command_fns(cls):
    for _, fn in inspect.getmembers(cls, inspect.isfunction):
        if hasattr(fn, "_zouqi"):
            yield fn


def call(fn, args, params: list[inspect.Parameter]):
    read = lambda p: getattr(args, p.name)
    exists = lambda p: hasattr(args, p.name)
    return fn(**{p.name: read(p) for p in params if exists(p)})


def start(cls):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    # global params (i.e. params of __init__)
    params = inspect_params(cls, "__init__")
    for name, command_data in map(
        attrgetter("__name__", "_zouqi"),
        command_fns(cls),
    ):
        # local params (i.e. params of command function)
        command_data["params"] = inspect_params(cls, name)
        subparser = subparsers.add_parser(name)
        command_param_names = {p.name for p in command_data["params"]}
        filtered_params = filter(lambda p: p.name not in command_param_names, params)
        add_arguments_from_params(subparser, filtered_params)
        subparser.add_argument(
            "--print-args",
            action="store_true",
            help="Print the parsed args in a message box.",
        )
        subparser.add_argument(
            "--config",
            type=Path,
            default=None,
            help="A YAML configuration file that overrides the default values of args.",
            metavar="YAML",
        )
        subparser.add_argument(
            "--config-ignored",
            type=str,
            nargs="*",
            default=[],
            help="A list of keys in the YAML configuration file that should be ignored.",
            metavar="KEYS",
        )
        add_arguments_from_params(subparser, command_data["params"])

    args = parser.parse_args()
    if args.config:
        # priority: default < yaml config < sys.argv
        argv = (
            sys.argv[1:2]
            + yaml2argv(args.config, args.command, args.config_ignored)
            + sys.argv[2:]
        )
        args = parser.parse_args(argv)

    if args.print_args:
        print_args(args)

    instance = call(cls, args, params)

    # if there is an placeholder, then set args to the instance and update args
    if hasattr(instance, "args") and isinstance(instance.args, argparse.Namespace):
        instance.args = argparse.Namespace(**vars(instance.args), **vars(args))

    command_func = getattr(instance, args.command)
    command_data = command_func._zouqi
    call(command_func, args, command_data["params"])

    return instance
