import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from app.models.pull_request import PullRequest
from app.models.user import User
from typing import Optional

class PRComment():
    pr: PullRequest
    body: str
    sender: User

    def __init__(self, pr: PullRequest, body: str, sender: Optional[User] = None) -> None:
        self.pr = pr
        self.body = body
        self.sender = sender