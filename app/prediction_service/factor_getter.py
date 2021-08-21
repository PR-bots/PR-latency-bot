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

class FactorGetter():
    pr: PullRequest
    installation: Installation
    token: str

    def __init__(self, pr: PullRequest, installation: Installation) -> None:
        self.pr = pr
        self.installation = installation
        self.token = getToken(self.installation)

    def lifetime_minutes(self):
        try:
            if self.pr.created_at is None:
                # /repos/{owner}/{repo}/pulls/{pull_number}
                headers = {'Authorization': 'token ' + self.token, 'Accept': 'application/vnd.github.v3+json'}
                url = "https://api.github.com/repos/{owner}/{repo}/pulls/{pull_request_number}".format(owner=self.pr.owner.login, repo=self.pr.repo.name, pull_request_number=self.pr.number)
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    raise Exception("error with func lifetime_minutes: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))
                self.pr.created_at = TimeOperator().convertTZTime2TimeStamp(response.json()["created_at"])
            return int((datetime.datetime.utcnow() - self.pr.created_at).total_seconds() / 60.0)
        except Exception as e:
            print("error with func lifetime_minutes: %s" % (repr(e)))
            print(traceback.format_exc())

    def has_comments(self):
        try:
            # /repos/{owner}/{repo}/issues/{issue_number}/timeline
            headers = {'Authorization': 'token ' + self.token, 'Accept': 'application/vnd.github.mockingbird-preview+json'}
            url = "https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/timeline?per_page=100".format(owner=self.pr.owner.login, repo=self.pr.repo.name, issue_number=self.pr.number)
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception("error with func has_comments: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))
            events = response.json()["created_at"]
            print("pause")
        except Exception as e:
            print("error with func has_comments: %s" % (repr(e)))
            print(traceback.format_exc())

    def query_pr_infos(self):
        try:
            # use graphql and query all the information
            '''
                1. lifetime_minutes: createdAt
                2. has_comments: issue comments: comments; pull request comment: reviews; commit comments: commits
                3. core_member: collaborators
                4. num_commits: commits-totalCount (need recrawl according to the totalCount)
                5. files_added: files-nodes (need recrawl according to the totalCount)
                6. prev_pullreqs: (depend on defaultBranchRef)
                7. open_pr_num: pullRequests (states: [OPEN]) { totalCount }
                8. account_creation_days: user-createdAt
                9. first_pr: pullRequests(baseRefName: "main") { totalCount }
                10. files_changed: changedFiles
                11. project_age: Repository-createdAt
                12. reopen_or_not: timeline-REOPENED_EVENT
                13. stars: stargazerCount
                14. description_length: bodyText
                15. followers: followers
            '''

            # first query the author:login, repo:default branch, number of changed files, number of commits; and all the attributed that do not depend on these variables
            query = """
                query {
                    repository(owner: "%s", name: "%s") {
                        pullRequest(number: %s) {
                            createdAt
                            comments { totalCount }
                            reviews (first:1, states: COMMENTED) { totalCount }
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
                        stargazerCount
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
            has_issue_comments = 1 if content["data"]["repository"]["pullRequest"]["comments"]["totalCount"] > 0 else 0
            has_pr_comments = 1 if content["data"]["repository"]["pullRequest"]["reviews"]["totalCount"] > 0 else 0
            num_commits = content["data"]["repository"]["pullRequest"]["commits"]["totalCount"]
            all_pr_num = content["data"]["repository"]["pullRequests"]["totalCount"]
            files_changed = content["data"]["repository"]["pullRequest"]["changedFiles"]
            project_age = int((datetime.datetime.utcnow() - TimeOperator().convertTZTime2TimeStamp(content["data"]["repository"]["createdAt"])).total_seconds() / 60 / 60 / 24 / 30)
            reopen_or_not = 1 if content["data"]["repository"]["pullRequest"]["timelineItems"]["totalCount"] > 0 else 0
            stars = content["data"]["repository"]["stargazerCount"]
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

            account_creation_days = int((datetime.datetime.utcnow() - TimeOperator().convertTZTime2TimeStamp(content["data"]["user"]["createdAt"])).total_seconds() / 60 / 60 / 24)
            core_member = 1 if content["data"]["repository"]["collaborators"] is not None and content["data"]["repository"]["collaborators"]["edges"][0]["permission"] != "READ" else 0
            followers = content["data"]["user"]["followers"]["totalCount"]

            # third query has_commit_comments -> has comments
            has_comments = None
            if has_issue_comments == 0 and has_pr_comments == 0:
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
                        if commit["commit"]["comments"]["totalCount"] > 0:
                            has_comments = 1
                            break
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
                            if commit["commit"]["comments"]["totalCount"] > 0:
                                has_comments = 1
                                break
                        hasNextPage = content["data"]["repository"]["pullRequest"]["commits"]["pageInfo"]["hasNextPage"]
                        endCursor = content["data"]["repository"]["pullRequest"]["commits"]["pageInfo"]["endCursor"]
                        if has_comments is not None or hasNextPage == False:
                            break

                if has_comments is None:
                    has_comments = 0
            else:
                has_comments = 1

            # fourth query files_added
            files_added = 0
            if files_changed <= 100:
                query = """
                    query {
                        repository(owner: "%s", name: "%s") {
                            pullRequest(number: %s) {
                                files (first: 100) { nodes { additions deletions } }
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
                for file in content["data"]["repository"]["pullRequest"]["files"]["nodes"]:
                    if file["additions"] > 0 and file["deletions"] == 0:
                        files_added += 1
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
                                        files (first:100) { nodes { additions deletions } pageInfo { endCursor hasNextPage } }
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
                                        files (first:100, after:"%s") { nodes { additions deletions }  pageInfo { endCursor hasNextPage } }
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

                    for file in content["data"]["repository"]["pullRequest"]["files"]["nodes"]:
                        if file["additions"] > 0 and file["deletions"] == 0:
                            files_added += 1
                    hasNextPage = content["data"]["repository"]["pullRequest"]["files"]["pageInfo"]["hasNextPage"]
                    endCursor = content["data"]["repository"]["pullRequest"]["files"]["pageInfo"]["endCursor"]
                    if hasNextPage == False:
                        break
            

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
                first_pr = 0 if prev_pullreqs > 0 else 1
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
                first_pr = 0 if prev_pullreqs > 0 else 1

            # return results
            result = {
                "lifetime_minutes": lifetime_minutes, "has_comments": has_comments, "core_member": core_member, "num_commits": num_commits, "files_added": files_added, "prev_pullreqs": prev_pullreqs, "open_pr_num": open_pr_num, "account_creation_days": account_creation_days, "first_pr": first_pr, "files_changed": files_changed, "project_age": project_age, "reopen_or_not": reopen_or_not, "stars": stars, "description_length": description_length, "followers": followers
            }

            return result

        except Exception as e:
            print("error with func query_pr_infos: %s" % (repr(e)))
            print(traceback.format_exc())

if __name__ == "__main__":
    factorGetter = FactorGetter(
        pr=PullRequest(owner=User(login="zhangxunhui"), repo=Repository(name="bot-pullreq-decision"), number=5),
        installation=Installation(id=18836058)
    )
    result = factorGetter.query_pr_infos()
    print("finish")