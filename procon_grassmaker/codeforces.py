import dataclasses
import json
import pathlib
import sys
import time
from datetime import datetime
from logging import getLogger
from typing import Dict, List, Optional, Any

import dateutil.tz
import requests
from bs4 import BeautifulSoup
from dacite import from_dict

from . import archive, submission, util
from .log import NETWORK

logger = getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class CodeforcesMember:
    handle: str
    name: Optional[str]


@dataclasses.dataclass(frozen=True)
class CodeforcesParty:
    contestId: Optional[int]
    members: List[CodeforcesMember]
    participantType: str
    teamId: Optional[int]
    teamName: Optional[str]
    ghost: bool
    room: Optional[int]
    startTimeSeconds: Optional[int]


@dataclasses.dataclass(frozen=True)
class CodeforcesProblem:
    contestId: Optional[int]
    problemsetName: Optional[str]
    index: str
    name: str
    type: str
    points: Optional[float]
    rating: Optional[int]
    tags: List[str]


@dataclasses.dataclass(frozen=True)
class CodeforcesSubmission(submission.Submission):
    id: int
    contestId: Optional[int]
    creationTimeSeconds: int
    relativeTimeSeconds: int
    problem: CodeforcesProblem
    author: CodeforcesParty
    programmingLanguage: str
    verdict: Optional[str]
    testset: str
    passedTestCount: int
    timeConsumedMillis: int
    memoryConsumedBytes: int
    points: Optional[float]


def codeforces_api_reqest(username: str) -> str:
    count = 1000000000
    from_ = 1
    codeforces_api = "https://codeforces.com/api/user.status"
    params = {"handle": username, "from": str(from_), "count": str(count)}
    logger.log(NETWORK, f"GET: {codeforces_api}")
    res = requests.get(codeforces_api, params)
    logger.log(NETWORK, f"status code: {res.status_code}")
    if res.status_code != 200:
        logger.error(f"status code {res.status_code}")
        raise util.NetworkError
    time.sleep(2)
    return res.text


def get_submissions_data(username: str) -> List[CodeforcesSubmission]:
    data: List[CodeforcesSubmission] = []
    res: Dict[str, Any] = json.loads(codeforces_api_reqest(username))
    if res["status"] != "OK":
        logger.error(f"codeforces api status: {res['status']}")
        logger.error(f"{res.get('comment','')}")
        raise util.NetworkError
    for sub in reversed(res["result"]):
        data.append(from_dict(CodeforcesSubmission, sub))
    return data


def get_submission_code(sub: CodeforcesSubmission) -> str:
    codeforces_url = (
        f"https://codeforces.com/contest/{sub.contestId}/submission/{sub.id}"
    )
    logger.log(NETWORK, f"GET: {codeforces_url}")
    res = requests.get(codeforces_url)
    logger.log(NETWORK, f"status code: {res.status_code}")
    if res.status_code != 200:
        logger.error(f"status code {res.status_code}")
        raise util.NetworkError
    soup = BeautifulSoup(res.text, "html.parser")
    code = soup.find(id="program-source-text")
    if code is None:
        logger.error("cannot find code")
        raise util.NetworkError
    logger.debug("sucess to get code.")
    time.sleep(2)
    return code.string


def is_ac(sub: CodeforcesSubmission) -> bool:
    return sub.verdict == "OK"


def get_archive_path(
    archive_root: pathlib.Path, sub: CodeforcesSubmission
) -> pathlib.Path:
    if sub.contestId is None:
        return archive_root / "codeforces" / sub.problem.index
    else:
        return archive_root / "codeforces" / str(sub.contestId) / sub.problem.index


def is_archived(archive_root: pathlib.Path, sub: CodeforcesSubmission) -> bool:
    archive_dir = get_archive_path(archive_root, sub)

    if not (archive_dir / "submissions.json").exists():
        return False
    archived_submissions = json.loads((archive_dir / "submissions.json").read_text())

    archived = False
    for archived_sub in archived_submissions:
        if sub.id == archived_sub["id"]:
            archived = True

    return archived


def archive_codeforces(
    username: str,
    archive_dir: pathlib.Path,
    ext_info: Dict[str, str],
    repo: archive.Archive,
) -> None:
    logger.info("start codeforces")
    submissions_data = get_submissions_data(username)
    archive_submissions: List[CodeforcesSubmission] = []
    for sub in submissions_data:
        util.get_ext(sub.programmingLanguage, ext_info)
        if is_ac(sub) and not is_archived(archive_dir, sub):
            archive_submissions.append(sub)

    if len(archive_submissions) == 0:
        logger.info("No submission to archive")
        return

    print(f"Archive {len(archive_submissions)} submissions from codeforces")
    ans = input("continue? [y/n] ")
    if ans != "y":
        sys.exit()

    for sub in archive_submissions:
        name = str(sub.id) + util.get_ext(sub.programmingLanguage, ext_info)
        time = datetime.fromtimestamp(sub.creationTimeSeconds, tz=dateutil.tz.tzlocal())
        repo.archive(
            get_archive_path(archive_dir, sub),
            get_submission_code(sub),
            name,
            time,
            sub,
            str(sub.problem.index) + ": " + sub.problem.name,
        )
