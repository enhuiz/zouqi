import types


class ignored:
    pass


class flag:
    pass


class custom(dict):
    pass


class choices(list):
    pass


def boolean(v):
    assert v.lower() in ["true", "false"]
    return v.lower() == "true"
