from librarians import core

def get_humans() -> list[str]:
  data = core.get_data("character/human/humans")
  if not isinstance(data, list):
    raise ValueError(f"Expected list from humans data, got {type(data)}")
  return data