import argparse
import pathlib
import sys
from logging import DEBUG, INFO, addLevelName, StreamHandler, getLogger
from typing import Dict, List
from pprint import pp

from . import atcoder, util, log

logger = getLogger()


def main() -> None:
    parser = argparse.ArgumentParser(prog="procon-grassmaker")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--config", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # load logger
    handler = StreamHandler()
    handler.setFormatter(log.formatter)
    logger.addHandler(handler)
    if args.verbose:
        logger.setLevel(DEBUG)
        logger.debug("--verbose is specified")
    else:
        logger.setLevel(INFO)

    # load config
    if args.init:
        logger.debug("--init is specified")
        util.init_config()
        sys.exit(0)

    if args.config:
        logger.debug("--config is specified")
        pp(util.get_config())
        sys.exit(0)

    config = util.get_config()
    username: Dict[str, str] = config["username"]
    logger.info(f"username: {username}")
    archive_dir = pathlib.Path(config["config"]["archive_dir"])
    logger.info(f"archive directry: {archive_dir}")

    ext_info: Dict[str, str] = util.get_extention_info()

    # archive
    if "atcoder" in username:
        atcoder.archive_atcoder(username["atcoder"], archive_dir, ext_info)

    util.write_extention_info(ext_info)


if __name__ == "__main__":
    main()
