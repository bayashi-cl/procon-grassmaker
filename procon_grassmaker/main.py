import argparse
import pathlib
import sys
from logging import getLogger
from pprint import pp
from typing import Dict, List

from . import atcoder, codeforces, log, util, archive, aoj

logger = getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(prog="procon-grassmaker")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--config", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    log.setup_logger(args.verbose)

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
    repo = archive.Archive(archive_dir)

    ext_info: Dict[str, str] = util.get_extention_info()

    # archive
    if "atcoder" in username:
        atcoder.archive_atcoder(username["atcoder"], archive_dir, ext_info, repo)
    if "codeforces" in username:
        codeforces.archive_codeforces(
            username["codeforces"], archive_dir, ext_info, repo
        )
    if "aizuonlinejudge" in username:
        aoj.archive_aoj(username["aizuonlinejudge"], archive_dir, ext_info, repo)

    repo.push()
    util.write_extention_info(ext_info)


if __name__ == "__main__":
    main()
