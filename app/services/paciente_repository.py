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

            # 2026-05-08 leo arregin / gonza arregin: migración ligera para bases existentes
            # - agrega columnas faltantes en cliente sin romper SQLite.
            cliente_cols = {row[1] for row in conn.execute("PRAGMA table_info(cliente)").fetchall()}
            if "activo" not in cliente_cols:
                conn.execute("ALTER TABLE cliente ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")
            if "created_at" not in cliente_cols:
                conn.execute("ALTER TABLE cliente ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
                conn.execute("UPDATE cliente SET created_at = datetime('now','localtime') WHERE created_at = ''")

            paciente_cols = {row[1] for row in conn.execute("PRAGMA table_info(paciente)").fetchall()}
            if "fecha_nacimiento" not in paciente_cols:
                conn.execute("ALTER TABLE paciente ADD COLUMN fecha_nacimiento TEXT")
            if "sexo" not in paciente_cols:
                conn.execute("ALTER TABLE paciente ADD COLUMN sexo TEXT NOT NULL DEFAULT 'desconocido'")
            if "peso_kg" not in paciente_cols:
                conn.execute("ALTER TABLE paciente ADD COLUMN peso_kg REAL")
            if "color" not in paciente_cols:
                conn.execute("ALTER TABLE paciente ADD COLUMN color TEXT")
            if "castrado" not in paciente_cols:
                conn.execute("ALTER TABLE paciente ADD COLUMN castrado INTEGER NOT NULL DEFAULT 0")
            if "estado" not in paciente_cols:
                conn.execute("ALTER TABLE paciente ADD COLUMN estado INTEGER NOT NULL DEFAULT 1")

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

    def search(self, term: str, limit: int = 50) -> list[dict]:
        term = term.strip().lower()
        wildcard = f"%{term}%"
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT p.id AS paciente_id,
                       p.nombre AS mascota,
                       p.especie,
                       p.raza,
                       p.sexo,
                       p.fecha_nacimiento,
                       p.peso_kg,
                       p.color,
                       c.id AS cliente_id,
                       c.nombre || ' ' || c.apellido AS propietario,
                       c.dni,
                       c.telefono,
                       c.email AS email_cliente,
                       c.direccion
                FROM paciente p
                JOIN cliente c ON c.id = p.cliente_id
                WHERE lower(p.nombre) LIKE ?
                   OR lower(c.nombre || ' ' || c.apellido) LIKE ?
                   OR lower(c.nombre) LIKE ?
                   OR lower(c.apellido) LIKE ?
                   OR lower(c.dni) LIKE ?
                   OR lower(c.telefono) LIKE ?
                ORDER BY p.nombre
                LIMIT ?
            """, [wildcard] * 6 + [limit]).fetchall()
        return [dict(r) for r in rows]

    def search_clientes(self, term: str, limit: int = 50) -> list[dict]:
        term = term.strip().lower()
        wildcard = f"%{term}%"
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT c.id AS cliente_id,
                       c.nombre || ' ' || c.apellido AS propietario,
                       c.dni,
                       c.telefono,
                       c.email,
                       c.direccion,
                       COUNT(p.id) AS mascotas
                FROM cliente c
                LEFT JOIN paciente p ON p.cliente_id = c.id
                WHERE lower(c.nombre) LIKE ?
                   OR lower(c.apellido) LIKE ?
                   OR lower(c.dni) LIKE ?
                   OR lower(c.telefono) LIKE ?
                   OR lower(c.email) LIKE ?
                GROUP BY c.id
                ORDER BY c.nombre
                LIMIT ?
            """, [wildcard] * 5 + [limit]).fetchall()
        return [dict(r) for r in rows]

    def create_cliente(
        self,
        nombre: str,
        apellido: str,
        dni: str,
        telefono: str,
        email: str,
        direccion: str,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO cliente
                    (nombre, apellido, dni, telefono, email, direccion, activo, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now','localtime'))
                """,
                (nombre.strip(), apellido.strip(), dni.strip(), telefono.strip(), email.strip(), direccion.strip()),
            )
        return cur.lastrowid

    def create_paciente(
        self,
        cliente_id: int,
        nombre: str,
        especie: str,
        raza: str,
        fecha_nacimiento: str | None,
        sexo: str,
        peso_kg: float | None = None,
        color: str = "",
        castrado: int = 0,
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO paciente
                    (cliente_id, nombre, especie, raza, fecha_nacimiento,
                     sexo, peso_kg, color, castrado, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    cliente_id,
                    nombre.strip(),
                    especie.strip(),
                    raza.strip(),
                    fecha_nacimiento.strip() if fecha_nacimiento else None,
                    sexo.strip() or 'desconocido',
                    float(peso_kg) if peso_kg else None,
                    color.strip(),
                    castrado,
                ),
            )
        return cur.lastrowid

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