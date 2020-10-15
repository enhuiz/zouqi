import types


def ignored():
    pass


def flag():
    pass


def listof(type_):
    return lambda s: list(map(type_, s.split(",")))


def tupleof(type_):
    return lambda s: tuple(map(type_, s.split(",")))


def choices(v):
    try:
        v = list(v)
    except:
        raise ValueError(f"Expect the choices to be iterable but get {v}.")

    def parser(s):
        if s is None:
            return s
        assert s in v, f"{s} is not in possible choices: {v}."
        return s

    return parser


def str2bool(v):
    assert v.lower() in ["true", "false"]
    return v.lower() == "true"


def optional(type_):
    return lambda s: None if s.lower() in ["null", "none"] else type_(s)


def union(*types):
    def parser(s):
        for typ in types:
            try:
                return typ(s)
            except:
                pass
        raise TypeError(s)

    return parser


class lambda_:
    def __init__(self, literal):
        self.literal = literal
        self.func = eval(literal)
        assert isinstance(self.func, types.LambdaType)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __str__(self):
        return self.literal
