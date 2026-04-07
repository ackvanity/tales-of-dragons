"""
dragonic/base.py — Core syscall types and attribute path primitives.

Defines the low-level machinery that allows Dragonic quest scripts to
communicate with the engine via Python coroutines. A quest script yields
a Syscall object; the runtime intercepts it, fires engine events, and
resumes the coroutine with the result.
"""

import haddock
from dataclasses import dataclass


class Syscall:
    """
    Base class for all Dragonic syscalls.

    A syscall is yielded by a quest coroutine to request an action from
    the engine. The engine intercepts the yield, performs the action, and
    resumes the coroutine with the result value.

    Example (internal):
        result = yield ReadAttrSyscall(path=[Attr("player"), Attr("name")])
        # engine resumes with the player's name as result
    """

    def __await__(self):
        result = yield self
        return result


class SendEventSyscall(Syscall):
    """Reserved syscall for directly sending an engine event (unused)."""

    event: haddock.Event


@dataclass
class Segment:
    """Base class for segments in an attribute path (e.g. world.player.name)."""


class Attr(Segment):
    """
    A named attribute segment in a world proxy path.

    Used to build paths like [Attr("player"), Attr("name")].
    """

    name: str

    def __init__(self, name: str) -> None:
        self.name = name


KeyLike = int | bool | str | haddock.EntityID
"""Valid key types for Item path segments."""

# Import here to avoid circular imports — dragonic.interactions imports haddock,
# haddock does not import dragonic, so this direction is safe.
from dragonic.interactions import DialogueResult as _DialogueResult

ValueLike = (
    haddock.EntityID
    | haddock.Entity
    | haddock.State
    | haddock.JSONValue
    | _DialogueResult
)
"""Valid value types that can flow through the Dragonic data stream."""


class Item(Segment):
    """
    A keyed index segment in a world proxy path (e.g. world.items[key]).

    Not yet used in quest scripts.
    """

    key: KeyLike

    def __init__(self, key: KeyLike) -> None:
        self.key = key


class AttrSyscall(Syscall):
    """Base class for syscalls that operate on an attribute path."""

    path: list[Segment]


class ReadAttrSyscall(AttrSyscall):
    """
    Syscall that reads a value from the game world at the given path.

    Handled by DragonicQuest.step(), which resolves known paths like
    [Attr("player"), Attr("name")] against Hiccup entities.
    """


class WriteAttrSyscall(AttrSyscall):
    """
    Syscall that writes a value to the game world at the given path.

    Not yet fully wired in the runtime.
    """

    value: ValueLike


class CompositeObject:
    """Placeholder for structured world objects. Not yet used."""
