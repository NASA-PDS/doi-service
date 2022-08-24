import os
import pathlib


def parse_project_root_dir() -> str:
    return str(pathlib.Path(os.path.abspath(__file__)).parent.parent)


PROJECT_ROOT_DIR = parse_project_root_dir()
