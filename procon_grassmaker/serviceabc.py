import pathlib
import sys
import json
from abc import ABCMeta, abstractmethod
from datetime import datetime
from logging import getLogger
from typing import Dict, Generic, List, TypeVar

import dateutil.tz

from procon_grassmaker.submission import SubmissionABC

from . import archive

logger = getLogger(__name__)
Sub = TypeVar("Sub", bound=SubmissionABC)


class ServiceABC(Generic[Sub], metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, username: str, repo: archive.Archive) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_submissions_data(self) -> List[Sub]:
        raise NotImplementedError

    @abstractmethod
    def get_submission_code(self, sub: Sub) -> str:
        raise NotImplementedError

    @abstractmethod
    def is_ac(self, sub: Sub) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_archive_path(self, sub: Sub) -> pathlib.Path:
        raise NotImplementedError

    @abstractmethod
    def get_name(self, sub: Sub) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_messsage(self, sub: Sub) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_epoch(self, sub: Sub) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_id(self, sub: Sub) -> int:
        raise NotImplementedError

    @abstractmethod
    def is_archived(self, sub: Sub) -> bool:
        raise NotImplementedError

    @abstractmethod
    def archive(self, yes: bool) -> None:
        raise NotImplementedError


class ServiceBase(ServiceABC[Sub]):
    username: str
    repo: archive.Archive
    servicename: str
    ext_info: Dict[str, str]
    id_keyname: str

    def __init__(self, username: str, repo: archive.Archive) -> None:
        self.username = username
        self.repo = repo

    def get_submissions_data(self) -> List[Sub]:
        raise NotImplementedError

    def get_submission_code(self, sub: Sub) -> str:
        raise NotImplementedError

    def is_ac(self, sub: Sub) -> bool:
        raise NotImplementedError

    def get_archive_path(self, sub: Sub) -> pathlib.Path:
        raise NotImplementedError

    def get_messsage(self, sub: Sub) -> str:
        raise NotImplementedError

    def get_epoch(self, sub: Sub) -> int:
        raise NotImplementedError

    def get_name(self, sub: Sub) -> str:
        raise NotImplementedError

    def get_id(self, sub: Sub) -> int:
        raise NotImplementedError

    def is_archived(self, sub: Sub) -> bool:
        archive_dir = self.get_archive_path(sub)

        if not (archive_dir / "submissions.json").exists():
            return False

        archived_submissions = json.loads(
            (archive_dir / "submissions.json").read_text()
        )

        archived = False
        for archived_sub in archived_submissions:
            if self.get_id(sub) == archived_sub[self.id_keyname]:
                archived = True

        return archived

    def archive(self, yes: bool) -> None:
        logger.info(f"start {self.servicename}")
        submissions_data = self.get_submissions_data()
        archive_submissions: List[Sub] = []
        for sub in submissions_data:
            if self.is_ac(sub) and not self.is_archived(sub):
                archive_submissions.append(sub)

        if len(archive_submissions) == 0:
            logger.info("No submission to archive")
            return

        print(f"Archive {len(archive_submissions)} submissions from {self.servicename}")
        if not yes:
            ans = input("continue? [y/n] ")
            if ans != "y":
                sys.exit()

        for sub in archive_submissions:
            name = self.get_name(sub)
            time = datetime.fromtimestamp(self.get_epoch(sub), tz=dateutil.tz.tzlocal())
            self.repo.archive(
                self.get_archive_path(sub),
                self.get_submission_code(sub),
                name,
                time,
                sub,
                self.get_messsage(sub),
            )
