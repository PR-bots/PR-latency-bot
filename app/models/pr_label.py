from app.models.user import User
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from app.models.pull_request import PullRequest

class PRLabel():
    pr: PullRequest
    body: str