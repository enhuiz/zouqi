import yaml
import textwrap
from itertools import chain


def find_first(l, predicate, default=None):
    return next((x for x in l if predicate(x)), default)


def find_first_index(l, predicate, default=None):
    if default is None:
        default = len(l)
    return next((i for i, x in enumerate(l) if predicate(x)), default)


def delete_first(l, predicate):
    i = find_first_index(l, predicate)
    if i < len(l):
        del l[i]


def message_box(title, content, aligner="<", max_width=70):
    lines = [textwrap.shorten(line, width=max_width) for line in content.splitlines()]

    width = max(map(len, [title] + lines)) + 2

    nb = width - 2  # number of blanks
    border = f"│{{: ^{nb}}}│"

    out = []
    out.append("┌" + "─" * nb + "┐")
    out.append(border.format(title.capitalize()))
    out.append("├" + "─" * nb + "┤")

    for line in lines:
        out.append(border.replace("^", aligner).format(line.strip()))

    out.append("└" + "─" * nb + "┘")

    return "\n".join(out)


def print_args(args):
    args = [f"{k}: {v}" for k, v in sorted(vars(args).items())]
    print(message_box("Arguments", "\n".join(args)))


def yaml2argv(path, command):
    def to_val(x):
        if isinstance(x, (tuple, list)):
            return " ".join(map(to_val, x))
        return str(x)

    def to_key(k):
        return f"--{k.replace('_', '-')}"

    def to_argv(k, v):
        argv = [to_key(k)]
        if v is not None:
            argv.append(to_val(v))
        return argv

    with open(path, "r") as f:
        o: dict = yaml.load(f, yaml.Loader) or {}

    if command in o:
        o.update(o[command])
        del o[command]

    argv = []

    # load the default (i.e. base) yaml of the current yaml
    if "default" in o:
        bases = o["default"]
        if not isinstance(bases, list):
            bases = [bases]
        for base in bases:
            argv.extend(yaml2argv(base, command))
        del o["default"]

    argv.extend(chain.from_iterable(to_argv(k, v) for k, v in o.items()))

    return argv
