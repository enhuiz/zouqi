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


if __name__ == "__main__":
    print("======= Calling in the script ========")
    FancyDriver("John").drive_wash("car")
    print("======= Calling from the CLI ========")
    zouqi.start(FancyDriver)
