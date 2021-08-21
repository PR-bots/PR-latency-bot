# used to get all factors for prediction
import sys, pathlib, requests, json, datetime, traceback
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
from app.models.pull_request import PullRequest
from app.models.installation import Installation
from app.services.authentication import getToken
from app.utils.time_operator import TimeOperator
from app.utils.word_counter import WordCounter

from app.models.installation import Installation
from app.models.pull_request import PullRequest
from app.models.user import User
from app.models.repository import Repository
from app.utils.global_variables import GlobalVariable
from app.services.queries import query_app_id

class FactorGetter():
    pr: PullRequest
    installation: Installation
    token: str

    def __init__(self, pr: PullRequest, installation: Installation) -> None:
        self.pr = pr
        self.installation = installation
        self.token = getToken(self.installation)

    def query_pr_infos(self):
        try:
            # use graphql and query all the information
            '''
                1. lifetime_minutes: createdAt (this factor is need to judge whether the predicted result is shorter than the already had lifetime)
                2. has_comments: issue comments: comments; pull request comment: reviews; commit comments: commits
                3. core_member: collaborators
                4. num_commits: commits-totalCount (need recrawl according to the totalCount)
                5. prev_pullreqs: (depend on defaultBranchRef)
                6. open_pr_num: pullRequests (states: [OPEN]) { totalCount }
                7. files_changed: changedFiles
                8. reopen_or_not: timeline-REOPENED_EVENT
                9. description_length: bodyText
                10. followers: followers
                11. num_code_comments: 
            '''

            # first query the author:login, repo:default branch, number of changed files, number of commits; and all the attributed that do not depend on these variables
            query = """
                query {
                    repository(owner: "%s", name: "%s") {
                        pullRequest(number: %s) {
                            createdAt
                            comments { totalCount }
                            reviews (states: COMMENTED) { totalCount }
                            commits { totalCount }
                            changedFiles
                            timelineItems (itemTypes: [REOPENED_EVENT]) { totalCount }
                            bodyText
                            title
                            author {
                                login
                            }
                        }
                        pullRequests { totalCount }
                        createdAt
                    }
                }
            """
            headers = {'Authorization': 'Bearer ' + self.token}
            url = "https://api.github.com/graphql"
            values = {"query": query % (self.pr.owner.login, self.pr.repo.name, self.pr.number)}
            response = requests.post(url=url, headers = headers, json=values)
            response.encoding = 'utf-8'
            if response.status_code != 200:
                raise Exception("error with func query_pr_infos: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))
            content = response.json()

            author_login = content["data"]["repository"]["pullRequest"]["author"]["login"]
            # factors
            lifetime_minutes = int((datetime.datetime.utcnow() - TimeOperator().convertTZTime2TimeStamp(content["data"]["repository"]["pullRequest"]["createdAt"])).total_seconds() / 60)
            num_issue_comments = content["data"]["repository"]["pullRequest"]["comments"]["totalCount"]
            num_pr_comments = content["data"]["repository"]["pullRequest"]["reviews"]["totalCount"]
            num_commits = content["data"]["repository"]["pullRequest"]["commits"]["totalCount"]
            all_pr_num = content["data"]["repository"]["pullRequests"]["totalCount"]
            files_changed = content["data"]["repository"]["pullRequest"]["changedFiles"]
            reopen_or_not = 1 if content["data"]["repository"]["pullRequest"]["timelineItems"]["totalCount"] > 0 else 0
            description_length = WordCounter().count([content["data"]["repository"]["pullRequest"]["bodyText"], content["data"]["repository"]["pullRequest"]["title"]])
            

            # second query factors including: account_creation_days, core_member, prev_pullreqs, first_pr, followers
            query = """
                query { 
                    repository(owner: "%s", name: "%s") {
                        collaborators (query: "%s") { edges{permission} }
                    }
                    user(login: "%s") {
                        createdAt
                        followers { totalCount }
                    }
                }
            """
            values = {"query": query % (self.pr.owner.login, self.pr.repo.name, author_login, author_login)}
            response = requests.post(url=url, headers = headers, json=values)
            response.encoding = 'utf-8'
            if response.status_code != 200:
                raise Exception("error with func query_pr_infos: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))
            content = response.json()

            core_member = 1 if content["data"]["repository"]["collaborators"] is not None and content["data"]["repository"]["collaborators"]["edges"][0]["permission"] != "READ" else 0
            followers = content["data"]["user"]["followers"]["totalCount"]

            # third query has_commit_comments -> has comments / num_code_comments
            num_commit_comments = 0 # record the number of commit comments
            if num_commits <= 100:
                query = """
                    query {
                        repository(owner: "%s", name: "%s") {
                            pullRequest(number: %s) {
                                commits (first:100) { nodes { commit { comments { totalCount } } } }
                            }
                        }
                    }
                """
                values = {"query": query % (self.pr.owner.login, self.pr.repo.name, self.pr.number)}
                response = requests.post(url=url, headers = headers, json=values)
                response.encoding = 'utf-8'
                if response.status_code != 200:
                    raise Exception("error with func query_pr_infos: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))
                content = response.json()
                for commit in content["data"]["repository"]["pullRequest"]["commits"]["nodes"]:
                    num_commit_comments += commit["commit"]["comments"]["totalCount"]
            else:
                page = 0
                endCursor = None
                while(True):
                    page += 1
                    if page == 1:
                        query = """
                            query {
                                repository(owner: "%s", name: "%s") {
                                    pullRequest(number: %s) {
                                        commits (first:100) { nodes { commit { comments { totalCount } } } pageInfo { endCursor hasNextPage } }
                                    }
                                }
                            }
                        """
                        values = {"query": query % (self.pr.owner.login, self.pr.repo.name, self.pr.number)}
                    else:
                        query = """
                            query {
                                repository(owner: "%s", name: "%s") {
                                    pullRequest(number: %s) {
                                        commits (first:100, after:"%s") { nodes { commit { comments { totalCount } } } pageInfo { endCursor hasNextPage } }
                                    }
                                }
                            }
                        """
                        values = {"query": query % (self.pr.owner.login, self.pr.repo.name, self.pr.number, endCursor)}
                    response = requests.post(url=url, headers = headers, json=values)
                    response.encoding = 'utf-8'
                    if response.status_code != 200:
                        raise Exception("error with func query_pr_infos: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))
                    content = response.json()

                    for commit in content["data"]["repository"]["pullRequest"]["commits"]["nodes"]:
                        num_commit_comments += commit["commit"]["comments"]["totalCount"]
                    hasNextPage = content["data"]["repository"]["pullRequest"]["commits"]["pageInfo"]["hasNextPage"]
                    endCursor = content["data"]["repository"]["pullRequest"]["commits"]["pageInfo"]["endCursor"]
                    if hasNextPage == False:
                        break

            has_comments = 1 if num_issue_comments + num_pr_comments + num_commit_comments > 0 else 0
            num_code_comments = num_pr_comments + num_commit_comments

            # fifth query all the pull requests for: open_pr_num, prev_pullreqs, first_pr
            open_pr_num = 0
            prev_pullreqs = 0
            if all_pr_num <= 100:
                query = """
                    query {
                        repository(owner: "%s", name: "%s") {
                            pullRequests(first: 100) {
                                nodes { author { login } state }
                            }
                        }
                    }
                """
                values = {"query": query % (self.pr.owner.login, self.pr.repo.name)}
                response = requests.post(url=url, headers = headers, json=values)
                response.encoding = 'utf-8'
                if response.status_code != 200:
                    raise Exception("error with func query_pr_infos: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))
                content = response.json()
                for prTmp in content["data"]["repository"]["pullRequests"]["nodes"]:
                    if prTmp["state"] == "OPEN":
                        open_pr_num += 1
                    if prTmp["author"]["login"] == author_login:
                        prev_pullreqs += 1
                open_pr_num = open_pr_num - 1 if open_pr_num > 0 else open_pr_num
                prev_pullreqs = prev_pullreqs - 1 if prev_pullreqs > 0 else prev_pullreqs
            else:
                page = 0
                endCursor = None
                while(True):
                    page += 1
                    if page == 1:
                        query = """
                            query {
                                repository(owner: "%s", name: "%s") {
                                    pullRequests(first: 100) {
                                        nodes { author { login } state }
                                        pageInfo { endCursor hasNextPage }
                                    }
                                }
                            }
                        """
                        values = {"query": query % (self.pr.owner.login, self.pr.repo.name)}
                    else:
                        query = """
                            query {
                                repository(owner: "%s", name: "%s") {
                                    pullRequests(first: 100, after: "%s") {
                                        nodes { author { login } state }
                                        pageInfo { endCursor hasNextPage }
                                    }
                                }
                            }
                        """
                        values = {"query": query % (self.pr.owner.login, self.pr.repo.name, endCursor)}
                    response = requests.post(url=url, headers = headers, json=values)
                    response.encoding = 'utf-8'
                    if response.status_code != 200:
                        raise Exception("error with func query_pr_infos: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))
                    content = response.json()

                    for prTmp in content["data"]["repository"]["pullRequests"]["nodes"]:
                        if prTmp["state"] == "OPEN":
                            open_pr_num += 1
                        if prTmp["author"]["login"] == author_login:
                            prev_pullreqs += 1
                    hasNextPage = content["data"]["repository"]["pullRequests"]["pageInfo"]["hasNextPage"]
                    endCursor = content["data"]["repository"]["pullRequests"]["pageInfo"]["endCursor"]
                    if hasNextPage == False:
                        break
                open_pr_num = open_pr_num - 1 if open_pr_num > 0 else open_pr_num
                prev_pullreqs = prev_pullreqs - 1 if prev_pullreqs > 0 else prev_pullreqs

            # return results
            result = {
                "lifetime_minutes": lifetime_minutes, "has_comments": has_comments, "core_member": core_member, "num_commits": num_commits, "prev_pullreqs": prev_pullreqs, "open_pr_num": open_pr_num, "files_changed": files_changed, "reopen_or_not": reopen_or_not, "description_length": description_length, "followers": followers, "num_code_comments": num_code_comments
            }

            return result

        except Exception as e:
            print("error with func query_pr_infos: %s" % (repr(e)))
            print(traceback.format_exc())

if __name__ == "__main__":
    GlobalVariable.appId = query_app_id()
    factorGetter = FactorGetter(
        pr=PullRequest(owner=User(login="zhangxunhui"), repo=Repository(name="bot-pullreq-decision"), number=23),
        installation=Installation(id=18992641)
    )
    result = factorGetter.query_pr_infos()
    print("finish")