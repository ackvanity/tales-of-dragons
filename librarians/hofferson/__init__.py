from librarians import core

def get_humans() -> list[str]:
  return core.get_data("character/human/humans")