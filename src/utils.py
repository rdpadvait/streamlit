import json
import os
from typing import Any, List, Union

from logger import logger


def clean_path(path: Union[str, List[str]]):
    logger.info(f"Cleaning path: {path}")
    paths = [path] if isinstance(path, str) else path
    paths = [os.path.abspath(p) for p in paths]
    for p in paths:
        if p and os.path.exists(p):
            os.remove(p)
        os.makedirs(os.path.dirname(p), exist_ok=True)


def read(file_path: str, verbose: bool = False):
    logger.info(f"Reading file: {file_path}")
    print(f"Reading {file_path}") if verbose else None
    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    elif file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = f.read().splitlines()
    else:
        logger.error(f"File type not supported: {file_path}")
        raise ValueError(f"File type not supported: {file_path}")
    return data


def write(file_path: str, data: Any, verbose: bool = True):
    logger.info(f"Writing to file: {file_path}")
    if file_path.endswith(".json"):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    elif file_path.endswith(".txt"):
        with open(file_path, "w", encoding="utf-8") as f:
            print(data, file=f)
    else:
        logger.error(f"File type not supported: {file_path}")
        raise ValueError(f"File type not supported: {file_path}")
    print(f"Wrote to {file_path}") if verbose else None
