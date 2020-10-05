def message_box(title, sections, aligner="<"):
    lines = [title] + [s for section in sections for s in section.splitlines()]
    widest = max(map(len, lines))
    width = widest + 4

    nb = width - 2  # number of blanks
    border = f"│{{: ^{nb}}}│"

    out = []
    out.append("┌" + "─" * nb + "┐")
    out.append(border.format(title.capitalize()))
    out.append("├" + "─" * nb + "┤")

    for i, section in enumerate(sections):
        for line in section.splitlines():
            out.append(border.replace("^", aligner).format(line.strip()))

        if i < len(sections) - 1:
            out.append("├" + "─" * nb + "┤")
        else:
            out.append("└" + "─" * nb + "┘")

    return "\n".join(out)


def print_args(global_args, command_args):
    global_args = [f"{k}: {v}" for k, v in sorted(global_args.items())]
    command_args = [f"{k}: {v}" for k, v in sorted(command_args.items())]
    print(message_box("Arguments", ["\n".join(global_args), "\n".join(command_args)]))
