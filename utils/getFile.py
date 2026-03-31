import yaml
import os
from typing import List, Dict, Generator
import json


def read_file(
    file_path: str, check_empty: bool = True, is_yaml: bool = False, is_json: bool = False
) -> List[str] | Dict:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if check_empty and os.stat(file_path).st_size == 0:
        raise ValueError(f"File is empty: {file_path}")

    if is_yaml:
        with open(file_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    if is_json:
        with open(os.path.abspath(file_path)) as f:
            return json.load(f)

    with open(file_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]