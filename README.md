# Zouqi: A Python CLI Starter Purely Built on argparse.

Zouqi (『走起』 in Chinese) is a CLI starter similar to [python-fire](https://github.com/google/python-fire). It is purely built on argparse. 

## Why not [python-fire](https://github.com/google/python-fire)?

  - Fire cannot be used to share options between commands easily.
  - Fire treat all member functions as its command, which is not desirable in many situations.

## Installation

```
pip install zouqi
```

## Example

### Code

```python
import zouqi
from zouqi.parsing import ignored


def prettify(something):
    return f"pretty {something}"


class Runner(zouqi.Runner):
    def __init__(self):
        super().__init__()
        self.add_argument("who", type=str)
        self.parse_args()

    # (This is not a command.)
    def show(self, action, something):
        print(self.args.who, action, something)

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


if __name__ == "__main__":
    Runner().run()
```

### Runs

```
$ python3 example.py 
usage: example.py [-h] {drive,drive_and_wash,wash} who
example.py: error: the following arguments are required: command, who
```

```
$ python3 example.py drive John car
John drives a car
```

```
$ python3 example.py drive_and_wash John --something truck
John drives a pretty truck
John washes a pretty truck, good.
```
