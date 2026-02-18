from dragonic.interactions import send_dialogue, send_prompt, add_character_hook, add_location_hook, send_story, send_pause
from dragonic.core import world

async def main():
  await add_character_hook("hiccup", "Hey Hiccup, is that a new tailfin you got for Toothless?")
  await send_dialogue("Hiccup", "Uhh, if you put it that way... yes. Just please don't tell Astrid yet. I really want to take this out on a flight.")
  await send_dialogue("Hiccup", "Wanna go together? I bet Toothless would be happy, right bud?")

  option = await send_prompt(["Yes, of course!", "Uh, no thanks..."])

  if option.index == 0:
    await send_story("The two of you soar above the skies with Toothless. The wind pushing against your face. Hiccup does his usual twisting and turning, and creaks come out like usual.")
    await send_dialogue("Hiccup", f"So, {await world.player.name}, how's the flight? Enjoyable, right?")

    option = await send_prompt(["Yeah, we should go again some time later", "Uh, not really! I'm scared of heights!"])
    await send_dialogue(await world.player.name, option.text)

    await send_story("The tail creaks. At first you thought it was because it's a prototype. Then it grew louder. And a crack appeared. As quick as thunder the tail bids farewell. You lost grip and crashed on the arid woods of somewhere at Berk.")

    await send_dialogue(await world.player.name, f"Uhhh, where are we?")

    await send_story("You'll heroically save Hiccup in due time")
  else:
    await send_story("You'll heroically save Hiccup in due time")