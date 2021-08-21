import sys, pathlib
from typing import Optional
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from app.models.pull_request import PullRequest
from app.models.installation import Installation
from app.models.repository import Repository
from app.models.user import User

class Trigger():
    installation: Installation

    def __init__(self, installation) -> None:
        self.installation = installation


class PRTrigger(Trigger):

    repo: Optional[Repository] = None
    sender: Optional[User] = None
    pr: PullRequest
    action: str

    def __init__(self, installation, repo, sender, pr, action) -> None:
        super(PRTrigger, self).__init__(installation)
        self.repo = repo
        self.sender = sender
        self.pr = pr
        self.action = action

class PRSchedulerTrigger(Trigger):
    pr: PullRequest

    def __init__(self, installation, pr) -> None:
        super(PRSchedulerTrigger, self).__init__(installation)
        self.pr = pr