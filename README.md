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
        self.add_argument("who")

        # Call init after argument adding to make sure it is updated.
        super().__init__()

    # (This is not a command.)
    def show(self, action):
        print(self.args.who, action, self.args.something)

    # Decorate the command with the zouqi.command decorator
    @zouqi.command
    def drive(self):
        self.add_argument("something")
        self.update_args()  # call update_args after add new args
        self.show("drives")

    @zouqi.command
    def wash(self):
        self.add_argument("something")
        self.update_args()
        self.show("washes")


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