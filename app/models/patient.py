from dataclasses import dataclass
from datetime import date


@dataclass
class Patient:
    id: int
    name: str
    species: str
    breed: str
    birth_date: date
    owner_name: str
