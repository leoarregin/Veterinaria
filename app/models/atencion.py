from dataclasses import dataclass
from datetime import datetime


@dataclass
class Atencion:
    id: int
    paciente_id: int
    veterinario_id: int
    fecha_hora: datetime
    motivo_consulta: str
    sintomas: str
    diagnostico: str
    tratamiento: str
    observaciones: str
    estado: str
