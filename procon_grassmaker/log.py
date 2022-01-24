import logging
from colorlog import ColoredFormatter


NETWORK = 21


def setup_logger(verbose: bool) -> None:
    logging.addLevelName(NETWORK, "NETWORK")
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
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    if verbose:
        logging.basicConfig(level=logging.DEBUG, handlers=[handler])
    else:
        logging.basicConfig(level=logging.INFO, handlers=[handler])
