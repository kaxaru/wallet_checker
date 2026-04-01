import json
from pathlib import Path
from typing import Any

import yaml

from app.utils.exceptions import ConfigurationError


def _build_missing_file_error(path: Path) -> ConfigurationError:
    example_path = path.with_suffix(path.suffix + ".example")
    if example_path.exists():
        return ConfigurationError(
            f"Missing required file: {path}. Copy {example_path} to {path} and fill it in."
        )
    return ConfigurationError(f"Missing required file: {path}")


def read_file(
    file_path: str,
    check_empty: bool = True,
    is_yaml: bool = False,
    is_json: bool = False,
) -> list[str] | dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise _build_missing_file_error(path)

    if check_empty and path.stat().st_size == 0:
        raise ConfigurationError(f"File is empty: {path}")

    if is_yaml:
        with path.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    if is_json:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    with path.open("r", encoding="utf-8") as file:
        return [line.strip() for line in file]

