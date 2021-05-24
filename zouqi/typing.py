from typing import *


def get_annotated_data(t):
    data = {}
    origin = get_origin(t)
    if origin is Annotated:
        data.update(get_args(t)[1])
    return data


Flag = Annotated[bool, dict(action="store_true", default=False)]
Ignored = Annotated[Any, dict(ignored=True)]
Custom = Annotated
