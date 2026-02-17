import haddock
import stoick
from clans.hofferson import astrid, finn
from clans.ingerman import fishlegs
from clans.jorgenson import snotlout
import dragonic.core

test_quest = """
add_character_hook("hiccup", "Hey Hiccup, is that a new tailfin you got for Toothless?")

send_dialogue("hiccup", "A tailfin?")
send_dialogue("hiccup", "Uhh, if you put it that way... yes. Just please don't tell Astrid yet. I really want to take this out on a flight.")
send_dialogue("hiccup", "Wanna go together? I bet Toothless would be happy, right bud?")

option = send_prompt(["Yes, of course!", "Uh, no thanks..."])

send_dialogue("player", option.text)

if option.index == 0:
  send_story("The two of you soar above the skies with Toothless. The wind pushing against your face. Hiccup does his usual twisting and turning, and creaks come out like usual.")
  send_dialogue("hiccup", f"So, {player.name}, how's the flight? Enjoyable, right?")

  option = send_prompt(["Yeah, we should go again some time later", "Uh, not really! I'm scared of heights!"])
  send_dialogue("player", option.text)

  send_story("The tail creaks. At first you thought it was because it's a prototype. Then it grew louder. And a crack appeared. As quick as thunder the tail bids farewell. You lost grip and crashed on the arid woods of somewhere at Berk.")

  send_dialogue("player", f"Uhhh, where are we?")

  send_story("You'll heroically save Hiccup in due time")
else:
  send_story("You'll heroically save Hiccup in due time")"""

astrid.modules.append(fishlegs)
finn.modules.append(fishlegs)

haddock.chieftain = haddock.Hiccup()
haddock.chieftain.application = stoick.TextualApplication()

haddock.chieftain.register_clan(astrid)
haddock.chieftain.register_clan(finn)
haddock.chieftain.register_clan(fishlegs)
haddock.chieftain.register_clan(snotlout)

haddock.chieftain.states.append(finn.Wandering("berk_arena"))
haddock.chieftain.states.append(astrid.Talking("hiccup"))
haddock.chieftain.entities[haddock.EntityID("ingerman", "satchel", "1")] = fishlegs.Satchel([], 10, haddock.EntityID("haddock", "player", "player"))
haddock.chieftain.entities[haddock.EntityID("jorgenson", "player", "player")] = dragonic.core.Player("Boldkhava")
haddock.chieftain.entities[haddock.EntityID("jorgenson", "quest", "rescue_hiccup_toothless")] = snotlout.DragonicQuest(test_quest)
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