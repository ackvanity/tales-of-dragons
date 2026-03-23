"""
dragonic/core.py — The world proxy object for quest scripts.

Provides the `world` proxy, which quest scripts use to read game state
without direct access to haddock.chieftain. Attribute accesses on `world`
build up a path (e.g. world.player.name → [Attr("player"), Attr("name")])
and awaiting the result yields a ReadAttrSyscall that the runtime resolves.

Usage in quest scripts:
    from dragonic.core import world

    name = await world.player.name    # reads player name
    health = await world.player.health
"""

from typing import Any
from dragonic.base import Segment, Attr, ReadAttrSyscall, WriteAttrSyscall


class Proxy:
    """
    Lazy path-building proxy for reading (and eventually writing) world state.

    Attribute access builds up a path list. Awaiting the proxy yields a
    ReadAttrSyscall that DragonicQuest.step() resolves against engine entities.

    Direct attribute assignment is blocked — use .set(value) instead.
    Attributes starting with "_" are treated as local proxy state and bypass
    the path-building mechanism.
    """

    _path: list[Segment]

    def __init__(self) -> None:
        self._path = []

    def __getattribute__(self, name: str) -> Any:
        if not name.startswith("_"):
            prox = Proxy()
            prox._path = list(self._path)
            prox._path.append(Attr(name))
            return prox
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if not name.startswith("_"):
            raise RuntimeError(
                f"Dragonic scripts cannot directly set global state. "
                f"Use .set({value.__repr__()}) instead"
            )
        object.__setattr__(self, name, value)

    def __await__(self):
        """Yield a ReadAttrSyscall for the current path."""
        syscall = ReadAttrSyscall()
        syscall.path = self._path
        return syscall.__await__()

    async def set(self, value: Any) -> None:
        """Write a value to the current path (not yet fully wired in runtime)."""
        syscall = WriteAttrSyscall()
        syscall.path = self._path
        syscall.value = value
        return await syscall


world = Proxy()
"""
The global world proxy. Import and await attributes to read game state.

    from dragonic.core import world
    name = await world.player.name
"""
