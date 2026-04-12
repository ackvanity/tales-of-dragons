from dragonic.interactions import (
    send_dialogue,
    send_prompt,
    add_character_hook,
    send_story,
)
from dragonic.core import world
from dragonic.base import NoOpSyscall

async def main():
    await NoOpSyscall()
    await send_dialogue("???", "Hi there folks, and welcome to Berk. Who are you?")
    res = (await send_prompt([f"Hi, I'm {await world.player.name}!"]))
    await send_dialogue(await world.player.name, f"Hi, I'm {await world.player.name}!")
    await send_dialogue("???", f"Well, nice to know you, {await world.player.name}. My name's Hiccup! Usually my dad does greetings, but he's gone for willow bark, again.")
    await send_dialogue("Hiccup", "Hey, do you happen to be good with tools or something?")
    await send_prompt([f"Well, I'm pretty good in crafting..."])
    await send_dialogue(await world.player.name, f"Well, I'm pretty good in crafting...")
    await send_dialogue("Hiccup", "Great! Let's go to my workshop.")
    await send_dialogue(await world.player.name, "Oh, uh, sure. I guess.")
    await send_dialogue("Hiccup", "Okay, so this is my workshop, it's a bit beaten up wit Grump around but it's nicely located next to Gobber's forge! Anywho, if you need anything to make, you'll always a hand or two.")
    await send_story("*A Night Fury growls*")
    await send_dialogue("Hiccup", f"Yes, Toothless, and a paw.... Oh, meet Toothless! Toothless, {await world.player.name}. {await world.player.name}, Toothless. I hope you're not too scared of him. He's really kind actually -- all dragons are.")
    await send_dialogue(await world.player.name, "Hiccup, I think I should get going. The village won't introduce myself, right?")
    await send_dialogue("Hiccup", "Right! Sure, there's the exit, you should be right at the arena after that.")
    await send_dialogue(await world.player.name, "Okay, bye Hiccup!")
