# Zouqi: A Python CLI Starter Purely Built on argparse.

Zouqi (『走起』 in Chinese) is a CLI starter similar to [python-fire]. It is purely built on argparse.

## Installation

```plain
pip install zouqi
```

## Example

### Code

```python
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


if __name__ == "__main__":
    print("======= Calling in the script ========")
    SuperFancyDriver("John").drive_wash("car")
    print("======= Calling from the CLI ========")
    zouqi.start(SuperFancyDriver)
```

### Runs

```plain
$ python3 example.py
======= Calling in the script ========
John is a super fancy driver
John drives a car
John washes a car, good.
======= Calling from the CLI ========
usage: example.py [-h] [--print-args] {drive,drive_wash,wash} who
example.py: error: the following arguments are required: command, who
```

```plain
$ python3 example.py drive John car
======= Calling in the script ========
John is a super fancy driver
John drives a car
John washes a car, good.
======= Calling from the CLI ========
John is a super fancy driver
John drives a car
```

```plain
$ python3 example.py drive_wash John --something truck --print-args
======= Calling in the script ========
John is a super fancy driver
John drives a car
John washes a car, good.
======= Calling from the CLI ========
┌─────────────────────┐
│      Arguments      │
├─────────────────────┤
│command: drive_wash  │
│name: John           │
│print_args: True     │
│something: truck     │
└─────────────────────┘
John is a super fancy driver
John drives a truck
John washes a truck, good.
```
