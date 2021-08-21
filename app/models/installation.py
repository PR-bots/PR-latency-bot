from typing import Optional
class Installation():
    id: int
    app_id: Optional[int] = None


    def __init__(self, id, app_id: Optional[int]=None) -> None:
        self.id = id
        self.app_id = app_id