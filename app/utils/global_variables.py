import aiomysql
from typing import Optional

class GlobalVariable():

    dbPool: Optional[aiomysql.pool.Pool] = None
    trainer = None # the models for predicting pull request latency
    appId: int