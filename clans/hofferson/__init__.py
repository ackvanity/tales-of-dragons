"""
clans/hofferson/__init__.py — Shared types for the hofferson module.

The hofferson module handles NPC dialogue (astrid.py) and location
navigation (finn.py). Both systems present the player with a list of
selectable actions, so they share a single Action type defined here.
"""

from dataclasses import dataclass
import haddock


@dataclass
class Action:
    """
    A selectable option presented to the player in a dialogue menu or location view.

    Attributes:
        line:       The button label shown to the player.
        signal:     The Event fired when the player selects this action.
        condition:  A condition string (reserved for future use — currently always "True").
        id:         An optional identifier used by quest hooks to remove injected actions.
                    Leave as "" for static actions that are never removed.
    """

    line: str
    signal: haddock.Event
    condition: str = "True"
    id: str = ""
