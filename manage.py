"""
Management script for Tales of Dragons

Commands:

package

To be added soon:

validate    - checks if the data directory is valid
    validate quests     - validates quests
    validate locations  - validates locations
    validate characters - validates characters
verify      - verifies if a file meets the format requirements
    verify save [save_path]                 - checks if the file is indeed a valid save file, by loading it in the current engine
    verify save [save_path] --format-only   - only verify formatting/syntax, disregarding the fact that some classes cannot be deserialized yet
scaffold    - an interactive wizard to create certain data entries
    scaffold quest      - creates a quest
    scaffold character  - creates a character
    scaffold location   - creates a location

BONUS: Diegetic mode!
    Create `.dragon-rider` on the project root with one line containing your name, and let's go!
    Commands work wildly different, type `hey hiccup help please` or `hey hiccup please help` for more info.
    To opt-out again, simply rename `.dragon-rider` to something else
"""

import typer
import os
from pathlib import Path
from typing import Annotated
from rich.console import Console
import librarians
import librarians.hofferson.finn
import librarians.hofferson.astrid
import librarians.ingerman
import librarians.core
from dev.package import package as _package

err_console = Console(stderr=True)
std_console = Console(stderr=False)
app = typer.Typer()

# validate = typer.Typer()

# @validate.command()
# def quests():
#     pass

# def validate_location(id: str):
#     try:
#         location = librarians.hofferson.finn.parse_location_data(librarians.core.get_data(f"location/{id}"))
#         std_console.print(f"[bold green]Success[/bold green]: Location '{id}' parsed correctly.")
#         return True
#     except Exception as e:
#         err_console.print(f"[red][b]Error[/b]: Location '{id}' cannot be parsed.[/red]")
#         return False

# @validate.command()
# def locations():
#     failure = 0
#     success = 0
#     skipped = 0
#     for location in os.listdir("content/location"):
#         if os.path.isfile("content/location/"+location) and location.endswith(".json"):
#             if validate_location(location[:-5]):
#                 success += 1
#             else:
#                 failure += 1
#         else: 
#             skipped += 1 

#     std_console.print(f"[b]Parse completed. [green]{success}[/green] parsed successfully, [red]{failure}[/red] failed to parse, [blue]{skipped}[/blue] skipped.[/b]")

# scaffold = typer.Typer()

# @scaffold.command()
# def quest():
#     raise NotImplementedError()

#     std_console.print("[b]Hi![/b]")
#     std_console.print("[i]Let's get started on writing your quest. This setup will help you get started[/i]")
#     std_console.print("[i]We will need the following details to create your quest.[/i]")
#     id = typer.prompt("Quest ID")
    
#     quest_file = """
# from dragonic.interactions import *
# from dragonic.core import *
# from dragonic.base import *

# VERSION = (1, 0, 0)

# async def main():
#     pass
# """

#     std_console.print(f"[green bold]Quest '{id}' created![/green bold]")
#     std_console.print(f"[i]The quest is saved in 'content/quest/{id}.py' and uses Python[/i]")
#     std_console.print(f"[i]You can communicate with the game world using the Dragonic API[/i]")

# @scaffold.command()
# def character():
#     pass

# app.add_typer(validate, name="validate")
# app.add_typer(scaffold, name="scaffold")

@app.command()
def package(
    headless: Annotated[
        bool,
        typer.Option(
            prompt="Perform migration? This will removing ALL files and directories in data/! THIS CANNOT BE UNDONE!",
            help="Skips confirmation. Used for CI/CD or automation",
        ),
    ],
):
    """
    Package the game files from content/ to data/
    THIS WILL DELETE EVERYTHING IN THE DATA/ DIRECTORY AND CANNOT BE UNDONE!
    """
    if not headless:
        std_console.print(f"[yellow bold]Operation cancelled by user.[/yellow bold]")
        return

    std_console.print(f"[red bold]WARN: Deleting all files in data/[/red bold]")
    _package()
    std_console.print(f"[green bold]All files migrated![/green bold]")

@app.command()
def hello():
    """
    Greet your fellow villages at Berk!
    """
    std_console.print(f"[bold]HICCUP:[/bold] Hey! How are you doing at Berk?")

if __name__ == "__main__":
    app()