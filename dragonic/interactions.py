from typing import List
from dragonic.base import Syscall

class StorySyscall(Syscall):
    pass

class SendDialogueSyscall(StorySyscall):
    speaker: str
    line: str

class SendStorySyscall(StorySyscall):
    text: str

class SendPromptSyscall(StorySyscall):
    options: List[str]

class AddLocationHookSyscall(StorySyscall):
    location: str
    line: str

class AddCharacterHookSyscall(StorySyscall):
    character: str
    line: str

class DialogueResult:
    index: int
    text: str

    def __init__(self, index=None, text=None):
        if index is not None:
            self.index = index # type: ignore
        if text is not None:
            self.text = text # type: ignore

async def send_dialogue(speaker: str, line: str) -> None:
    syscall = SendDialogueSyscall()
    syscall.speaker = speaker
    syscall.line = line
    return await syscall

async def send_story(text: str) -> None:
    syscall = SendStorySyscall()
    syscall.text = text
    return await syscall

async def send_prompt(options: List[str]) -> DialogueResult:
    syscall = SendPromptSyscall()
    syscall.options = options
    return await syscall

async def send_pause() -> None:
    syscall = SendPromptSyscall()
    syscall.options = ["Continue"]
    await syscall

async def add_location_hook(location: str, line: str) -> None:
    syscall = AddLocationHookSyscall()
    syscall.location = location
    syscall.line = line
    return await syscall
    
async def add_character_hook(character: str, line: str) -> None:
    syscall = AddCharacterHookSyscall()
    syscall.character = character
    syscall.line = line
    return await syscall