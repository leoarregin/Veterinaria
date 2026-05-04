from dataclasses import dataclass
from datetime import date


@dataclass
class Cliente:
    id: int
    nombre: str
    apellido: str
    dni: str
    telefono: str
    email: str
    direccion: str
    fecha_alta: date
    estado: bool = True
