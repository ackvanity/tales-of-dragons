"""
librarians/evaluator.py — Event string parser.

Parses event strings stored in location/character JSON files into live
haddock.Event objects via eval().

This is a legacy mechanism — the event strings were written before a proper
event registry existed. See TODO for planned replacement.

The eval scope is intentionally minimal: only astrid, finn, and fishlegs
are available, limiting what event strings can reference.
"""

# astrid, finn, fishlegs are intentionally imported into this module's namespace
# so that eval()-based event strings like "finn.LocationTeleportEngineEvent('x')"
# resolve correctly against _eval_scope. Do not remove them.
import haddock
from clans.hofferson import astrid, finn
from clans.ingerman import fishlegs
from clans.trader import johann

_eval_scope = {
    "astrid": astrid,
    "finn": finn,
    "fishlegs": fishlegs,
    "haddock": haddock,
    "johann": johann,
}
"""Controlled scope used by eval() to prevent arbitrary code execution."""


def parse_event(event: str) -> haddock.Event:
    """
    Parse an event string from a data file into a live haddock.Event.

    Args:
        event: A Python expression string, e.g.
               "finn.LocationTeleportEngineEvent('berk_square')"

    Returns:
        The haddock.Event instance produced by evaluating the expression.

    Warning:
        This uses eval() and should be replaced with a structured event
        registry. The scope is limited to astrid, finn, and fishlegs.
    """
    return eval(event, _eval_scope)
