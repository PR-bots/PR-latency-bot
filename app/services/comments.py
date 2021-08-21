# the services related to labels
import sys, requests, pathlib, json, asyncio, datetime, traceback
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from app.services.authentication import getToken
from app.models.pr_comment import PRComment
from app.models.trigger import *
from app.db.operators.pull_request_operator import PullRequestOperator
from app.utils.global_variables import GlobalVariable
from app.prediction_service.predictor import Predictor

LATENCY_ACCEPT = "✔️This pull request can be merged"
LATENCY_REJECT = "✖️This pull request cannot be merged"

def return_pr_latency(prTrigger: PRTrigger) -> bool:
    try:
        # insert/update db: pull_requests
        async def insert_pull_request() -> None:
            prOp = PullRequestOperator()
            await prOp.insert_pull_request(pr=prTrigger.pr, installation=prTrigger.installation)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(insert_pull_request())

        # predict the result:
        latency = Predictor(trainer=GlobalVariable.trainer, type="submission").predict(pr=prTrigger.pr, installation=prTrigger.installation)
        latency_comment = LATENCY_ACCEPT if latency else LATENCY_REJECT

        token = getToken(prTrigger.installation)
        comment = PRComment(pr=prTrigger.pr, body=latency_comment)
        headers = {'Authorization': 'token ' + token, 'Accept': 'application/vnd.github.v3+json'}
        url = "https://api.github.com/repos/{owner}/{repo}/issues/{pull_request_number}/comments".format(owner=comment.pr.owner.login, repo=comment.pr.repo.name, pull_request_number=comment.pr.number)
        data = {"body": comment.body}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code != 201:
            raise Exception("error with func return_pr_latency: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))

        comment_id = response.json()["id"]
        comment_body = comment.body
        # insert/update db: pull_requests - last_comment_at, comment_or_not
        async def update_pull_request_comment() -> None:
            prOp = PullRequestOperator()
            await prOp.update_pull_request_comment(pr=prTrigger.pr, last_comment_at=datetime.datetime.utcnow(), comment_or_not=1, comment_id=comment_id, comment_body=comment_body)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(update_pull_request_comment())
    except Exception as e:
        print("error with func return_pr_latency: %s" % (repr(e)))
        print(traceback.format_exc())


async def return_pr_latency_schedular(prSchedulerTrigger:PRSchedulerTrigger) -> bool:
    try:
        # predict the result:
        latency = Predictor(trainer=GlobalVariable.trainer, type="process").predict(pr=prSchedulerTrigger.pr, installation=prSchedulerTrigger.installation)
        latency_comment = LATENCY_ACCEPT if latency else LATENCY_REJECT

        token = getToken(prSchedulerTrigger.installation)
        comment = PRComment(pr=prSchedulerTrigger.pr, body=latency)
        headers = {'Authorization': 'token ' + token, 'Accept': 'application/vnd.github.v3+json'}
        url = "https://api.github.com/repos/{owner}/{repo}/issues/{pull_request_number}/comments".format(owner=comment.pr.owner.login, repo=comment.pr.repo.name, pull_request_number=comment.pr.number)
        data = {"body": comment.body}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code != 201:
            raise Exception("error with func return_pr_latency_schedular: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))

        comment_id = response.json()["id"]
        comment_body = comment.body
        # insert/update db: pull_requests - last_comment_at, comment_or_not
        prOp = PullRequestOperator()
        await prOp.update_pull_request_comment(pr=prSchedulerTrigger.pr, last_comment_at=datetime.datetime.utcnow(), comment_or_not=1, comment_id=comment_id, comment_body=comment_body)
    except Exception as e:
        print("error with func return_pr_latency_schedular: %s" % (repr(e)))
        print(traceback.format_exc())


if __name__ == "__main__":
    return_pr_latency()