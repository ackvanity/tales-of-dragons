"""
Packages game files.
All content is written to the content/ directory, and only then copied to data/
This is especially crucial to quests, where the game engine will catalog the
files according to SemVer versions for backwards-compatibility.
"""
import os
import shutil

class PackageException(Exception):
    """
    Raised when the game content cannot be properly packaged
    """

class QuestPackageException(PackageException):
    """
    Raised when a quest cannot be packaged
    """

class QuestVersionExistsException(QuestPackageException):
    """
    Raised when a quest to the packaged is already present and is not byte-for-byte equal.
    """

def migrate_quest(id: str, code: str, version: tuple[int, int, int], target_dir: str):
    os.makedirs(target_dir, exist_ok=True)
    file_name = target_dir + "/" + ".".join(list(map(str,version))) + ".py"
    
    if os.path.exists(file_name):
        if os.path.isfile(file_name):
            old_code = ""
            with open(file_name, "r") as f:
                old_code = f.read()
            
            if old_code != code:
                raise QuestVersionExistsException(f"Cannot write quest {id}, version {'.'.join(list(map(str,version)))}: Quest exists")
        else:
            raise FileExistsError(f"Cannot write quest file to {file_name}: Is a directory")
    else:
        with open(file_name, "w") as f:
            f.write(code)

def package():
    shutil.rmtree("data/")
    os.makedirs("data", exist_ok=True)

    # Character and locations can directly be copied
    shutil.rmtree("data/character")
    shutil.rmtree("data/location")
    shutil.copytree("content/character", "data/character")
    shutil.copytree("content/location", "data/location")

    # Migrate quests

    for quest in os.listdir("content/quest"):
        print(quest)
        if os.path.isfile("content/quest/" + quest) and quest.endswith(".py"):
            id = quest[:-3]
            
            with open(f"content/quest/{quest}", "r") as f:
                code = f.read()
                namespace: dict = {}
                exec(code, namespace)
                version: tuple[int, int, int] = namespace["VERSION"] # type: ignore
                migrate_quest(id, code, version, f"data/quest/{id}/")