import dataclasses
import json
import pathlib
import time
from datetime import datetime
from logging import getLogger
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup

from procon_grassmaker import archive, util
from procon_grassmaker.log import NETWORK
from procon_grassmaker.serviceabc import ServiceBase
from procon_grassmaker.src.langs_ac import languages_atcoder
from procon_grassmaker.submission import SubmissionABC

logger = getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class AtCoderSubmission(SubmissionABC):
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


class AtCoder(ServiceBase[AtCoderSubmission]):
    servicename = "atcoder"
    ext_info = languages_atcoder
    id_keyname = "id"

    def __init__(self, username: str, repo: archive.Archive) -> None:
        super().__init__(username, repo)

    def atcoder_api_request(self, sec: int) -> str:
        atcoder_api = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions"
        params = {"user": self.username, "from_second": str(sec)}

        logger.info(f"from {datetime.fromtimestamp(sec)}")
        logger.log(NETWORK, f"GET: {atcoder_api}")
        res = requests.get(atcoder_api, params)
        logger.log(NETWORK, f"status code: {res.status_code}")

        if res.status_code != 200:
            logger.error(f"status code {res.status_code}")
            raise util.NetworkError

        time.sleep(2)
        return res.text

    def get_submissions_data(self) -> List[AtCoderSubmission]:
        csv_file = self.repo.root / "data" / "AtCoder.csv"
        sec = 0
        if csv_file.exists():
            df = pd.read_csv(csv_file)
            sec = max(df["epoch_second"]) + 1
        else:
            df = pd.DataFrame()

        new_data: List[AtCoderSubmission] = []
        while True:
            res = json.loads(self.atcoder_api_request(sec))
            if not isinstance(res, list):
                raise ValueError
            if len(res) == 0:
                break
            for sub in res:
                new_data.append(AtCoderSubmission(**sub))
            sec = new_data[-1].epoch_second + 1
        n_new_data = len(new_data)
        logger.info(f"got {n_new_data} new submissions")
        if n_new_data == 0:
            return []
        new_df = pd.DataFrame(new_data)
        new_df.sort_values(by="epoch_second")
        df_after: pd.DataFrame = pd.concat([df, new_df])
        df_after.to_csv(csv_file)
        self.repo.add_commit([csv_file], "update Atcoder.csv", None)
        return new_data

    def get_submission_code(self, sub: AtCoderSubmission) -> str:
        atcoder_url = (
            f"https://atcoder.jp/contests/{sub.contest_id}/submissions/{sub.id}"
        )
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

    def get_archive_path(self, sub: AtCoderSubmission) -> pathlib.Path:
        return self.repo.root / "atcoder" / sub.contest_id / sub.problem_id

    def get_messsage(self, sub: AtCoderSubmission) -> str:
        return sub.problem_id

    def get_epoch(self, sub: AtCoderSubmission) -> int:
        return sub.epoch_second

    def get_name(self, sub: AtCoderSubmission) -> str:
        return str(sub.id) + self.ext_info[sub.language]

    def get_id(self, sub: AtCoderSubmission) -> int:
        return sub.id

    def is_ac(self, sub: AtCoderSubmission) -> bool:
        return sub.result == "AC"

    def is_archived(self, sub: AtCoderSubmission) -> bool:
        return super().is_archived(sub)

    def archive(self, yes: bool) -> None:
        return super().archive(yes)
