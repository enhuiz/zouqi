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
