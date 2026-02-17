from typing import List

class DialogueResult:
    index: int
    text: str

    def __init__(self, index=None, text=None):
        if index is not None:
            self.index = index # type: ignore
        if text is not None:
            self.text = text # type: ignore

class DragonicStubCallError(NotImplementedError):
    def __init__(self):
        super().__init__("Attemped to call a Dragonic stub object")
    

def send_dialogue(speaker: str, text: str) -> None:
    raise NotImplementedError()

def send_story(text: str) -> None:
    raise NotImplementedError()

def send_prompt(options: List[str]) -> DialogueResult:
    raise NotImplementedError()

def send_pause() -> None:
    raise NotImplementedError()

def add_location_hook(location: str, line: str) -> None:
    raise NotImplementedError()
    
def add_character_hook(character: str, line: str) -> None:
    raise NotImplementedError()