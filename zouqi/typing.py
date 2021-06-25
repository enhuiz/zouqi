from typing import *


class Parser(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


def get_annotated_data(t):
    ret = {}
    origin = get_origin(t)
    if origin is Annotated:
        data = get_args(t)[1]
        if isinstance(data, Parser):
            ret = data
    return ret


Flag = Annotated[bool, Parser(action="store_true", default=False)]
Ignored = Annotated[Any, Parser(ignored=True)]
Custom = Annotated
