"""
dragonic/interactions.py — High-level helpers for Dragonic quest scripts.

Provides the async functions that quest scripts call to interact with the
player. Each function constructs the appropriate Syscall subclass and
yields it to the Dragonic runtime, which handles the engine-level dispatch
and resumes the coroutine with the result.

Quest scripts import from this module:
    from dragonic.interactions import send_dialogue, send_prompt, ...
"""

from typing import List
from dragonic.base import Syscall


# ---------------------------------------------------------------------------
# Syscall types (yielded by helper functions below)
# ---------------------------------------------------------------------------

class StorySyscall(Syscall):
    """Base class for syscalls that produce visible output to the player."""


class SendDialogueSyscall(StorySyscall):
    """Syscall to display a character dialogue line. Auto-advances."""

    speaker: str
    line: str


class SendStorySyscall(StorySyscall):
    """Syscall to display a narration paragraph. Auto-advances."""

    text: str


class SendPromptSyscall(StorySyscall):
    """Syscall to present a player choice menu. Suspends until selection."""

    options: List[str]


class AddLocationHookSyscall(StorySyscall):
    """Syscall to inject a navigation option into a location (not yet wired)."""

    location: str
    line: str


class AddCharacterHookSyscall(StorySyscall):
    """Syscall to inject a dialogue option into an NPC. Suspends until clicked."""

    character: str
    line: str


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class DialogueResult:
    """
    The result returned from send_prompt().

    Attributes:
        index: Zero-based index of the option the player selected.
        text:  The label string of the selected option.
    """

    index: int
    text: str

    def __init__(self, index: int | None = None, text: str | None = None) -> None:
        if index is not None:
            self.index = index  # type: ignore
        if text is not None:
            self.text = text  # type: ignore


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def send_dialogue(speaker: str, line: str) -> None:
    """
    Display a dialogue line attributed to speaker.

    The quest suspends until the runtime fires ReturnDataEvent(None) after
    mounting the dialogue widget (auto-advance — no player action needed).
    """
    syscall = SendDialogueSyscall()
    syscall.speaker = speaker
    syscall.line = line
    return await syscall


async def send_story(text: str) -> None:
    """
    Display a narration paragraph with no speaker.

    Auto-advances the same way as send_dialogue.
    """
    syscall = SendStorySyscall()
    syscall.text = text
    return await syscall


async def send_prompt(options: List[str]) -> DialogueResult:
    """
    Present the player with a list of choices and wait for a selection.

    Returns a DialogueResult with the selected option's index and text.
    The quest suspends here until the player makes a choice.
    """
    syscall = SendPromptSyscall()
    syscall.options = options
    return await syscall


async def send_pause() -> None:
    """
    Display a single "Continue" button and wait for the player to click it.

    Use after a story beat that should let the player breathe before the
    next event fires.
    """
    syscall = SendPromptSyscall()
    syscall.options = ["Continue"]
    await syscall


async def add_location_hook(location: str, line: str) -> None:
    """
    Inject a navigation option into a location (not yet wired in the engine).

    Reserved for future use.
    """
    syscall = AddLocationHookSyscall()
    syscall.location = location
    syscall.line = line
    return await syscall


async def add_character_hook(character: str, line: str) -> None:
    """
    Inject a dialogue option into an NPC's menu and wait for the player to click it.

    The option appears in the NPC's action list immediately. The quest suspends
    here until the player selects it, at which point the option is automatically
    removed and the quest resumes.

    Args:
        character: The NPC's id (e.g. "hiccup").
        line:      The button label shown to the player.
    """
    syscall = AddCharacterHookSyscall()
    syscall.character = character
    syscall.line = line
    return await syscall
