# Zouqi: A Python CLI Starter Purely Built on argparse.

Zouqi (『走起』 in Chinese) is a CLI starter similar to [python-fire](https://github.com/google/python-fire). It is purely built on argparse. 

## Why not [python-fire](https://github.com/google/python-fire)?

  - Fire cannot be used to share options between commands easily.
  - Fire treat all member functions as its command, which is not desirable in many situations.

## Example

### Code

```python
import zouqi


class Runner(zouqi.Runner):
    def __init__(self):
        self.add_argument("who", type=str)

        # Call init after argument adding to make sure it is updated.
        super().__init__()

    # (This is not a command.)
    def show(self, action, something):
        print(self.args.who, action, something)

    # Decorate the command with the zouqi.command decorator
    @zouqi.command
    def drive(self, something):
        # something without default value becomes an argument: <something>
        self.show("drives", something)

    @zouqi.command
    def wash(self, something):
        self.show("washes", something)

    @zouqi.command
    def drive_and_wash(self, something="car"):
        # something with default value becomes an option: --something
        self.drive(something)
        self.wash(something)


if __name__ == "__main__":
    Runner().run()
```

### Runs

```
$ python3 example.py 
usage: example.py [-h] {drive,wash} who
example.py: error: the following arguments are required: command, who
```

```
$ python3 example.py drive John car
John drives car
```

```
$ python3 example.py drive_and_wash John --something truck
John drives truck
John washes truck
```
