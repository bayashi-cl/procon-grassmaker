import dataclasses
import json
import pathlib
import sys
import time
from datetime import datetime
from logging import getLogger
from typing import Dict, List, Optional

import dateutil.tz
import requests
from dacite import from_dict

from . import archive, submission, util
from .log import NETWORK

logger = getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class AOJSubmission(submission.Submission):
    judgeId: int
    judgeType: int
    userId: str
    problemId: str
    submissionDate: int
    language: str
    status: int
    cpuTime: int
    memory: int
    codeSize: int
    accuracy: str
    judgeDate: int
    score: int
    problemTitle: Optional[str]
    token: Optional[str]


@dataclasses.dataclass(frozen=True)
class AOJSolution:
    judgeId: int
    userId: str
    problemId: str
    language: str
    cpuTime: int
    memory: int
    submissionDate: int
    policy: str
    sourceCode: str
    reviewed: int


def aoj_api_reqest(username: str) -> str:
    page = 0
    size = 1000000000
    aoj_api = f"https://judgeapi.u-aizu.ac.jp/submission_records/users/{username}"
    params = {"page": str(page), "size": str(size)}
    logger.log(NETWORK, f"GET: {aoj_api}")
    res = requests.get(aoj_api, params)
    logger.log(NETWORK, f"status code: {res.status_code}")
    if res.status_code != 200:
        logger.error(f"status code {res.status_code}")
        raise util.NetworkError
    time.sleep(2)
    return res.text


def get_submissions_data(username: str) -> List[AOJSubmission]:
    data: List[AOJSubmission] = []
    res: List[Dict] = json.loads(aoj_api_reqest(username))
    for sub in reversed(res):
        data.append(from_dict(AOJSubmission, sub))
    return data


def get_submission_code(sub: AOJSubmission) -> str:
    aoj_url = f"https://judgeapi.u-aizu.ac.jp/reviews/{sub.judgeId}"
    logger.log(NETWORK, f"GET: {aoj_url}")
    res = requests.get(aoj_url)
    logger.log(NETWORK, f"status code: {res.status_code}")
    if res.status_code != 200:
        logger.error(f"status code {res.status_code}")
        raise util.NetworkError
    sol = from_dict(AOJSolution, json.loads(res.text))
    time.sleep(2)
    return sol.sourceCode


def is_ac(sub: AOJSubmission) -> bool:
    return sub.status == 4


def get_archive_path(archive_root: pathlib.Path, sub: AOJSubmission) -> pathlib.Path:
    return archive_root / "AOJ" / sub.problemId


def is_archived(archive_root: pathlib.Path, sub: AOJSubmission) -> bool:
    archive_dir = get_archive_path(archive_root, sub)

    if not (archive_dir / "submissions.json").exists():
        return False
    archived_submissions = json.loads((archive_dir / "submissions.json").read_text())

    archived = False
    for archived_sub in archived_submissions:
        if sub.judgeId == archived_sub["judgeId"]:
            archived = True

    return archived


def archive_aoj(
    username: str,
    archive_dir: pathlib.Path,
    ext_info: Dict[str, str],
    repo: archive.Archive,
) -> None:
    logger.info("start AOJ")
    submissions_data = get_submissions_data(username)
    archive_submissions: List[AOJSubmission] = []
    for sub in submissions_data:
        util.get_ext(sub.language, ext_info)
        if is_ac(sub) and not is_archived(archive_dir, sub):
            archive_submissions.append(sub)

    if len(archive_submissions) == 0:
        logger.info("No submission to archive")
        return

    print(f"Archive {len(archive_submissions)} submissions from AOJ")
    ans = input("continue? [y/n] ")
    if ans != "y":
        sys.exit()

    for sub in archive_submissions:
        name = str(sub.judgeId) + util.get_ext(sub.language, ext_info)
        time = datetime.fromtimestamp(
            sub.submissionDate // 1000, tz=dateutil.tz.tzlocal()
        )
        repo.archive(
            get_archive_path(archive_dir, sub),
            get_submission_code(sub),
            name,
            time,
            sub,
            str(sub.problemId),
        )
