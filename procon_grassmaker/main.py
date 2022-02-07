import argparse
import pathlib
import sys
from logging import getLogger
from pprint import pp
from typing import Dict, List

from . import archive, atcoder, codeforces, log, util, aoj

logger = getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(prog="procon-grassmaker")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--config", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--dir", type=pathlib.Path)
    parser.add_argument("--yes", "-y", action="store_true")
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

    archive_dir: pathlib.Path
    if args.dir is None:
        config = util.get_config()
        archive_dir = pathlib.Path(config["config"]["archive_dir"])
    else:
        archive_dir = args.dir

    if not archive_dir.exists():
        logger.error(f"{archive_dir} not found")
        sys.exit(1)
    logger.info("archive directory found")

    repo = archive.Archive(archive_dir)
    username = repo.get_usernames()

    # archive
    if "atcoder" in username:
        ac = atcoder.AtCoder(username["atcoder"], repo)
        ac.archive(args.yes)

    if "codeforces" in username:
        cf = codeforces.CodeForeces(username["codeforces"], repo)
        cf.archive(args.yes)

    if "aizuonlinejudge" in username:
        aoj_ = aoj.AizuOnlineJudge(username["aizuonlinejudge"], repo)
        aoj_.archive(args.yes)

    repo.push()


if __name__ == "__main__":
    main()
