TCSS_PATH = "tcss"

def load_tcss_file(module, name):
  path = '/'.join([TCSS_PATH, module, name]) + ".tcss"
  try:
    with open(path, "r") as file:
      return file.read()
  except FileNotFoundError:
    return "" # return nothing if file doesn't exist