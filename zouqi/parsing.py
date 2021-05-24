from typing import Union, Optional, get_args, get_origin

from .typing import *


def check_literals(s, literals):
    if s.lower() not in literals:
        raise ValueError(f"s.lower() shoud be within {literals}")


def bool_parser(s):
    check_literals(s, ["true", "false"])
    return s.lower() == "true"


def none_parser(s):
    check_literals(s, ["none", "null"])
    return None


def get_parser(t):
    parser = None

    if t is bool:
        parser = bool_parser
    if t is type(None):
        parser = none_parser

    origin = get_origin(t)
    if origin is None:
        parser = t
    elif origin is Annotated:
        data = get_annotated_data(t)
        if "type" in data:
            parser = data["type"]
        else:
            parser = get_parser(get_args(t)[0])
    elif origin is Union:
        parser = union_parsers(*map(get_parser, get_args(t)))

    if parser is None:
        raise NotImplementedError(f"Parser for {t} is not implemented.")

    return parser


def union_parsers(*parsers):
    def parse(s):
        lines = []
        for parser in parsers:
            try:
                return parser(s)
            except Exception as e:
                lines.append(f"\t{parser.__name__}: {str(e)}")
        raise ValueError("union_parsers: \n" + "\n".join(lines))

    return parse


if __name__ == "__main__":
    assert get_parser(Optional[bool])("None") == None
    assert get_parser(bool)("true") == True
    assert get_parser(Annotated[float, ""])("235.5") == 235.5
    assert get_parser(Union[bool, float])("235.5") == 235.5
    assert get_parser(Union[bool, int])("235.5") == 235.5
