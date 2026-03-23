"""
main.py — Bootstrap entry point for Tales of Dragons.

Wires up the engine (Hiccup), registers all clans and render chiefs,
seeds initial game state, and starts the Textual application.

To start the game:
    python main.py
"""

import haddock
import stoick
from clans.hofferson import astrid, finn
from clans.ingerman import fishlegs
from clans.jorgenson import snotlout
from components.hofferson.astrid import TalkingRenderChief
from components.hofferson.finn import WanderingRenderChief
from components.ingerman.fishlegs import SatchelsListRenderChief, SatchelItemsRenderChief
from components.jorgenson.snotlout import PromptRenderChief, DialogueRenderChief, StoryRenderChief

# ---------------------------------------------------------------------------
# Register module cross-injections
# (fishlegs adds "Check satchel" to NPC and location menus)
# ---------------------------------------------------------------------------

astrid.modules.append(fishlegs)
finn.modules.append(fishlegs)

# ---------------------------------------------------------------------------
# Initialise the engine
# ---------------------------------------------------------------------------

haddock.chieftain = haddock.Hiccup()
haddock.chieftain.application = stoick.TextualApplication()

# ---------------------------------------------------------------------------
# Register clans (riders) and chiefs (view layer)
# ---------------------------------------------------------------------------

haddock.chieftain.register_clan(astrid)
haddock.chieftain.register_clan(finn)
haddock.chieftain.register_clan(fishlegs)
haddock.chieftain.register_clan(snotlout)

haddock.chieftain.declare_chief(TalkingRenderChief())
haddock.chieftain.declare_chief(WanderingRenderChief())
haddock.chieftain.declare_chief(SatchelsListRenderChief())
haddock.chieftain.declare_chief(SatchelItemsRenderChief())
haddock.chieftain.declare_chief(PromptRenderChief())
haddock.chieftain.declare_chief(DialogueRenderChief())
haddock.chieftain.declare_chief(StoryRenderChief())

# ---------------------------------------------------------------------------
# Seed initial game state
# ---------------------------------------------------------------------------

# Location stack: player starts at the arena, with a conversation with Hiccup
# already on top (Talking is rendered first since it's appended last).
haddock.chieftain.states.append(finn.Wandering("berk_arena"))
haddock.chieftain.states.append(astrid.Talking("hiccup"))

# Player inventory
haddock.chieftain.entities[haddock.EntityID("ingerman", "satchel", "1")] = fishlegs.Satchel(
    [], 10, haddock.EntityID("haddock", "player", "player")
)

# Player entity
haddock.chieftain.entities[haddock.EntityID("jorgenson", "player", "player")] = snotlout.Player(
    "Boldkhava"
)

# Active quests
haddock.chieftain.entities[haddock.EntityID("jorgenson", "quest", "rescue_hiccup_toothless")] = (
    snotlout.DragonicQuest("rescue_hiccup_toothless")
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

haddock.chieftain.application.run()
