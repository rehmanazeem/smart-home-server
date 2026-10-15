from . import *

def resource_path(relative_path: str) -> str:
    """
    Get the absolute path to the resource file, works for dev and for PyInstaller executable.
    The base path is set relative to this file's location.
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        # Use the directory of the main script if available, else fallback to this file
        if hasattr(sys, 'frozen'):
            base_path = os.path.dirname(sys.executable)
        elif hasattr(sys, 'argv') and sys.argv and os.path.isfile(sys.argv[0]):
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def read_file(path: str) -> str:
    """Read and return the contents of a file."""
    with open(resource_path(os.path.join(path)), 'r', encoding='utf-8') as file:
        return file.read()
    
def write_file(path: str, content: str) -> None:
    """Write content to a file."""
    with open(resource_path(os.path.join(path)), 'w', encoding='utf-8') as file:
        file.write(content)

def read_yaml_file(path: str | list) -> dict:
    """
    ----------------------------------------------------------------------------------
    Reads a YAML file from the specified path and returns its contents as a dictionary.
    ----------------------------------------------------------------------------------
    Args:
        path (str or list): The file path to the YAML file.

    Returns:
        dict: The contents of the YAML file parsed into a Python dictionary.

    Note:
        If 'path' is provided as a list, it will be joined into a single path string.
    ----------------------------------------------------------------------------------
    """

    if isinstance(path, list):
        path = os.path.join(*path)

    with open(resource_path(os.path.join(path)), 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def write_yaml_file(path: str | list, data: dict) -> None:
    """
    ----------------------------------------------------------------------------------
    Write a dictionary to a YAML file.
    ----------------------------------------------------------------------------------
    Args:
        path (str): The file path where the YAML file will be written.
        data (dict): The dictionary containing data to write to the YAML file.
    ----------------------------------------------------------------------------------
    """
    if isinstance(path, list):
        path = os.path.join(*path)

    with open(resource_path(os.path.join(path)), 'w', encoding='utf-8') as file:
        for k,v in data.items():
            yaml.dump({k: v}, file, default_flow_style=False)
            file.write('\n')

def update_yaml_file(path: str | list, key: str, data: dict) -> None:
    """
    ----------------------------------------------------------------------------------
    Update a YAML file with the contents of a dictionary for a specific key.
    ----------------------------------------------------------------------------------
    Args:
        path (str): The path to the YAML file.
        key (str): The key in the YAML file to update.
        data (dict): The dictionary data to update for the given key.
    ----------------------------------------------------------------------------------
    """
    if isinstance(path, list):
        path = os.path.join(*path)

    existing_data = read_yaml_file(path)
    for k, v in existing_data.items():
        if k == key:
            existing_data[k] = data
    write_yaml_file(path, existing_data)
