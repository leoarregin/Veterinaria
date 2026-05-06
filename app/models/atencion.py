from dataclasses import dataclass
from datetime import datetime


@dataclass
class Atencion:
    id: int
    turno_id: int
    paciente_id: int
    veterinario_id: int
    fecha_hora: datetime
    anamnesis: str
    examen_fisico: str
    diagnostico: str
    tratamiento: str
    observaciones: str
    
