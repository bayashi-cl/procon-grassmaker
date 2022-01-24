import datetime
import json
import pathlib
import dataclasses
import sys
from typing import List, Any
from logging import getLogger

from git import InvalidGitRepositoryError, Repo

from . import submission

logger = getLogger(__name__)


class Archive:
    repo: Repo

    def __init__(self, path: pathlib.Path):
        try:
            self.repo = Repo(path)
            logger.info(".git dirctry found")
        except InvalidGitRepositoryError:
            logger.error("cannot find .git directory")
            print("cannot find .git directory")
            print(f"try 'git init' at {str(path)}")
            sys.exit(1)
        try:
            origin = self.repo.remotes.origin
            logger.info("pull from remote repo")
            origin.pull()
        except AttributeError:
            pass

    def archive(
        self,
        dir: pathlib.Path,
        code: str,
        name: str,
        time: datetime.datetime,
        info: submission.Submission,
        msg: str,
    ):
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)
        code_file = dir / name

        if code_file.exists():
            logger.error(f"{code_file} is already exist.")
            raise ValueError
        logger.info(f"archive code at {code_file}.")
        code_file.write_text(code)

        submissions_file = dir / "submissions.json"
        if not submissions_file.exists():
            logger.info(f"Generate {submissions_file}")
            submissions_file.touch()
            submissions_file.write_text("[]")

        logger.info(f"Load {submissions_file}")
        submissions: List[Any] = json.loads(submissions_file.read_text())
        submissions.append(dataclasses.asdict(info))
        logger.info(f"Update {submissions_file}")
        submissions_file.write_text(json.dumps(submissions))

        logger.debug(f"git add [{code_file}, {submissions_file}]")
        self.repo.index.add([str(code_file), str(submissions_file)])
        logger.info(f"git commit [{msg}, author_date={time}]")
        self.repo.index.commit(msg, author_date=time)  # type: ignore

    def push(self):
        try:
            origin = self.repo.remotes.origin
            logger.info("push to remote repo")
            origin.push()
        except AttributeError:
            pass
