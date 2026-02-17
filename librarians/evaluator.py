from clans.hofferson import astrid, finn
from clans.ingerman import fishlegs
import haddock

def parse_event(event: str) -> haddock.Event:
  return eval(event, globals(), locals())