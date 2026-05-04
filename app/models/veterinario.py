from dataclasses import dataclass


@dataclass
class Veterinario:
    id: int
    nombre: str
    apellido: str
    matricula: str
    telefono: str
    email: str
    estado: bool = True
    user_id: int | None = None
