import sqlite3
from datetime import date, datetime
from pathlib import Path

from app.models.atencion import Atencion


class TurnoRepository:
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
                CREATE TABLE IF NOT EXISTS turno (
                    id                  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    paciente_id         INTEGER NOT NULL,
                    veterinario_id      INTEGER NOT NULL,
                    recepcionista_id    INTEGER NOT NULL DEFAULT 1,
                    fecha_hora          TEXT    NOT NULL,
                    estado              TEXT    NOT NULL DEFAULT 'pendiente'
                                        CHECK (estado IN ('pendiente','confirmado','presente',
                                                           'atendido','cancelado','ausente',urgente)),
                    motivo              TEXT,
                    urgencia            TEXT    NOT NULL DEFAULT 'normal',
                    created_at          TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                    FOREIGN KEY (paciente_id)      REFERENCES paciente(id),
                    FOREIGN KEY (veterinario_id)   REFERENCES users(id),
                    FOREIGN KEY (recepcionista_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS atencion (
                    id              INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    turno_id        INTEGER,
                    paciente_id     INTEGER NOT NULL,
                    veterinario_id  INTEGER NOT NULL,
                    fecha_hora      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                    anamnesis       TEXT,
                    examen_fisico   TEXT,
                    diagnostico     TEXT,
                    tratamiento     TEXT,
                    observaciones   TEXT,
                    monto           REAL    NOT NULL DEFAULT 0.0,
                    temperatura_c   REAL,
                    peso_consulta_kg REAL,
                    fc_rpm           REAL,
                    fr_rpm           REAL,
                    trc_seg          REAL,
                    mucosas          TEXT,
                    condicion_corporal TEXT,
                    dolor            TEXT,
                    FOREIGN KEY (turno_id)       REFERENCES turno(id),
                    FOREIGN KEY (paciente_id)    REFERENCES paciente(id),
                    FOREIGN KEY (veterinario_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS medicacion (
                    id            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    atencion_id   INTEGER NOT NULL,
                    medicamento   TEXT    NOT NULL,
                    dosis         TEXT,
                    via           TEXT,
                    frecuencia    TEXT,
                    duracion_dias INTEGER,
                    FOREIGN KEY (atencion_id) REFERENCES atencion(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS estudio (
                    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    atencion_id INTEGER NOT NULL,
                    tipo        TEXT    NOT NULL,
                    descripcion TEXT,
                    resultado   TEXT,
                    fecha       TEXT    NOT NULL,
                    FOREIGN KEY (atencion_id) REFERENCES atencion(id) ON DELETE CASCADE
                );
            """)
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(turno)").fetchall()}
            if "urgencia" not in columns:
                conn.execute("ALTER TABLE turno ADD COLUMN urgencia TEXT NOT NULL DEFAULT 'normal'")

    # ── turnos ────────────────────────────────────────────────

    def get_turnos_hoy(self, veterinario_id: int | None = None) -> list[dict]:
        hoy = date.today().isoformat()
        query = """
            SELECT t.id, t.fecha_hora, t.estado, t.motivo, t.urgencia,
                   p.id AS paciente_id, p.nombre AS mascota,
                   p.especie, p.raza, p.peso_kg, p.sexo, p.fecha_nacimiento AS fecha_nac,
                   c.nombre || ' ' || c.apellido AS propietario,
                   c.telefono,
                   u.full_name AS veterinario,
                   u.id AS vet_id
            FROM turno t
            JOIN paciente p ON p.id = t.paciente_id
            JOIN cliente  c ON c.id = p.cliente_id
            JOIN users    u ON u.id = t.veterinario_id
            WHERE DATE(t.fecha_hora) = ?
        """
        params: list = [hoy]
        if veterinario_id:
            query += " AND t.veterinario_id = ?"
            params.append(veterinario_id)
        query += " ORDER BY CASE t.urgencia WHEN 'emergencia' THEN 1 WHEN 'urgente' THEN 2 ELSE 3 END, t.fecha_hora"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_by_id(self, turno_id: int) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT t.id, t.fecha_hora, t.estado, t.motivo, t.urgencia,
                       p.id AS paciente_id, p.nombre AS mascota,
                       p.especie, p.raza, p.peso_kg, p.sexo, p.fecha_nacimiento AS fecha_nac,
                       c.nombre || ' ' || c.apellido AS propietario,
                       c.telefono,
                       u.full_name AS veterinario,
                       u.id AS vet_id
                FROM turno t
                JOIN paciente p ON p.id = t.paciente_id
                JOIN cliente  c ON c.id = p.cliente_id
                JOIN users    u ON u.id = t.veterinario_id
                WHERE t.id = ?
            """, (turno_id,)).fetchone()
        return dict(row) if row else None

    def create_turno(
        self,
        paciente_id: int,
        veterinario_id: int,
        recepcionista_id: int,
        fecha_hora: str,
        motivo: str,
        urgencia: str = 'normal',
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO turno
                    (paciente_id, veterinario_id, recepcionista_id,
                     fecha_hora, estado, motivo, urgencia)
                VALUES (?, ?, ?, ?, 'confirmado', ?, ?)
                """,
                (paciente_id, veterinario_id, recepcionista_id, fecha_hora, motivo.strip(), urgencia),
            )
        return cur.lastrowid

    def marcar_presente(self, turno_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE turno SET estado = 'presente' WHERE id = ?",
                (turno_id,)
            )

    def marcar_atendido(self, turno_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE turno SET estado = 'atendido' WHERE id = ?",
                (turno_id,)
            )

    def cancelar(self, turno_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE turno SET estado = 'cancelado' WHERE id = ?",
                (turno_id,)
            )
     
    def crear_turno_urgente(self, mascota_id: int, veterinario_id: int,
                            recepcionista_id: int, motivo: str = "") -> int:
        """Crea un turno urgente con la hora actual."""
        from datetime import datetime
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            cur = conn.execute("""
                INSERT INTO turno
                    (paciente_id, veterinario_id, recepcionista_id,
                    fecha_hora, estado, motivo)
                VALUES (?,?,?,?,'urgente',?)
            """, (mascota_id, veterinario_id, recepcionista_id, ahora, motivo))
            return cur.lastrowid

    # ── atenciones ────────────────────────────────────────────

    def get_historial(self, paciente_id: int) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT a.id, a.fecha_hora, a.anamnesis, a.examen_fisico,
                a.diagnostico, a.tratamiento, a.observaciones,
                a.temperatura_c, a.peso_consulta_kg, a.fc_rpm, a.fr_rpm,
                a.trc_seg, a.mucosas, a.condicion_corporal, a.dolor,
                0.0 AS monto,
                u.full_name AS veterinario
                FROM atencion a
                JOIN users u ON u.id = a.veterinario_id
                WHERE a.paciente_id = ?
                ORDER BY a.fecha_hora DESC
            """, (paciente_id,)).fetchall()

        result = []
        for row in rows:
            a = dict(row)
            a["medicaciones"] = [dict(r) for r in conn.execute("""
                SELECT medicamento, dosis, via, frecuencia, duracion_dias
                FROM medicacion WHERE atencion_id = ?
            """, (a["id"],)).fetchall()]
            a["estudios"] = [dict(r) for r in conn.execute("""
                SELECT tipo, descripcion, resultado, fecha
                FROM estudio WHERE atencion_id = ?
            """, (a["id"],)).fetchall()]
            result.append(a)
        return result

    def guardar_atencion(self, data: dict) -> int:
        with self._connect() as conn:
            cur = conn.execute("""
                INSERT INTO atencion
                (turno_id, paciente_id, veterinario_id,
                anamnesis, examen_fisico, diagnostico,
                tratamiento, observaciones,
                temperatura_c, peso_consulta_kg, fc_rpm, fr_rpm,
                trc_seg, mucosas, condicion_corporal, dolor)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                data.get("turno_id"),
                data["paciente_id"],
                data["veterinario_id"],
                data.get("anamnesis", ""),
                data.get("examen_fisico", ""),
                data.get("diagnostico", ""),
                data.get("tratamiento", ""),
                data.get("observaciones", ""),
                data.get("temperatura_c")     or None,
                data.get("peso_consulta_kg")  or None,
                data.get("fc_rpm")            or None,
                data.get("fr_rpm")            or None,
                data.get("trc_seg")           or None,
                data.get("mucosas",           ""),
                data.get("condicion_corporal")or None,
                data.get("dolor")             or None,
            ))
            atencion_id = cur.lastrowid

            for m in data.get("medicaciones", []):
                if m.get("medicamento", "").strip():
                    conn.execute("""
                        INSERT INTO medicacion
                            (atencion_id, medicamento, dosis, via, frecuencia, duracion_dias)
                        VALUES (?,?,?,?,?,?)
                    """, (atencion_id, m["medicamento"], m.get("dosis", ""),
                          m.get("via", ""), m.get("frecuencia", ""),
                          m.get("duracion_dias") or None))

            for e in data.get("estudios", []):
                if e.get("tipo", "").strip():
                    conn.execute("""
                        INSERT INTO estudio
                            (atencion_id, tipo, descripcion, resultado, fecha)
                        VALUES (?,?,?,?,?)
                    """, (atencion_id, e["tipo"], e.get("descripcion", ""),
                          e.get("resultado", ""),
                          e.get("fecha", date.today().isoformat())))

            if data.get("turno_id"):
                conn.execute(
                    "UPDATE turno SET estado = 'atendido' WHERE id = ?",
                    (data["turno_id"],)
                )

        return atencion_id

    def _row_to_atencion(self, row: sqlite3.Row) -> Atencion:
        return Atencion(
            id=row["id"],
            turno_id=row["turno_id"],
            paciente_id=row["paciente_id"],
            veterinario_id=row["veterinario_id"],
            fecha_hora=datetime.fromisoformat(row["fecha_hora"]),
            anamnesis=row["anamnesis"] or "",
            examen_fisico=row["examen_fisico"] or "",
            diagnostico=row["diagnostico"] or "",
            tratamiento=row["tratamiento"] or "",
            observaciones=row["observaciones"] or "",
        )