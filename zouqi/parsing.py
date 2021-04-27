class ignored:
    pass


class flag:
    pass


class custom(dict):
    pass


def boolean(v):
    assert v.lower() in ["true", "false"]
    return v.lower() == "true"


def optional(parser):
    def parse(s):
        if s.lower() in ["null", "none"]:
            return None
        return parser(s)

    return parse
