import sys, pathlib, traceback
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from typing import Optional
from app.utils.config_loader import ConfigLoader

class BaseOperator:

    engine: Optional[AsyncEngine] = None

    def __init__(self) -> None:
        try:
            env = ConfigLoader().load_env()
            url = "mysql+aiomysql://{user}:{password}@{host}:{port}/{db}".format(user=env["MYSQL"]["USER"], password=env["MYSQL"]["PASSWORD"], host=env["MYSQL"]["HOST"], port=env["MYSQL"]["PORT"], db=env["MYSQL"]["DB"])
            self.engine = create_async_engine(url, echo=True)
        except Exception as e:
            print("error with initialization of BaseOperator: %s" % (repr(e)))
            print(traceback.format_exc())