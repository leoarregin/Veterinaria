from datetime import date, datetime

from app.models.user import User
from app.services.paciente_repository import PacienteRepository
from app.services.turno_repository import TurnoRepository
from app.services.user_repository import UserRepository


class HospitalService:
    def __init__(self) -> None:
        self.user_repository     = UserRepository()
        self.paciente_repository = PacienteRepository()
        self.turno_repository    = TurnoRepository()

    # ── dashboard ─────────────────────────────────────────────

    def get_dashboard_summary(self) -> dict:
        pacientes = self.paciente_repository.list_all()
        turnos    = self.turno_repository.get_turnos_hoy()
        return {
            "patients_count":      len(pacientes),
            "appointments_count":  len(turnos),
            "users_count":         len(self.get_users()),
            "patients":            pacientes,
            "appointments":        turnos,
        }

    # ── usuarios ──────────────────────────────────────────────

    def get_users(self) -> list[User]:
        return self.user_repository.list_all()

    # ── turnos ────────────────────────────────────────────────

    def get_turnos_hoy(self, veterinario_id: int | None = None) -> list[dict]:
        return self.turno_repository.get_turnos_hoy(veterinario_id)

    def get_turno_by_id(self, turno_id: int) -> dict | None:
        return self.turno_repository.get_by_id(turno_id)

    def marcar_presente(self, turno_id: int) -> None:
        self.turno_repository.marcar_presente(turno_id)

    def cancelar_turno(self, turno_id: int) -> None:
        self.turno_repository.cancelar(turno_id)

    def crear_turno_urgente(self, mascota_id: int, veterinario_id: int,
                         recepcionista_id: int, motivo: str = "") -> int:
        return self.turno_repository.crear_turno_urgente(
        mascota_id, veterinario_id, recepcionista_id, motivo)

    # ── pacientes ─────────────────────────────────────────────

    def get_paciente_info(self, paciente_id: int) -> dict | None:
        return self.paciente_repository.get_info_completa(paciente_id)

    # ── atenciones ────────────────────────────────────────────

    def get_historial(self, mascota_id: int) -> list[dict]:
        return self.turno_repository.get_historial(mascota_id)

    def guardar_atencion(self, data: dict) -> int:
        return self.turno_repository.guardar_atencion(data)
