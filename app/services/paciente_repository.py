import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.models.paciente import Paciente


class PacienteRepository:
    def __init__(self, db_path: str | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        self.db_path = Path(db_path) if db_path else base_dir / "hospital_veterinario.db"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS cliente (
                    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    nombre      TEXT    NOT NULL,
                    apellido    TEXT    NOT NULL,
                    dni         TEXT    UNIQUE,
                    telefono    TEXT,
                    email       TEXT,
                    direccion   TEXT,
                    activo      INTEGER NOT NULL DEFAULT 1,
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS paciente (
                    id               INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    cliente_id       INTEGER NOT NULL,
                    nombre           TEXT    NOT NULL,
                    especie          TEXT    NOT NULL,
                    raza             TEXT,
                    fecha_nacimiento TEXT,
                    sexo             TEXT    NOT NULL DEFAULT 'desconocido'
                                     CHECK (sexo IN ('M','F','desconocido')),
                    peso_kg          REAL,
                    color            TEXT,
                    castrado         INTEGER NOT NULL DEFAULT 0,
                    estado           INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (cliente_id) REFERENCES cliente(id)
                );
            """)

    # ── pacientes ─────────────────────────────────────────────

    def list_all(self) -> list[Paciente]:
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT p.*, c.nombre || ' ' || c.apellido AS propietario,
                       c.telefono, c.email AS email_cliente
                FROM paciente p
                JOIN cliente c ON c.id = p.cliente_id
                WHERE p.estado = 1
                ORDER BY p.nombre
            """).fetchall()
        return [self._row_to_paciente(r) for r in rows]

    def get_by_id(self, paciente_id: int) -> Paciente | None:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT p.*, c.nombre || ' ' || c.apellido AS propietario,
                       c.telefono, c.email AS email_cliente
                FROM paciente p
                JOIN cliente c ON c.id = p.cliente_id
                WHERE p.id = ?
            """, (paciente_id,)).fetchone()
        return self._row_to_paciente(row) if row else None

    def get_info_completa(self, paciente_id: int) -> dict | None:
        """Devuelve dict con todos los campos para los templates."""
        with self._connect() as conn:
            row = conn.execute("""
                SELECT p.*, c.nombre || ' ' || c.apellido AS propietario,
                       c.telefono, c.email AS email_cliente
                FROM paciente p
                JOIN cliente c ON c.id = p.cliente_id
                WHERE p.id = ?
            """, (paciente_id,)).fetchone()
        return dict(row) if row else None

    def _row_to_paciente(self, row: sqlite3.Row) -> Paciente:
        return Paciente(
            id=row["id"],
            cliente_id=row["cliente_id"],
            nombre=row["nombre"],
            especie=row["especie"],
            raza=row["raza"] or "",
            sexo=row["sexo"],
            fecha_nacimiento=date.fromisoformat(row["fecha_nacimiento"])
                             if row["fecha_nacimiento"] else date.today(),
            peso_kg=Decimal(str(row["peso_kg"])) if row["peso_kg"] else Decimal("0"),
            color=row["color"] or "",
            castrado=row["castrado"],
            estado=row["estado"],
        )