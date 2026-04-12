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
from clans.thorston.tuffnut import TitleScreen, SaveGameList, CreateGame
from clans.thorston import tuffnut
from components.hofferson.astrid import TalkingRenderChief
from components.hofferson.finn import WanderingRenderChief
from components.ingerman.fishlegs import (
    SatchelsListRenderChief,
    SatchelItemsRenderChief,
)
from components.jorgenson.snotlout import (
    PromptRenderChief,
    DialogueRenderChief,
    StoryRenderChief,
)
from components.thorston.tuffnut import (
    TitleScreenRenderChief,
    SaveGameListRenderChief,
    CreateGameRenderChief,
)
from components.thorston import tuffnut as tuffnut_c
from components.thorston.ruffnut import RuffnutInitiationStateRenderChief
from clans.thorston import ruffnut
import asyncio

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
haddock.chieftain.register_clan(tuffnut)
haddock.chieftain.register_clan(ruffnut)

haddock.chieftain.declare_chief(TalkingRenderChief())
haddock.chieftain.declare_chief(WanderingRenderChief())
haddock.chieftain.declare_chief(SatchelsListRenderChief())
haddock.chieftain.declare_chief(SatchelItemsRenderChief())
haddock.chieftain.declare_chief(PromptRenderChief())
haddock.chieftain.declare_chief(DialogueRenderChief())
haddock.chieftain.declare_chief(StoryRenderChief())
haddock.chieftain.declare_chief(TitleScreenRenderChief())
haddock.chieftain.declare_chief(SaveGameListRenderChief())
haddock.chieftain.declare_chief(CreateGameRenderChief())
haddock.chieftain.declare_chief(RuffnutInitiationStateRenderChief())

# ---------------------------------------------------------------------------
# Seed initial game state
# ---------------------------------------------------------------------------

init_player_name = None
init_save_name = None

def init_game(player_name):
    global init_player_name
    init_player_name = player_name
    haddock.chieftain.application.exit() # type: ignore

def reset_app():
    haddock.chieftain.application = stoick.TextualApplication()
    haddock.chieftain.states.clear()
    haddock.chieftain.entities.clear()

def _init_game(player_name):
    # Restart the application
    reset_app()

    # Location stack: player starts at the arena, with a conversation with Hiccup
    # already on top, followed by a welcome "quest"
    haddock.chieftain.states.append(finn.Wandering("berk_arena"))
    haddock.chieftain.states.append(ruffnut.RuffnutInitiationState())

    # Player inventory
    haddock.chieftain.entities[haddock.EntityID("ingerman", "satchel", "1")] = (
        fishlegs.Satchel(
            [], 10, haddock.EntityID("haddock", "player", "player")
        )
    )

    # Player entity
    haddock.chieftain.entities[
        haddock.EntityID("jorgenson", "player", "player")
    ] = snotlout.Player(player_name)

    # Active quests
    haddock.chieftain.entities[
        haddock.EntityID("jorgenson", "quest", "rescue_hiccup_toothless")
    ] = snotlout.DragonicQuest("rescue_hiccup_toothless")

    haddock.chieftain.entities[
        haddock.EntityID("jorgenson", "quest", "meet_hiccup")
    ] = snotlout.DragonicQuest("meet_hiccup")

tuffnut_c.start_game_func = init_game

haddock.chieftain.states.append(TitleScreen())
haddock.chieftain.states.append(SaveGameList())
haddock.chieftain.states.append(CreateGame())


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

haddock.chieftain.application.run()

if init_player_name:
    reset_app()
    _init_game(init_player_name)
    haddock.chieftain.application.run()