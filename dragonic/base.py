import haddock
from dataclasses import dataclass

class Syscall:
    def __await__(self):
        result = yield self
        return result

class SendEventSyscall(Syscall):
    event: haddock.Event

@dataclass
class Segment:
    pass

class Attr(Segment):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

KeyLike = int | bool | str | haddock.EntityID
ValueLike = haddock.EntityID | haddock.Entity | haddock.State | haddock.JSONValue

class Item(Segment):
    key: KeyLike

    def __init__(self, key: KeyLike) -> None:
        self.key = key

class AttrSyscall(Syscall):
    path: list[Segment]

class ReadAttrSyscall(AttrSyscall):
    pass

class WriteAttrSyscall(AttrSyscall):
    value: ValueLike

class CompositeObject():
    pass