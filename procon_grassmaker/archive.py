import datetime
import json
import pathlib
import dataclasses
import sys
from typing import List, Any, Optional, Dict
from logging import getLogger

from git import InvalidGitRepositoryError, Repo
import dateutil.tz
import toml

# from . import submission
from procon_grassmaker.submission import SubmissionABC

logger = getLogger(__name__)


class Archive:
    repo: Repo
    root: pathlib.Path

    def __init__(self, path: pathlib.Path):
        self.root = path
        try:
            self.repo = Repo(path)
            logger.info(".git dirctry found")
        except InvalidGitRepositoryError:
            logger.error("cannot find .git directory")
            print("cannot find .git directory")
            print(f"try 'git init' at {str(path)}")
            sys.exit(1)
        logger.info("git repository found")
        try:
            origin = self.repo.remotes.origin
            logger.info("pull from remote repo")
            origin.pull()
        except AttributeError:
            pass

        if not (path / "data").exists():
            (path / "data").mkdir()

    def get_usernames(self) -> Dict[str, str]:
        config_file = self.root / ".grassmaker" / "config.toml"
        if not config_file.exists():
            raise ValueError

        config = toml.loads(config_file.read_text())
        return config["username"]

    def archive(
        self,
        dir: pathlib.Path,
        code: str,
        name: str,
        time: datetime.datetime,
        info: SubmissionABC,
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
        self.add_commit([code_file, submissions_file], msg, time)

    def add_commit(
        self, files: List[pathlib.Path], msg: str, time: Optional[datetime.datetime]
    ) -> None:
        if time is None:
            time = datetime.datetime.now(tz=dateutil.tz.tzlocal())
        logger.info("git add :")
        for f in files:
            logger.info(f" - {f}")
        files_str = [str(f) for f in files]
        self.repo.index.add(files_str)
        logger.info(f"git commit {msg}, author_date={time}")
        self.repo.index.commit(msg, author_date=time)  # type: ignore

    def push(self):
        try:
            origin = self.repo.remotes.origin
            logger.info("push to remote repo")
            origin.push()
        except AttributeError:
            pass
