from typing import List


from typing import Dict
class JWTQuery():
    headers: Dict
    url: str

    def __init__(self, headers, url) -> None:
        self.headers = headers
        self.url = url