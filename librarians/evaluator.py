# astrid, finn, fishlegs are intentionally imported into this module's namespace
# so that eval()-based event strings like "finn.LocationTeleportEngineEvent('x')"
# resolve correctly. Do not remove them.
import haddock
from clans.hofferson import astrid, finn
from clans.ingerman import fishlegs

_eval_scope = {"astrid": astrid, "finn": finn, "fishlegs": fishlegs}

def parse_event(event: str) -> haddock.Event:
  return eval(event, _eval_scope)