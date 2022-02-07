import json
import pathlib
import sys
from typing import Any, Dict
from logging import getLogger

import toml

logger = getLogger(__name__)


def get_ext(lang: str, info: Dict[str, str]) -> str:
    if lang not in info:
        while True:
            e = input(f"Input extention of {lang}. (like '.cpp') >> ")
            if e[0] == ".":
                break
            print("start whth dot")
        info[lang] = e
    return info[lang]


config_base = """[config]
archive_dir = ''

"""
config_dir = pathlib.Path.home() / ".config" / "procon-grassmaker"
config_file = config_dir / "settings.toml"
extention_file = config_dir / "extention.json"


def init_config() -> None:
    if not config_file.exists():
        logger.info(f"Genetate config file at {config_file}")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file.touch()
        config_file.write_text(config_base)
    else:
        logger.info("Config file is already exists.")
    print(str(config_file))


def get_config() -> Any:
    if not config_file.exists():
        logger.error("cannot find config file")
        print("Config file does not exists.")
        print("Please genetate config file with command 'procon-grassmaker --init'")
        sys.exit(1)

    logger.info(f"Config file is load from {config_file}")
    return toml.loads(config_file.read_text())


class NetworkError(Exception):
    pass
