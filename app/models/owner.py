from dataclasses import dataclass


@dataclass
class Owner:
    id: int
    name: str
    phone: str
    email: str
