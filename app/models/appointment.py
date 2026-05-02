from dataclasses import dataclass
from datetime import datetime


@dataclass
class Appointment:
    id: int
    patient_name: str
    veterinarian: str
    scheduled_at: datetime
    reason: str
