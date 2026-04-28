from dragonic.interactions import send_dialogue


async def send_debug(obj: object):
    await send_dialogue("DEBUG", str(obj))
