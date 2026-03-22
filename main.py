import haddock
import stoick
from clans.hofferson import astrid, finn
from clans.ingerman import fishlegs
from clans.jorgenson import snotlout
from components.hofferson.astrid import TalkingRenderChief
from components.hofferson.finn import WanderingRenderChief
from components.ingerman.fishlegs import SatchelsListRenderChief, SatchelItemsRenderChief
from components.jorgenson.snotlout import PromptRenderChief, DialogueRenderChief, StoryRenderChief

astrid.modules.append(fishlegs)
finn.modules.append(fishlegs)

haddock.chieftain = haddock.Hiccup()
haddock.chieftain.application = stoick.TextualApplication()

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

haddock.chieftain.states.append(finn.Wandering("berk_arena"))
haddock.chieftain.states.append(astrid.Talking("hiccup"))
haddock.chieftain.entities[haddock.EntityID("ingerman", "satchel", "1")] = fishlegs.Satchel([], 10, haddock.EntityID("haddock", "player", "player"))
haddock.chieftain.entities[haddock.EntityID("jorgenson", "player", "player")] = snotlout.Player("Boldkhava")
haddock.chieftain.entities[haddock.EntityID("jorgenson", "quest", "rescue_hiccup_toothless")] = snotlout.DragonicQuest("rescue_hiccup_toothless")
haddock.chieftain.application.run()

# while True:
#   src = input(">>> ")
#   try:
#     event = eval(src, globals(), locals())
#     haddock.chieftain.mail_event(event)
#   except Exception as e:
#     print("Error evaluating condition:")
#     print(e)
#     print("Engine state not changed.")