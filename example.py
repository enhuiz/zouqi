import zouqi


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
    def wash(self, something):
        self.show("washes a", something)

    @zouqi.command
    def drive_and_wash(self, something: prettify = "car"):
        # Equivalent to: parser.add_argument('--something', type=prettify, default='car').
        # Type hint is used as argument parser (a little bit abuse of type hint here).
        self.drive(something)
        self.wash(something)


if __name__ == "__main__":
    Runner().run()
