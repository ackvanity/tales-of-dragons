import json
from typing import Iterable

SAVE_DIRECTORY = "saves"
DATA_DIRECTORY = "data"


def get_data(path: Iterable[str] | str, ext: str = "json", parse: bool = True):
    if not isinstance(path, str):
        path = "/".join(path)

    try:
        with open(f"{DATA_DIRECTORY}/{path}.{ext}", "r") as f:
            if parse:
                return json.load(f)
            else:
                return f.read()
    except FileNotFoundError:
        raise
