from librarians.core import TCSS_DIRECTORY


def load_tcss_file(module, name):
    path = "/".join([TCSS_DIRECTORY, module, name]) + ".tcss"
    try:
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return ""  # return nothing if the styles don't exist
