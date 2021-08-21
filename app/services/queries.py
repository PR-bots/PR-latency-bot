# query github using apis
import sys, requests, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

import json, time, jwt, traceback

from typing import Dict, List
from app.models.installation import Installation
from app.models.jwt_query import JWTQuery
from app.utils.config_loader import ConfigLoader
from app.utils.global_variables import GlobalVariable

ALGORITHM = "RS256"

def query_installations() -> Dict:

    result: Dict = {}
    try:

        envConfig = ConfigLoader().load_env()
        if "APP" not in envConfig or "PRIVATE_KEY_PATH" not in envConfig['APP']:
            raise Exception("error with configuration .env.yaml")
        
        private_key_path: str = envConfig['APP']['PRIVATE_KEY_PATH']

        with open(private_key_path) as f:
            private_pem = f.read()
        
        payload = {
            "iat": int(time.time()) - 60,
            "exp": int(time.time()) + (10 * 60),
            "iss": GlobalVariable.appId
        }
        encoded_jwt = jwt.encode(payload, private_pem, algorithm=ALGORITHM)

        headers = {'Authorization': 'bearer ' + encoded_jwt, "Accept": "application/vnd.github.v3+json"}
        url = "https://api.github.com/app/installations"

        page = 1
        per_page = 100
        while(True):
            urlNew = url + "?per_page=%s&page=%s" % (per_page, page)
            response = requests.get(urlNew, headers=headers)
            if response.status_code != 200:
                raise Exception("error with func query_installations: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))
            installations = response.json()
            for installation in installations:
                result[installation["account"]["login"]] = Installation(id=installation["id"], app_id=installation["app_id"]) # installation is related to a user
            if len(installations) < per_page:
                break
            else:
                page += 1
    except Exception as e:
        print("error with func query_installations: %s" % (repr(e)))
        print(traceback.format_exc())
    finally:
        return result



def query_access_token(query: JWTQuery) -> str:
    result: str = None
    try:
        response = requests.post(query.url, headers=query.headers)
        if response.status_code != 201:
            raise Exception("error with func query_access_token: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))
        result = response.json()["token"]
    except Exception as e:
        print("error with func query_access_token: %s" % (repr(e)))
        print(traceback.format_exc())
    finally:
        return result


def query_app_id() -> int:
    try:
        result: int
        app_slug = ConfigLoader().load_env()["APP"]["APP_SLUG"]
        personal_token = ConfigLoader().load_env()["APP"]["PERSONAL_TOKEN"]
        url = "https://api.github.com/apps/{app_slug}".format(app_slug=app_slug)
        headers = {'Authorization': 'Bearer ' + personal_token, "Accept": "application/vnd.github.v3+json"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception("error with func query_app_id: code: %s, message: %s" % (response.status_code, json.loads(response.text)["message"]))
        result = response.json()["id"]
        return result
    except Exception as e:
        print("error with func query_app_id: %s" % (repr(e)))
        print(traceback.format_exc())