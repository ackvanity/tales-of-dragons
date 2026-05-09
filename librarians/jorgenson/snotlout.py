from librarians.core import DATA_DIRECTORY
import os

def version_compatible(save_version: tuple[int, int, int], code_version: tuple[int, int, int]):
    if save_version[0] != code_version[0]:
        return False
    
    if save_version[1] > code_version[1]:
        return False

    return True

def version_newer(new_version, old_version):
    if new_version[0] > old_version[0]:
        return True
    if new_version[0] < old_version[0]:
        return False

    if new_version[1] > old_version[1]:
        return True
    if new_version[1] < old_version[1]:
        return False

    if new_version[2] > old_version[2]:
        return True
    if new_version[2] < old_version[2]:
        return False


def get_quest(id: str, save_version: tuple[int, int, int] | None) -> tuple[str, tuple[int, int, int]]:
    dir = f"quest/{id}"

    valid_versions = []

    for quest in os.listdir(DATA_DIRECTORY + "/" + dir):
        parts = quest.split(".")
        code_version = (int(parts[0]), int(parts[1]), int(parts[2]))
        
        if save_version is None or version_compatible(save_version, code_version):
            valid_versions.append(code_version)
    
    if not len(valid_versions):
        raise Exception("No valid version exists!")

    used_version = valid_versions[0]

    for version in valid_versions:
        if version_newer(version, used_version):
            used_version = version
    
    return (dir + "/" + ".".join(map(str,used_version)), used_version)