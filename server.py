from flask import Flask, Response
from flask_sock import Sock
import haddock
from clans.hofferson import astrid, finn
from clans.ingerman import fishlegs
from clans.jorgenson import snotlout
from clans.thorston import tuffnut
from clans.trader import johann
from clans.thorston import ruffnut
from components.hofferson.astrid import TalkingRenderChief
from components.hofferson.finn import WanderingRenderChief
from components.jorgenson.snotlout import (
    PromptRenderChief,
    DialogueRenderChief,
    StoryRenderChief,
)
from librarians import core
import json
import uuid
from collections.abc import Callable
from components.thorston.ruffnut import RuffnutInitiationStateRenderChief
from components.trader.johann import FishingRenderChief

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
haddock.chieftain.application = None

# ---------------------------------------------------------------------------
# Register clans (riders) and chiefs (view layer)
# ---------------------------------------------------------------------------

haddock.chieftain.register_clan(astrid)
haddock.chieftain.register_clan(finn)
haddock.chieftain.register_clan(fishlegs)
haddock.chieftain.register_clan(snotlout)
haddock.chieftain.register_clan(tuffnut)
haddock.chieftain.register_clan(ruffnut)
haddock.chieftain.register_clan(johann)

haddock.chieftain.declare_chief(PromptRenderChief())
haddock.chieftain.declare_chief(DialogueRenderChief())
haddock.chieftain.declare_chief(StoryRenderChief())
haddock.chieftain.declare_chief(RuffnutInitiationStateRenderChief())
haddock.chieftain.declare_chief(FishingRenderChief())
haddock.chieftain.declare_chief(TalkingRenderChief())
haddock.chieftain.declare_chief(WanderingRenderChief())


class FlaskApplication:
    send_data: Callable[[str, haddock.JSONValue], None]

    def __init__(self, send_data):
        self.send_data = send_data


app = Flask(__name__)
sock = Sock(app)
save_path = ""


def reset_game():
    haddock.chieftain.states.clear()
    haddock.chieftain.entities.clear()


@app.route("/")
def index():
    resp = Response(
        response=json.dumps(core.get_save_files()),
        status=200,
        mimetype="application/json",
    )

    return resp


@app.route("/spawn/<name>")
def spwan(name):
    global save_path
    reset_game()

    save_path = core.SAVE_DIRECTORY + "/" + str(uuid.uuid4()) + ".json"

    haddock.chieftain.states.append(finn.Wandering("berk_arena"))
    haddock.chieftain.states.append(ruffnut.RuffnutInitiationState())

    # Player inventory
    haddock.chieftain.entities[haddock.EntityID("ingerman", "satchel", "1")] = (
        fishlegs.SmallSatchel(
            [], haddock.EntityID("jorgenson", "player", "player")
        )
    )

    # Player entity
    haddock.chieftain.entities[
        haddock.EntityID("jorgenson", "player", "player")
    ] = snotlout.Player(name)

    # Active quests
    haddock.chieftain.entities[
        haddock.EntityID("jorgenson", "quest", "rescue_hiccup_toothless")
    ] = snotlout.DragonicQuest("rescue_hiccup_toothless")

    haddock.chieftain.entities[
        haddock.EntityID("jorgenson", "quest", "meet_hiccup")
    ] = snotlout.DragonicQuest("meet_hiccup")

    haddock.chieftain.save(save_path)

    return "Initalization Complete"


@app.route("/load/<id>")
def load(id):
    global save_path
    save_path = core.SAVE_DIRECTORY + "/" + id
    haddock.chieftain.load(save_path)

    return f"Loaded player {haddock.chieftain.call_entity(haddock.EntityID('jorgenson', 'player', 'player')).name}, ID {id}"  # type: ignore


@sock.route("/berk")
def berk(ws):
    haddock.chieftain.application = FlaskApplication(
        lambda tag, data: ws.send(json.dumps([tag, data]))
    )

    haddock.chieftain.mail_event(haddock.TeamAssembled())

    while True:
        haddock.chieftain.save(save_path)
        data = ws.receive()
        event = haddock.deserialize(json.loads(data))

        haddock.chieftain.mail_event(event)  # type: ignore
        haddock.chieftain.save(save_path)


app.run()
