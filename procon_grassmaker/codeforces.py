import dataclasses
import json
import pathlib
import time
from logging import getLogger
from typing import Any, Dict, List, Optional

import dukpy
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dacite import from_dict

from procon_grassmaker import archive, util
from procon_grassmaker.log import NETWORK
from procon_grassmaker.serviceabc import ServiceBase
from procon_grassmaker.src.langs_cf import languages_codeforces
from procon_grassmaker.submission import SubmissionABC

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
class CodeforcesSubmission(SubmissionABC):
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


class CodeForeces(ServiceBase[CodeforcesSubmission]):
    servicename = "codeforces"
    ext_info = languages_codeforces
    id_keyname = "id"

    def __init__(self, username: str, repo: archive.Archive) -> None:
        return super().__init__(username, repo)

    def codeforces_api_reqest(self) -> str:
        from_ = 1
        count = 1000000000
        codeforces_api = "https://codeforces.com/api/user.status"
        params = {"handle": self.username, "from": str(from_), "count": str(count)}
        logger.log(NETWORK, f"GET: {codeforces_api}")
        res = requests.get(codeforces_api, params)
        logger.log(NETWORK, f"status code: {res.status_code}")
        if res.status_code != 200:
            logger.error(f"status code {res.status_code}")
            raise util.NetworkError
        time.sleep(2)
        return res.text

    def get_archive_path(self, sub: CodeforcesSubmission) -> pathlib.Path:
        if sub.contestId is None:
            return self.repo.root / "codeforces" / sub.problem.index
        else:
            return (
                self.repo.root / "codeforces" / str(sub.contestId) / sub.problem.index
            )

    def redirect(self, soup: BeautifulSoup) -> BeautifulSoup:
        if soup.find("body").text != "Redirecting... Please, wait.":
            logger.error("Faild to ridirect.")
            raise util.NetworkError
        scripts = soup.find_all("script")
        assert len(scripts) == 2
        url_aes = "https://codeforces.com" + scripts[0]["src"]
        aes_js = requests.get(url_aes).text

        code_js: str = scripts[1].text
        code_js = code_js.replace("document.cookie", "cookie")
        code_js = code_js.replace("document.location.href", "href")

        raw_cookie, href = dukpy.evaljs([aes_js + code_js, "[cookie, href]"])
        cookies = dict(elem.split("=") for elem in raw_cookie.split("; "))
        res = requests.get(href, cookies=cookies)
        if res.status_code != 200:
            logger.error(f"status code {res.status_code}")
            raise util.NetworkError
        return BeautifulSoup(res.text, "html.parser")

    def get_submission_code(self, sub: CodeforcesSubmission) -> str:
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
            logger.info("Failed to find code. Try ridirect...")
            soup = self.redirect(soup)
            code = soup.find(id="program-source-text")
            if code is None:
                logger.error("Redirect success, but failed to find code again.")
                raise util.NetworkError

        logger.debug("success to get code.")
        time.sleep(2)
        return code.string

    def get_submissions_data(self) -> List[CodeforcesSubmission]:
        csv_file = self.repo.root / "data" / "CodeForces.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file, index_col=0)
        else:
            df = pd.DataFrame()

        data: List[CodeforcesSubmission] = []
        res: Dict[str, Any] = json.loads(self.codeforces_api_reqest())
        if res["status"] != "OK":
            logger.error(f"codeforces api status: {res['status']}")
            logger.error(res.get("comment", ""))
            raise util.NetworkError
        for sub in reversed(res["result"]):
            data.append(from_dict(CodeforcesSubmission, sub))

        df_after = pd.DataFrame(data)
        df_after.sort_values(by="creationTimeSeconds")
        if len(df) != len(df_after):
            df_after.to_csv(csv_file)
            self.repo.add_commit([csv_file], "update CodeForces.csv", None)

        return data

    def is_ac(self, sub: CodeforcesSubmission) -> bool:
        return sub.verdict == "OK"

    def is_archived(self, sub: CodeforcesSubmission) -> bool:
        return super().is_archived(sub)

    def get_name(self, sub: CodeforcesSubmission) -> str:
        return str(sub.id) + self.ext_info[sub.programmingLanguage]

    def get_messsage(self, sub: CodeforcesSubmission) -> str:
        return str(sub.problem.index) + ": " + sub.problem.name

    def get_epoch(self, sub: CodeforcesSubmission) -> int:
        return sub.creationTimeSeconds

    def get_id(self, sub: CodeforcesSubmission) -> int:
        return sub.id

    def archive(self, yes: bool) -> None:
        return super().archive(yes)
