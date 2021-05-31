import textwrap


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
