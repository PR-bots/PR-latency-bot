import sys, pathlib, datetime
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from app.models.installation import Installation
from app.models.pull_request import PullRequest
from app.models.user import User
from app.models.repository import Repository
from app.utils.time_operator import TimeOperator

from app.prediction_service.factor_getter import FactorGetter
import pytest

def test_lifetime_minutes() -> None:
    factorGetter = FactorGetter(
        pr=PullRequest(owner=User(login="zhangxunhui"), repo=Repository(name="bot-pullreq-decision"), number=5),
        installation=Installation(id=18836058)
    )
    lifetime = factorGetter.lifetime_minutes()
    assert lifetime == int((datetime.datetime.utcnow() - TimeOperator().convertTZTime2TimeStamp("2021-08-15T07:43:10Z")).total_seconds()/60)


def test_has_comments() -> None:
    factorGetter = FactorGetter(
        pr=PullRequest(owner=User(login="zhangxunhui"), repo=Repository(name="bot-pullreq-decision"), number=5),
        installation=Installation(id=18836058)
    )
    has_comments = factorGetter.has_comments()

def test_query_pr_infos() -> None:
    factorGetter = FactorGetter(
        pr=PullRequest(owner=User(login="zhangxunhui"), repo=Repository(name="bot-pullreq-decision"), number=5),
        installation=Installation(id=18836058)
    )
    result = factorGetter.query_pr_infos()
    print("pause")