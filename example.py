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
