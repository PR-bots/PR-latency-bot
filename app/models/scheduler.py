import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from app.models.installation import Installation
from app.models.pull_request import PullRequest

class SchedulerModel():
    installation: Installation

    def __init__(self, installation: Installation) -> None:
        self.installation = installation

class PRScheduler(SchedulerModel):
    pr: PullRequest

    def __init__(self, installation: Installation, pr: PullRequest) -> None:
        super().__init__(installation)
        self.pr = pr