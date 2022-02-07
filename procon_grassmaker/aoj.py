import dataclasses
import json
import pathlib
import sys
import time
from datetime import datetime
from logging import getLogger
from typing import Dict, List, Optional

import dateutil.tz
import pandas as pd
import requests
from dacite import from_dict

from procon_grassmaker import archive, util
from procon_grassmaker.log import NETWORK
from procon_grassmaker.serviceabc import ServiceBase
from procon_grassmaker.src.langs_aoj import languages_aoj
from procon_grassmaker.submission import SubmissionABC

logger = getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class AOJSubmission(SubmissionABC):
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


class AizuOnlineJudge(ServiceBase):
    servicename = "aizuonlinejudge"
    ext_info = languages_aoj
    id_keyname = "judgeId"

    def __init__(self, username: str, repo: archive.Archive) -> None:
        return super().__init__(username, repo)

    def aoj_api_reqest(self) -> str:
        page = 0
        size = 1000000000
        aoj_api = (
            f"https://judgeapi.u-aizu.ac.jp/submission_records/users/{self.username}"
        )
        params = {"page": str(page), "size": str(size)}
        logger.log(NETWORK, f"GET: {aoj_api}")
        res = requests.get(aoj_api, params)
        logger.log(NETWORK, f"status code: {res.status_code}")
        if res.status_code != 200:
            logger.error(f"status code {res.status_code}")
            raise util.NetworkError
        time.sleep(2)
        return res.text

    def get_submissions_data(self) -> List[AOJSubmission]:
        csv_file = csv_file = self.repo.root / "data" / "AOJ.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file)
        else:
            df = pd.DataFrame()

        data: List[AOJSubmission] = []
        res: List[Dict] = json.loads(self.aoj_api_reqest())
        for sub in reversed(res):
            data.append(from_dict(AOJSubmission, sub))

        df_after = pd.DataFrame(data)
        if len(df) != len(df_after):
            df_after.to_csv(csv_file)
            self.repo.add_commit([csv_file], "update AOJ.csv", None)

        return data

    def get_submission_code(self, sub: AOJSubmission) -> str:
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

    def is_ac(self, sub: AOJSubmission) -> bool:
        return sub.status == 4

    def get_archive_path(self, sub: AOJSubmission) -> pathlib.Path:
        return self.repo.root / "AOJ" / sub.problemId

    def get_name(self, sub: AOJSubmission) -> str:
        return str(sub.judgeId) + self.ext_info[sub.language]

    def get_messsage(self, sub: AOJSubmission) -> str:
        return str(sub.problemId)

    def get_epoch(self, sub: AOJSubmission) -> int:
        return sub.submissionDate // 1000

    def get_id(self, sub: AOJSubmission) -> int:
        return sub.judgeId

    def is_archived(self, sub: AOJSubmission) -> bool:
        return super().is_archived(sub)

    def archive(self, yes: bool) -> None:
        return super().archive(yes)
