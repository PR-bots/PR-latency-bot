import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

from app.db.operators.base_operator import BaseOperator
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

@pytest.mark.asyncio
async def test_base_operator() -> None:
    baseOp = BaseOperator()
    assert type(baseOp.engine) == AsyncEngine