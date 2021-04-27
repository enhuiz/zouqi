# Zouqi: A Python CLI Starter Purely Built on argparse.

Zouqi (『走起』 in Chinese) is a CLI starter similar to [python-fire]. It is purely built on argparse.

## Why not [python-fire]?

-   Fire cannot be used to share options between commands easily.
-   Fire treat all member functions as its command, which is not desirable in many situations.

## Installation

```plain
pip install zouqi
```

## Example

### Code

```python
import zouqi
from zouqi.parsing import ignored


def prettify(something):
    return f"pretty {something}"


class Runner:
    def __init__(self, who: str):
        self.who = who

    # (This is not a command.)
    def show(self, action, something):
        print(self.who, action, something)

    # Decorate the command with the zouqi.command decorator.
    @zouqi.command
    def drive(self, something):
        # Equivalent to: parser.add_argument('something').
        # the parsed args will be stored in self.drive.args instead of self.args
        self.show("drives a", something)

    @zouqi.command
    def wash(self, something, hidden_option: ignored = ""):
        # hidden option will be ignored during parsing but still passable by another function
        self.show("washes a", something + hidden_option)

    @zouqi.command
    def drive_and_wash(self, something: prettify = "car"):
        # Equivalent to: parser.add_argument('--something', type=prettify, default='car').
        # Type hint is used as argument parser (a little bit abuse of type hint here).
        self.drive(something)
        self.wash(something, ", good.")


class FancyRunner(Runner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def drive(self, title, *args, **kwargs):
        # other args are automatically inherited from its parent class
        print(self.who, "is a", title)
        super().drive(*args, **kwargs)


class SuperFancyRunner(FancyRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @zouqi.command(inherit=True)
    def drive(self, *args, title: str = "super fancy driver", **kwargs):
        super().drive(title, *args, **kwargs)


if __name__ == "__main__":
    print("======= Calling in the script ========")
    SuperFancyRunner("John").drive_and_wash("car")
    print("======= Calling from the CLI ========")
    zouqi.start(SuperFancyRunner)
```

### Runs

```plain
$ python3 example.py
======= Calling in the script ========
John is a super fancy driver
John drives a car
John washes a car, good.
======= Calling from the CLI ========
usage: example.py [-h] [--print-args] {drive,drive_and_wash,wash} who
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
$ python3 example.py drive_and_wash John --something truck --print-args
======= Calling in the script ========
John is a super fancy driver
John drives a car
John washes a car, good.
======= Calling from the CLI ========
┌─────────────────────────┐
│        Arguments        │
├─────────────────────────┤
│command: drive_and_wash  │
│print_args: True         │
│something: pretty truck  │
│who: John                │
└─────────────────────────┘
John is a super fancy driver
John drives a pretty truck
John washes a pretty truck, good.
```

[python-fire]: https://github.com/google/python-fire
