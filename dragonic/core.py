import haddock

class Player(haddock.Entity):
  name: str
  health: int = 100

  def __init__(self, name):
    self.name = name

player: Player