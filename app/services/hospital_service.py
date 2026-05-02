from datetime import date, datetime, timedelta

from app.models.appointment import Appointment
from app.models.owner import Owner
from app.models.patient import Patient
from app.models.user import User
from app.services.user_repository import UserRepository


class HospitalService:
    def __init__(self) -> None:
        self.owners = [
            Owner(1, "Ana Lopez", "11-5555-1234", "ana@example.com"),
            Owner(2, "Carlos Perez", "11-5555-5678", "carlos@example.com"),
        ]
        self.patients = [
            Patient(1, "Luna", "Canino", "Labrador", date(2020, 4, 12), "Ana Lopez"),
            Patient(2, "Milo", "Felino", "Europeo", date(2021, 9, 3), "Carlos Perez"),
        ]
        self.appointments = [
            Appointment(1, "Luna", "Dra. Martinez", datetime.now() + timedelta(hours=2), "Vacunacion"),
            Appointment(2, "Milo", "Dr. Gomez", datetime.now() + timedelta(days=1), "Control general"),
        ]
        self.user_repository = UserRepository()

    def get_dashboard_summary(self) -> dict:
        return {
            "owners_count": len(self.owners),
            "patients_count": len(self.patients),
            "appointments_count": len(self.appointments),
            "users_count": len(self.get_users()),
            "patients": self.patients,
            "appointments": self.appointments,
        }

    def get_users(self) -> list[User]:
        return self.user_repository.list_all()
