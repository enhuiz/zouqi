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
