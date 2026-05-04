from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Paciente:
    id: int
    cliente_id: int
    nombre: str
    especie: str
    raza: str
    sexo: str
    fecha_nacimiento: date
    peso: Decimal
    color: str
    estado: bool = True
