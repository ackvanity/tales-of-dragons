from dataclasses import dataclass
import haddock


@dataclass
class Action:
    line: str
    signal: haddock.Event
    condition: str = "True"
    id: str = ""
