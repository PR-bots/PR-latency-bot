# this is the authentication service
import sys, time, pathlib, traceback
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

import jwt
from app.utils.global_variables import GlobalVariable
from app.models.jwt_query import JWTQuery
from app.models.installation import Installation
from app.services.queries import query_access_token
from app.utils.config_loader import ConfigLoader

ALGORITHM = "RS256"

def getToken(installation: Installation) -> str:
    result: str = None
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
        
        # query access token of the installation
        headers = {'Authorization': 'bearer ' + encoded_jwt, "Accept": "application/vnd.github.v3+json"}
        url = "https://api.github.com/app/installations/{installation_id}/access_tokens".format(installation_id=installation.id)
        jwtQuery = JWTQuery(headers=headers, url=url)
        result = query_access_token(jwtQuery)
        
    except Exception as e:
        print("error with func getToken: %s" % repr(e))
        print(traceback.format_exc())

    finally:
        return result