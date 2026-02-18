from typing import Any
import haddock
from dragonic.base import Segment, Item, Attr, ReadAttrSyscall, WriteAttrSyscall

class Proxy:
  _path: list[Segment]

  def __init__(self):
    self._path = []

  def __getattribute__(self, name: str) -> Any:
    if not name.startswith("_"):
      prox = Proxy()
      prox._path = list(self._path)
      prox._path.append(Attr(name))
      return prox
    else:
      return object.__getattribute__(self, name)
  
  def __setattr__(self, name: str, value: Any) -> None:
    if not name.startswith("_"):
      raise RuntimeError(f"Dragonic scripts cannot directly set global state. Use .set({value.__repr()}) instead")
    else:
      object.__setattr__(self, name, value)

  def __await__(self):
    syscall = ReadAttrSyscall()
    syscall.path = self._path
    return syscall.__await__()
  
  async def set(self, value):
    syscall = WriteAttrSyscall()
    syscall.path = self.pathj
    syscall.value = value
    return await syscall

world = Proxy()