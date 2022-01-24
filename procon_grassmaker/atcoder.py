import dataclasses
import json
import pathlib
import sys
import time
from datetime import datetime
from logging import getLogger
from typing import Dict, List

import dateutil.tz
import requests
from bs4 import BeautifulSoup

from . import archive, submission, util
from .log import NETWORK

logger = getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class AtCoderSubmission(submission.Submission):
    id: int
    epoch_second: int
    problem_id: str
    contest_id: str
    user_id: str
    language: str
    point: float
    length: int
    result: str
    execution_time: int


def atcoder_api_request(username: str, sec: int) -> str:
    atcoder_api = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions"
    params = {"user": username, "from_second": str(sec)}
    logger.info(f"from {datetime.fromtimestamp(sec)}")
    logger.log(NETWORK, f"GET: {atcoder_api}")
    res = requests.get(atcoder_api, params)
    logger.log(NETWORK, f"status code: {res.status_code}")
    if res.status_code != 200:
        logger.error(f"status code {res.status_code}")
        raise util.NetworkError
    time.sleep(2)
    return res.text


def get_submissions_data(username: str) -> List[AtCoderSubmission]:
    sec = 0
    data: List[AtCoderSubmission] = []
    while True:
        res = json.loads(atcoder_api_request(username, sec))
        if not isinstance(res, list):
            raise ValueError
        if len(res) == 0:
            break
        for sub in res:
            data.append(AtCoderSubmission(**sub))
        sec = data[-1].epoch_second + 1

    return data


def get_submission_code(sub: AtCoderSubmission) -> str:
    atcoder_url = f"https://atcoder.jp/contests/{sub.contest_id}/submissions/{sub.id}"
    logger.log(NETWORK, f"GET: {atcoder_url}")
    res = requests.get(atcoder_url)
    logger.log(NETWORK, f"status code: {res.status_code}")
    if res.status_code != 200:
        logger.error(f"status code {res.status_code}")
        raise util.NetworkError
    soup = BeautifulSoup(res.text, "html.parser")
    code = soup.find(id="submission-code")
    if code is None:
        logger.error("cannot find code")
        raise util.NetworkError
    logger.debug("sucess to get code.")
    time.sleep(2)
    return code.string


def get_archive_path(
    archive_root: pathlib.Path, sub: AtCoderSubmission
) -> pathlib.Path:
    return archive_root / "atcoder" / sub.contest_id / sub.problem_id


def is_ac(sub: AtCoderSubmission) -> bool:
    return sub.result == "AC"


def is_archived(archive_root: pathlib.Path, sub: AtCoderSubmission) -> bool:
    archive_dir = get_archive_path(archive_root, sub)

    if not (archive_dir / "submissions.json").exists():
        return False
    archived_submissions = json.loads((archive_dir / "submissions.json").read_text())

    archived = False
    for archived_sub in archived_submissions:
        if sub.id == archived_sub["id"]:
            archived = True

    return archived


def archive_atcoder(
    username: str,
    archive_dir: pathlib.Path,
    ext_info: Dict[str, str],
    repo: archive.Archive,
) -> None:
    logger.info("start codeforces")
    submissions_data = get_submissions_data(username)
    archive_submissions: List[AtCoderSubmission] = []
    for sub in submissions_data:
        util.get_ext(sub.language, ext_info)
        if is_ac(sub) and not is_archived(archive_dir, sub):
            archive_submissions.append(sub)

    if len(archive_submissions) == 0:
        logger.info("No submission to archive")
        return

    print(f"Archive {len(archive_submissions)} submissions from atcoder")
    ans = input("continue? [y/n] ")
    if ans != "y":
        sys.exit()

    for sub in archive_submissions:
        name = str(sub.id) + util.get_ext(sub.language, ext_info)
        time = datetime.fromtimestamp(sub.epoch_second, tz=dateutil.tz.tzlocal())
        repo.archive(
            get_archive_path(archive_dir, sub),
            get_submission_code(sub),
            name,
            time,
            sub,
            sub.problem_id,
        )


if __name__ == "__main__":
    pass
