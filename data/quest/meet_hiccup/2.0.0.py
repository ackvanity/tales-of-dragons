from dragonic.interactions import (
    send_dialogue,
    send_prompt,
    send_story,
    send_debug,
)
from dragonic.base import NoOpSyscall

VERSION = (2, 0, 0)


async def surviving():
    await send_debug("Surviving Scene")


async def who_am_i():
    await send_debug("Who Am I Scene")


async def stay_alive():
    await send_dialogue(
        "HICCUP",
        "Woah! Just stay with me bud, j-just stay with me! Easy now, deep breaths, deeep breaths....",
    )
    await send_story(
        "Hiccup gently places his hand under your body. In a stroke he lifts you. Your head spins. Everything is up. Nothing is up. The Night Fury looms inches below you as Hiccup lowers you to the saddle. Your body has no choice but to lie as low as it can, and tight pain pierces your forehead as he places you down on Toothless. Your bruises explode in pain, scraping with the rough weathered saddle."
    )
    await send_story(
        "Your eyes feel so heavy... and you don't know how long they'll stay open"
    )

    result = await send_prompt(
        [
            "Oh... I'm just... gonna sleep... Hiccup...",
            "Oookay- I think... I'm... good to... go now...",
        ]
    )

    await send_dialogue("YOU", result.text)

    if result.index == 0:
        await send_dialogue(
            "HICCUP",
            "Oh gods, hang on. Hang on, d-don't close your eyes! Hey, hey- look at me! I'm here, stay with me now, just stay with me for a while. Please... don't go. just remember, deep breaths. O-okay, now you're getting it!",
        )
        await send_story(
            "You try pulling your lead-heavy eyelids up, following what Hiccup told you to do. Your lungs barely fill up with air, every breath pushing your chest to its limits."
        )

    elif result.index == 1:
        await send_story(
            "Okay... now just stay calm and stay with me, alright? Re-Remember, deep breaths... deep breaths..."
        )

    await send_story(
        "Toothless begins plowing the thick undergrowth. Your head lolls with every step, as the world shakes around you. The only things that stay are the hard saddle pressing on your back and Hiccup's hands tensely clenching your hands."
    )
    await send_dialogue(
        "HICCUP",
        "Hold on now... hold on! You're doing good- just hang on now, j-just a littleee more...",
    )
    await send_story(
        "The blue skies swim past you as you try to find which way is up. A wooden roof cuts into the vivid sky hue. Rustic and aged, as if it will fall by dusk. Toothless settles down immediately, sending the world on a major earthquake. You barely hold balance. Your head tips to the left. Your body follows. Hiccup shifts forward. His two hands catch your body. Barely"
    )
    await send_dialogue(
        "HICCUP",
        "Oh, woaah! It's okay... it's okay... we're at Gothi's now. She will treat you",
    )
    await send_dialogue("YOU", "Ah... need... sleep...")
    await send_story(
        "Succumbing to your tiredness, you let your eyelids close. The world turns pitch black and silence appears, but a pair of hands still grip yours, worried to let go. Nobody tells you to stay awake, so you just... continue... because... what else can.... you... do..."
    )


async def crash_land():
    await send_story(
        "You lay weakly on the ground, back pressed against the thick damp grass. Your head barely holds, bursting into headache on every move..."
    )
    await send_story(
        "A Night Fury walks past you. Its black scales hide the sun from you. Its growl vibrates your lungs. Your head shakes. You want to move. But you can't even stay awake."
    )
    await send_dialogue("???", "Hey! Toothless, what did you find this time bud...?")
    await send_story(
        "The fish-thin kid rubs his fingers around your left hand, looking for a pulse. The Night Fury stares into your heavy eyelids, mildly touching your bruised face. You want to drift away, but the confusion, steady growl, and the talk of a small-ish Viking teen stops you from doing so."
    )
    await send_dialogue("???", "Uh, hi there, fella. Are you okay?")
    await send_dialogue("YOU", (await send_prompt(["I... guess...."])).text)
    await send_dialogue(
        "???",
        "Oh, thank gods. Can you tell me your name? H-H-How did you end up like this?",
    )

    result = await send_prompt(
        [
            "Wait... what... happened...?",
            "Who, are... you?",
            "Hold... on... my... head... hurts...",
        ]
    )

    await send_dialogue("YOU", result.text)

    if result.index == 0:
        await send_story(
            "The skinny boy gently touches your head, the Night Fury sniffing your bruised shoulder"
        )
        await send_dialogue(
            "???",
            "It's okay, you're safe. I don't know either, you were like this when Toothless smelled you.",
        )

        result_2 = await send_prompt(
            ["Who's... Toothless?", "Okay- ah!! I... get it..."]
        )

        await send_dialogue("YOU", result_2.text)

        if result_2.index == 0:
            await send_dialogue(
                "???",
                "Oh, my bad. My name's Hiccup, and that Night Fury's Toothless - don't get scared by him!",
            )
            await send_dialogue("HICCUP", "So, who are you?")
            await send_dialogue("YOU", (await send_prompt(["I... don't know..."])).text)

            await who_am_i()

            await send_dialogue(
                "HICCUP",
                "Oh gods, I think you're paling. We need to get to Gothi, now!",
            )

            await stay_alive()

        elif result_2.index == 1:
            await send_dialogue(
                "???",
                "Gods, you look... pale. We need to get you to Gothi, now. Toothless!",
            )
            await send_dialogue(
                "???",
                "I'm Hiccup, by the way. I'll take you on Toothless. He's the Night Fury.",
            )

            await stay_alive()

            await send_dialogue(
                "HICCUP", "So, who are you? You haven't said your name yet..."
            )
            await send_dialogue(
                "YOU",
                (await send_prompt(["I'm... I'm... uh, what's my name...?"])).text,
            )

            await who_am_i()

    elif result.index == 1:
        await send_dialogue(
            "???",
            "Oh, my bad. My name's Hiccup, and that Night Fury's Toothless - don't get scared by him!",
        )

        result_2 = await send_prompt(
            [
                "Oh, that... good...",
                "Nice... meeting... you... I'm... I'm... uh, who am I...?",
            ]
        )

        await send_dialogue("YOU", result_2.text)

        if result_2.index == 0:
            await send_dialogue(
                "HICCUP",
                "Oh, gods... you're paling. We need to get you to Gothi, now. Toothless!",
            )

            await stay_alive()

            await send_dialogue(
                "HICCUP", "So, who are you? You haven't said your name yet..."
            )
            await send_dialogue(
                "YOU",
                (await send_prompt(["I'm... I'm... uh, what's my name...?"])).text,
            )

            await who_am_i()

        elif result_2.index == 1:
            await who_am_i()

            await send_dialogue(
                "HICCUP",
                "Oh gods, I think you're paling. We need to get to Gothi, now!",
            )

            await stay_alive()


async def main():
    await NoOpSyscall()

    await crash_land()
    await surviving()
