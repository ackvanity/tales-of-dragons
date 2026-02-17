import json
from typing import Iterable

SAVE_DIRECTORY = "saves"
DATA_DIRECTORY = "data"


def get_data(path: Iterable[str] | str):
    if not isinstance(path, str):
        path = "/".join(path)

    try:
        with open(f"{DATA_DIRECTORY}/{path}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise
