from argparse import Namespace
from typing import Optional

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
    # If there is a placeholder called args,
    # it will be assigned as parser.parse_args() after parsing.
    args: Optional[Namespace] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @zouqi.command(inherit=True)
    def drive(self, something: str, title: str = "super fancy driver", **kwargs):
        # something: str overrides something: PrettifiedString
        # title = "super fancy driver" overrides title = "fancy driver"
        assert self.args.something == something
        super().drive(self.args.something, title=title, **kwargs)


if __name__ == "__main__":
    print("======= Calling in the script ========")
    SuperFancyDriver("John").drive_wash("car")
    print("======= Calling from the CLI ========")
    zouqi.start(SuperFancyDriver)
