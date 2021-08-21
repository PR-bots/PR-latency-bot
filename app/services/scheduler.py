import sys, pathlib, asyncio, traceback
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from apscheduler.schedulers.background import BackgroundScheduler
from app.db.operators.pull_request_operator import PullRequestOperator
from app.models.scheduler import SchedulerModel
from typing import List
from app.models.trigger import PRSchedulerTrigger
from app.services.comments import return_pr_latency_schedular
from app.services.queries import query_installations
from app.utils.config_loader import ConfigLoader

class Scheduler():

    sched: BackgroundScheduler

    def __init__(self) -> None:
        try:
            self.sched = BackgroundScheduler()
            self.sched.add_job(self.job_predict_latency, 'interval', minutes=ConfigLoader().load_env()["SERVICE"]["SCHEDULER"]["CYCLE_MINUTES"])
            self.sched.start()
            print("the schedular is started.")
        except Exception as e:
            print("error with the initialization of Scheduler: %s" % (repr(e)))
            print(traceback.format_exc())

    def job_predict_latency(self) -> None:
        try:
            # query prs
            prOp = PullRequestOperator()
            tasks: List[SchedulerModel] = asyncio.run(prOp.query_prScheduler_4_scheduler())

            # the installation_id may change, so we need to use bot_slug to get app_id and then get related installation_id
            installationDict = query_installations()

            # handle each task and predict the latency
            for task in tasks:
                # if user remove the installation, we also need to remove it......
                asyncio.run(return_pr_latency_schedular(PRSchedulerTrigger(installation=installationDict[task.pr.owner.login], pr=task.pr)))
        except Exception as e:
            print("error with func job_predict_latency: %s" % (repr(e)))
            print(traceback.format_exc())