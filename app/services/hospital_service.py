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

    def get_veterinarios(self) -> list[User]:
        return self.user_repository.list_by_role("Veterinario")

    def search_pacientes(self, term: str) -> list[dict]:
        return self.paciente_repository.search(term)

    # 2026-05-08 leo arregin / gonza arregin: busca clientes para registro de mascota existente
    def search_clientes(self, term: str) -> list[dict]:
        return self.paciente_repository.search_clientes(term)

    def crear_cliente(
        self,
        nombre: str,
        apellido: str,
        dni: str,
        telefono: str,
        email: str,
        direccion: str,
    ) -> int:
        return self.paciente_repository.create_cliente(
            nombre, apellido, dni, telefono, email, direccion
        )

    def crear_paciente(
        self,
        cliente_id: int,
        nombre: str,
        especie: str,
        raza: str,
        fecha_nacimiento: str | None,
        sexo: str,
    ) -> int:
        return self.paciente_repository.create_paciente(
            cliente_id,
            nombre,
            especie,
            raza,
            fecha_nacimiento,
            sexo,
        )

    def crear_turno(self, data: dict) -> int:
        return self.turno_repository.create_turno(
            paciente_id=int(data["paciente_id"]),
            veterinario_id=int(data["veterinario_id"]),
            recepcionista_id=int(data.get("recepcionista_id") or 1),
            fecha_hora=data["fecha_hora"],
            motivo=data.get("motivo", ""),
            urgencia=data.get("urgencia", "normal") or "normal",
        )

    def marcar_presente(self, turno_id: int) -> None:
        self.turno_repository.marcar_presente(turno_id)

    def cancelar_turno(self, turno_id: int) -> None:
        self.turno_repository.cancelar(turno_id)

        
    def marcar_en_consulta(self, turno_id: int) -> None:
        self.turno_repository.marcar_en_consulta(turno_id)
    
    def marcar_en_pausa(self, turno_id: int) -> None:
        self.turno_repository.marcar_en_pausa(turno_id)
    
    def get_atencion_en_pausa(self, turno_id: int) -> dict | None:
        return self.turno_repository.get_atencion_en_pausa(turno_id)
    
    def guardar_atencion_pausa(self, data: dict,
                                previa: dict | None = None) -> int:
        return self.turno_repository.guardar_atencion_pausa(data, previa)
    

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

    # 2026-05-29 Leo Arregin: Métodos de servicio para consultas de reportes.
    def get_atenciones_totales_por_periodo(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        sort_by: str = "dia",
        sort_dir: str = "desc",
    ) -> list[dict]:
        return self.turno_repository.get_atenciones_totales_por_periodo(
            start_date, end_date, sort_by, sort_dir
        )

    def get_atenciones_totales_por_medico(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        sort_by: str = "total",
        sort_dir: str = "desc",
    ) -> list[dict]:
        return self.turno_repository.get_atenciones_totales_por_medico(
            start_date, end_date, sort_by, sort_dir
        )

    def get_frecuencia_atencion_por_cliente(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        sort_by: str = "atenciones",
        sort_dir: str = "desc",
    ) -> list[dict]:
        return self.turno_repository.get_frecuencia_atencion_por_cliente(
            start_date, end_date, sort_by, sort_dir
        )

    def guardar_atencion(self, data: dict, previa: dict | None = None) -> int:
        return self.turno_repository.guardar_atencion(data, previa)
