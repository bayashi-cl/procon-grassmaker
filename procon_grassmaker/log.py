from logging import addLevelName
from colorlog import ColoredFormatter


NETWORK = 21
addLevelName(NETWORK, "NETWORK")
formatter = ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "NETWORK": "blue",
        "ERROR": "red",
        "CRITICAL": "red",
    },
)
