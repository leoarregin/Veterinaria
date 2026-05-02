from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    username: str
    full_name: str
    role: str
    status: str
    last_access: datetime
    email: str = ""
