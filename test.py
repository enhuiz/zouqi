import sys
from unittest.mock import patch

import zouqi
from zouqi.typing import Ignored, Custom, Flag, Parser

from argparse import Namespace
from typing import Optional


def prettify(s):
    return f"pretty {s}"


# equivalent to: parser.add_argument(..., type=prettify).
PrettifiedString = Custom[str, Parser(type=prettify)]


class Driver:
    # If there is a placeholder called args,
    # it will be assigned as parser.parse_args() after parsing.
    args: Optional[Namespace] = None

    def __init__(self, name: str, title: str = "guy", flag: Flag = False):
        # name will be treated as parser.add_argument("name")
        # title will be treated as parser.add_argument("title", default="")
        self.name = name
        self.title = title
        self.flag = flag

    # not a command.
    def print_action(self, action, something):
        print(self.name, "is a", self.title)
        print(self.name, action, something)

    # decorate the cli command with the zouqi.command decorator.
    @zouqi.command
    def drive(self, something, maybe_ignored: bool = False, title: str = "driver"):
        # equivalent to: parser.add_argument('something').
        self.maybe_ignored = maybe_ignored
        self.print_action("drives a", something)
        print("Flag is", self.flag)

    @zouqi.command
    def wash(self, something, ignored: Ignored = ""):
        # hidden option will be ignored in cli but still visible in no-cli callings
        self.print_action("washes a", something + ignored)

    @zouqi.command
    def drive_wash(self, something: Optional[str] = "car"):
        # equivalent to: parser.add_argument('--something', type=prettify, default='car').
        if something is None:
            something = "nothing"
        self.drive(something)
        self.wash(something, ", good")


class FancyDriver(Driver):
    def __init__(self, *args, title: str = "fancy guy", **kwargs):
        # <title = "fancy driver"> overrides <title = "driver">
        # as <flag> is not passed, it will be ignored.
        super().__init__(*args, title=title, **kwargs)

    @zouqi.command
    def drive(self, something: PrettifiedString, title: str = "fancy driver"):
        # <something: PrettifiedString> overrides <something: str>
        # option overrides argument, which requires --something
        super().drive(something)

    # same as base class, but not a command, cannot be called.
    def wash(self, *args, **kwargs):
        super().wash(*args, **kwargs)


def test_runner_1(capsys):
    argv = [__name__, "drive", "John", "car"]
    with patch.object(sys, "argv", argv):
        zouqi.start(Driver)
    captured = capsys.readouterr()
    assert captured[0] == "John is a driver\nJohn drives a car\nFlag is False\n"


def test_fancy_runner_1(capsys):
    argv = [__name__, "drive", "John", "car"]
    with patch.object(sys, "argv", argv):
        zouqi.start(FancyDriver)
    captured = capsys.readouterr()
    assert (
        captured[0]
        == "John is a fancy driver\nJohn drives a pretty car\nFlag is False\n"
    )


def test_fancy_runner_2(capsys):
    argv = [__name__, "drive_wash", "John", "--something", "car"]
    with patch.object(sys, "argv", argv):
        zouqi.start(FancyDriver)
    captured = capsys.readouterr()
    assert (
        captured[0]
        == "John is a fancy guy\nJohn drives a car\nFlag is False\nJohn is a fancy guy\nJohn washes a car, good\n"
    )


def test_bool():
    argv = [__name__, "drive", "John", "car", "--maybe-ignored", "false"]
    with patch.object(sys, "argv", argv):
        driver = zouqi.start(Driver)
    assert not driver.maybe_ignored

    argv = [__name__, "drive", "John", "car", "--maybe-ignored", "true"]
    with patch.object(sys, "argv", argv):
        driver = zouqi.start(Driver)
    assert driver.maybe_ignored


def test_none(capsys):
    def assertion(something, expected):
        argv = [__name__, "drive_wash", "John", "--something", something]
        with patch.object(sys, "argv", argv):
            zouqi.start(FancyDriver)
        captured = capsys.readouterr()
        assert (
            captured[0]
            == f"John is a fancy guy\nJohn drives a {expected}\nFlag is False\nJohn is a fancy guy\nJohn washes a {expected}, good\n"
        )

    assertion("none", "nothing")
    assertion("null", "nothing")
    assertion("None", "nothing")
    assertion("NULL", "nothing")
    assertion("NIL", "NIL")
