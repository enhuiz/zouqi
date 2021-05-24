import sys
from unittest.mock import patch

import zouqi
from zouqi.typing import Ignored, Custom


def prettify(s):
    return f"pretty {s}"


PrettifiedString = Custom[str, dict(type=prettify)]


class Driver:
    def __init__(self, name: str):
        self.name = name

    # not a command.
    def print_action(self, action, something):
        print(self.name, action, something)

    # decorate the cli command with the zouqi.command decorator.
    @zouqi.command
    def drive(self, something):
        # equivalent to: parser.add_argument('something').
        # the parsed args will be stored in self.drive.args instead of self.args
        self.print_action("drives a", something)

    @zouqi.command
    def wash(self, something, hidden_option: Ignored = ""):
        # hidden option will be ignored in cli but still visible in no-cli callings
        self.print_action("washes a", something + hidden_option)

    @zouqi.command
    def drive_wash(self, something: str = "car"):
        # equivalent to: parser.add_argument('--something', type=prettify, default='car').
        self.drive(something)
        self.wash(something, ", good.")


class FancyDriver(Driver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @zouqi.command
    def drive(self, something: PrettifiedString, title: str = "fancy driver", **kwargs):
        # other args are automatically inherited from its parent class
        # while something: PrettifiedString overrides something: str
        print(self.name, "is a", title)
        super().drive(something, **kwargs)

    # same as base class, but not a command, cannot be called.
    def wash(self, *args, **kwargs):
        super().wash(*args, **kwargs)


class SuperFancyDriver(FancyDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @zouqi.command(inherit=True)
    def drive(self, something: str, title: str = "super fancy driver", **kwargs):
        # something: str overrides something: PrettifiedString
        # title = "super fancy driver" overrides title = "fancy driver"
        super().drive(something, title=title, **kwargs)


def test_runner_1(capsys):
    argv = [__name__, "drive", "John", "car"]
    with patch.object(sys, "argv", argv):
        zouqi.start(Driver)
    captured = capsys.readouterr()
    assert captured[0] == "John drives a car\n"


def test_fancy_runner_1(capsys):
    argv = [__name__, "drive", "John", "car"]
    with patch.object(sys, "argv", argv):
        zouqi.start(FancyDriver)
    captured = capsys.readouterr()
    assert captured[0] == "John is a fancy driver\nJohn drives a pretty car\n"


def test_super_fancy_runner_1(capsys):
    argv = [__name__, "drive", "John", "car"]
    with patch.object(sys, "argv", argv):
        zouqi.start(SuperFancyDriver)
    captured = capsys.readouterr()
    assert captured[0] == "John is a super fancy driver\nJohn drives a car\n"


def test_super_fancy_runner_2(capsys):
    argv = [__name__, "drive_wash", "John", "--something", "car"]
    with patch.object(sys, "argv", argv):
        zouqi.start(SuperFancyDriver)
    captured = capsys.readouterr()
    assert (
        captured[0]
        == "John is a super fancy driver\nJohn drives a car\nJohn washes a car, good.\n"
    )
