from optparse import Option
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from app.models.user import User
from app.models.repository import Repository
from typing import Optional
from datetime import datetime

class PullRequest():
    id: int
    owner: User
    repo: Repository
    number: int
    state: str
    locked: bool
    created_at: datetime
    last_comment_at: datetime

    def __init__(self, owner, repo, number, state: Optional[str] = None, locked: Optional[bool] = None, created_at: Optional[datetime] = None, last_comment_at: Optional[datetime] = None, id: Optional[int] = None) -> None:
        self.owner = owner
        self.repo = repo
        self.number = number
        self.state = state
        self.locked = locked
        self.created_at = created_at
        self.last_comment_at = last_comment_at
        self.id = id