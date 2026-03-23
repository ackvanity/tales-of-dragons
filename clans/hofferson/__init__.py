"""
clans/hofferson/__init__.py — Shared types for the hofferson module.

The hofferson module handles NPC dialogue (astrid.py) and location
navigation (finn.py). Both systems present the player with a list of
selectable actions, so they share a single Action type defined here.
"""

from dataclasses import dataclass, field
from typing import Type
import haddock


@dataclass
class Action(haddock.Serializable):
    """
    A selectable option presented to the player in a dialogue menu or location view.

    Implements Serializable so that injected quest-hook actions stored on Human
    and Location entities are fully persisted and restored without any coupling
    to quest replay.

    The signal is serialized using the haddock event registry — only Event
    subclasses registered via haddock.register_event() can appear as signals
    in persisted actions.

    Attributes:
        line:       The button label shown to the player.
        signal:     The Event fired when the player selects this action.
        condition:  Condition string (reserved for future use, always "True").
        id:         Identifies removable quest-hook actions. Empty for static actions.
    """

    line: str
    signal: haddock.Event = field(default_factory=haddock.Event)
    condition: str = "True"
    id: str = ""

    @staticmethod
    def tag() -> str:
        return "hofferson.Action"

    def serialize(self) -> haddock.JSONValue:
        return {
            "line": self.line,
            "signal": self.signal.serialize(),
            "condition": self.condition,
            "id": self.id,
        }

    @classmethod
    def deserialize(cls: Type["Action"], data: haddock.JSONValue) -> "Action":
        if not isinstance(data, dict):
            raise haddock.DeserializeException(f"Expected dict for Action, got {data!r}")
        return cls(
            line=data["line"],  # type: ignore
            signal=haddock.deserialize_event(data["signal"]),
            condition=data.get("condition", "True"),  # type: ignore
            id=data.get("id", ""),  # type: ignore
        )
