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
                                                           'atendido','cancelado','ausente')),
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

    def get_turnos_hoy(self, veterinario_id=None) -> list[dict]:
        hoy = date.today().isoformat()
        query = """
            SELECT t.id, t.fecha_hora, t.estado, t.motivo, t.urgencia,
                p.id AS paciente_id, p.nombre AS mascota,
                p.especie, p.raza, p.peso_kg, p.sexo,
                p.fecha_nacimiento AS fecha_nac,
                c.nombre || ' ' || c.apellido AS propietario,
                c.telefono,
                u.full_name AS veterinario,
                u.id AS vet_id
            FROM turno t
            JOIN paciente p ON p.id = t.paciente_id
            JOIN cliente  c ON c.id = p.cliente_id
            JOIN users    u ON u.id = t.veterinario_id
            WHERE DATE(t.fecha_hora) = ?
            AND t.estado NOT IN ('cancelado','ausente')
        """
        params = [hoy]
        if veterinario_id:
            query += " AND t.veterinario_id = ?"
            params.append(veterinario_id)
    
        # ordenar: emergencia primero, urgente segundo, normal último
        # dentro de cada grupo por hora
        query += """
            ORDER BY
                CASE t.urgencia
                    WHEN 'emergencia' THEN 1
                    WHEN 'urgente'    THEN 2
                    ELSE                   3
                END,
                CASE t.estado
                    WHEN 'en_pausa'    THEN 1
                    WHEN 'en_consulta' THEN 2
                    WHEN 'presente'    THEN 3
                    WHEN 'confirmado'  THEN 4
                    WHEN 'pendiente'   THEN 5
                    ELSE                    6
                END,
                t.fecha_hora
        """
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    
    
    def get_by_id(self, turno_id: int) -> dict | None:
        with self._connect() as conn:
            row = self._connect().execute("""
                SELECT t.id, t.fecha_hora, t.estado, t.motivo, t.urgencia,
                    p.id AS paciente_id, p.nombre AS mascota,
                    p.especie, p.raza, p.peso_kg, p.sexo,
                    p.fecha_nacimiento AS fecha_nac,
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

    def marcar_en_consulta(self, turno_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE turno SET estado = 'en_consulta' WHERE id = ?",
                (turno_id,)
            )
 
    def marcar_en_pausa(self, turno_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE turno SET estado = 'en_pausa' WHERE id = ?",
                (turno_id,)
            )
    
    def get_atencion_en_pausa(self, turno_id: int) -> dict | None:
        """Devuelve la atención en pausa de un turno si existe."""
        with self._connect() as conn:
            row = conn.execute("""
                SELECT a.*,
                    GROUP_CONCAT(
                        m.medicamento || '|' || COALESCE(m.dosis,'') || '|' ||
                        COALESCE(m.via,'') || '|' || COALESCE(m.frecuencia,'') || '|' ||
                        COALESCE(CAST(m.duracion_dias AS TEXT),''),
                        ';;'
                    ) AS meds_raw
                FROM atencion a
                LEFT JOIN medicacion m ON m.atencion_id = a.id
                WHERE a.turno_id = ? AND a.estado = 'en_pausa'
                GROUP BY a.id
                ORDER BY a.fecha_hora DESC
                LIMIT 1
            """, (turno_id,)).fetchone()
    
            if not row:
                return None
    
            a = dict(row)
    
            # recuperar medicaciones
            meds = []
            if a.get("meds_raw"):
                for item in a["meds_raw"].split(";;"):
                    parts = item.split("|")
                    if len(parts) == 5 and parts[0].strip():
                        meds.append({
                            "medicamento":  parts[0],
                            "dosis":        parts[1],
                            "via":          parts[2],
                            "frecuencia":   parts[3],
                            "duracion_dias":parts[4],
                        })
            a["medicaciones"] = meds
    
            # recuperar estudios
            estudios = conn.execute("""
                SELECT tipo, descripcion, resultado, fecha
                FROM estudio WHERE atencion_id = ?
            """, (a["id"],)).fetchall()
            a["estudios"] = [dict(e) for e in estudios]
    
            return a
    
    
    def guardar_atencion_pausa(self, data: dict,
                                previa: dict | None = None) -> int:
        """
        Guarda o actualiza una atención con estado 'en_pausa'.
        Si existe una atención previa en pausa la actualiza,
        si no existe crea una nueva.
        """
        with self._connect() as conn:
            if previa:
                # actualizar atención existente
                conn.execute("""
                    UPDATE atencion SET
                        anamnesis=?, examen_fisico=?, diagnostico=?,
                        tratamiento=?, observaciones=?,
                        temperatura_c=?, peso_consulta_kg=?,
                        fc_rpm=?, fr_rpm=?, trc_seg=?,
                        mucosas=?, condicion_corporal=?, dolor=?,
                        estado='en_pausa'
                    WHERE id=?
                """, (
                    data.get("anamnesis",""),
                    data.get("examen_fisico",""),
                    data.get("diagnostico",""),
                    data.get("tratamiento",""),
                    data.get("observaciones",""),
                    data.get("temperatura_c")      or None,
                    data.get("peso_consulta_kg")   or None,
                    data.get("fc_rpm")             or None,
                    data.get("fr_rpm")             or None,
                    data.get("trc_seg")            or None,
                    data.get("mucosas",""),
                    data.get("condicion_corporal") or None,
                    data.get("dolor")              or None,
                    previa["id"],
                ))
                atencion_id = previa["id"]
    
                # borrar y reinsertar medicaciones
                conn.execute(
                    "DELETE FROM medicacion WHERE atencion_id = ?",
                    (atencion_id,))
                conn.execute(
                    "DELETE FROM estudio WHERE atencion_id = ?",
                    (atencion_id,))
            else:
                # crear nueva atención en pausa
                cur = conn.execute("""
                    INSERT INTO atencion
                        (turno_id, paciente_id, veterinario_id,
                        anamnesis, examen_fisico, diagnostico,
                        tratamiento, observaciones,
                        temperatura_c, peso_consulta_kg,
                        fc_rpm, fr_rpm, trc_seg,
                        mucosas, condicion_corporal, dolor,
                        estado)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'en_pausa')
                """, (
                    data.get("turno_id"),
                    data["paciente_id"],
                    data["veterinario_id"],
                    data.get("anamnesis",""),
                    data.get("examen_fisico",""),
                    data.get("diagnostico",""),
                    data.get("tratamiento",""),
                    data.get("observaciones",""),
                    data.get("temperatura_c")      or None,
                    data.get("peso_consulta_kg")   or None,
                    data.get("fc_rpm")             or None,
                    data.get("fr_rpm")             or None,
                    data.get("trc_seg")            or None,
                    data.get("mucosas",""),
                    data.get("condicion_corporal") or None,
                    data.get("dolor")              or None,
                ))
                atencion_id = cur.lastrowid
    
            # insertar medicaciones
            for m in data.get("medicaciones", []):
                if m.get("medicamento","").strip():
                    conn.execute("""
                        INSERT INTO medicacion
                            (atencion_id, medicamento, dosis,
                            via, frecuencia, duracion_dias)
                        VALUES (?,?,?,?,?,?)
                    """, (atencion_id, m["medicamento"],
                        m.get("dosis",""), m.get("via",""),
                        m.get("frecuencia",""),
                        m.get("duracion_dias") or None))
    
            # insertar estudios
            for e in data.get("estudios", []):
                if e.get("tipo","").strip():
                    conn.execute("""
                        INSERT INTO estudio
                            (atencion_id, tipo, descripcion, resultado, fecha)
                        VALUES (?,?,?,?,?)
                    """, (atencion_id, e["tipo"],
                        e.get("descripcion",""),
                        e.get("resultado",""),
                        e.get("fecha", date.today().isoformat())))
    
        return atencion_id
    
    
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
                       u.full_name AS veterinario,
                       t.motivo AS motivo_consulta,
                       t.urgencia AS tipo_atencion
                FROM atencion a
                LEFT JOIN turno t ON t.id = a.turno_id
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

    # 2026-05-29 Leo Arregin: Consultas SQL para los reportes demandados.
    def get_atenciones_totales_por_periodo(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        sort_by: str = "dia",
        sort_dir: str = "desc",
    ) -> list[dict]:
        order_fields = {
            "dia": "DATE(a.fecha_hora)",
            "total": "total_atenciones",
            "normal": "normal",
            "urgente": "urgente",
            "emergencia": "emergencia",
        }
        order_column = order_fields.get(sort_by, "DATE(a.fecha_hora)")
        order_direction = "ASC" if sort_dir.lower() == "asc" else "DESC"

        query = """
            SELECT DATE(a.fecha_hora) AS dia,
                   COUNT(*) AS total_atenciones,
                   COUNT(CASE WHEN lower(COALESCE(t.urgencia, 'normal')) = 'normal' THEN 1 END) AS normal,
                   COUNT(CASE WHEN lower(t.urgencia) = 'urgente' THEN 1 END) AS urgente,
                   COUNT(CASE WHEN lower(t.urgencia) = 'emergencia' THEN 1 END) AS emergencia
            FROM atencion a
            JOIN turno t ON t.id = a.turno_id
            WHERE a.estado = 'cerrado'
        """
        params = []
        if start_date:
            query += " AND DATE(a.fecha_hora) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND DATE(a.fecha_hora) <= ?"
            params.append(end_date)
        query += f" GROUP BY DATE(a.fecha_hora) ORDER BY {order_column} {order_direction}, DATE(a.fecha_hora) DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_atenciones_totales_por_medico(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        sort_by: str = "total",
        sort_dir: str = "desc",
    ) -> list[dict]:
        order_fields = {
            "veterinario": "u.full_name",
            "total": "total_atenciones",
            "normal": "normal",
            "urgente": "urgente",
            "emergencia": "emergencia",
        }
        order_column = order_fields.get(sort_by, "total_atenciones")
        order_direction = "ASC" if sort_dir.lower() == "asc" else "DESC"

        query = """
            SELECT u.full_name AS veterinario,
                   COUNT(*) AS total_atenciones,
                   COUNT(CASE WHEN lower(COALESCE(t.urgencia, 'normal')) = 'normal' THEN 1 END) AS normal,
                   COUNT(CASE WHEN lower(t.urgencia) = 'urgente' THEN 1 END) AS urgente,
                   COUNT(CASE WHEN lower(t.urgencia) = 'emergencia' THEN 1 END) AS emergencia
            FROM atencion a
            JOIN users u ON u.id = a.veterinario_id
            JOIN turno t ON t.id = a.turno_id
            WHERE a.estado = 'cerrado'
        """
        params = []
        if start_date:
            query += " AND DATE(a.fecha_hora) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND DATE(a.fecha_hora) <= ?"
            params.append(end_date)
        query += f" GROUP BY u.id ORDER BY {order_column} {order_direction}, u.full_name"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_frecuencia_atencion_por_cliente(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        sort_by: str = "atenciones",
        sort_dir: str = "desc",
    ) -> list[dict]:
        order_fields = {
            "cliente": "cliente",
            "atenciones": "atenciones",
            "mascotas": "mascotas",
            "promedio": "promedio_por_mascota",
            "ultima": "ultima_atencion",
        }
        order_column = order_fields.get(sort_by, "atenciones")
        order_direction = "ASC" if sort_dir.lower() == "asc" else "DESC"

        query = """
            SELECT c.id AS cliente_id,
                   c.nombre || ' ' || c.apellido AS cliente,
                   COUNT(*) AS atenciones,
                   COUNT(DISTINCT p.id) AS mascotas,
                   ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT p.id), 1) AS promedio_por_mascota,
                   MAX(a.fecha_hora) AS ultima_atencion
            FROM atencion a
            JOIN paciente p ON p.id = a.paciente_id
            JOIN cliente c ON c.id = p.cliente_id
            WHERE a.estado = 'cerrado'
        """
        params = []
        if start_date:
            query += " AND DATE(a.fecha_hora) >= ?"
            params.append(start_date)
        if end_date:
            query += " AND DATE(a.fecha_hora) <= ?"
            params.append(end_date)
        query += f" GROUP BY c.id ORDER BY {order_column} {order_direction}, cliente"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def guardar_atencion(self, data: dict,
                        previa: dict | None = None) -> int:
        """
        Cierra definitivamente la atención.
        Si hay una atención previa en pausa la actualiza a 'cerrado',
        si no existe crea una nueva como 'cerrado'.
        """
        with self._connect() as conn:
            if previa:
                conn.execute("""
                    UPDATE atencion SET
                        anamnesis=?, examen_fisico=?, diagnostico=?,
                        tratamiento=?, observaciones=?,
                        temperatura_c=?, peso_consulta_kg=?,
                        fc_rpm=?, fr_rpm=?, trc_seg=?,
                        mucosas=?, condicion_corporal=?, dolor=?,
                        estado='cerrado'
                    WHERE id=?
                """, (
                    data.get("anamnesis",""),
                    data.get("examen_fisico",""),
                    data.get("diagnostico",""),
                    data.get("tratamiento",""),
                    data.get("observaciones",""),
                    data.get("temperatura_c")      or None,
                    data.get("peso_consulta_kg")   or None,
                    data.get("fc_rpm")             or None,
                    data.get("fr_rpm")             or None,
                    data.get("trc_seg")            or None,
                    data.get("mucosas",""),
                    data.get("condicion_corporal") or None,
                    data.get("dolor")              or None,
                    previa["id"],
                ))
                atencion_id = previa["id"]
                conn.execute(
                    "DELETE FROM medicacion WHERE atencion_id = ?",
                    (atencion_id,))
                conn.execute(
                    "DELETE FROM estudio WHERE atencion_id = ?",
                    (atencion_id,))
            else:
                cur = conn.execute("""
                    INSERT INTO atencion
                        (turno_id, paciente_id, veterinario_id,
                        anamnesis, examen_fisico, diagnostico,
                        tratamiento, observaciones,
                        temperatura_c, peso_consulta_kg,
                        fc_rpm, fr_rpm, trc_seg,
                        mucosas, condicion_corporal, dolor,
                        estado)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'cerrado')
                """, (
                    data.get("turno_id"),
                    data["paciente_id"],
                    data["veterinario_id"],
                    data.get("anamnesis",""),
                    data.get("examen_fisico",""),
                    data.get("diagnostico",""),
                    data.get("tratamiento",""),
                    data.get("observaciones",""),
                    data.get("temperatura_c")      or None,
                    data.get("peso_consulta_kg")   or None,
                    data.get("fc_rpm")             or None,
                    data.get("fr_rpm")             or None,
                    data.get("trc_seg")            or None,
                    data.get("mucosas",""),
                    data.get("condicion_corporal") or None,
                    data.get("dolor")              or None,
                ))
                atencion_id = cur.lastrowid
    
            # medicaciones y estudios
            for m in data.get("medicaciones", []):
                if m.get("medicamento","").strip():
                    conn.execute("""
                        INSERT INTO medicacion
                            (atencion_id, medicamento, dosis,
                            via, frecuencia, duracion_dias)
                        VALUES (?,?,?,?,?,?)
                    """, (atencion_id, m["medicamento"],
                        m.get("dosis",""), m.get("via",""),
                        m.get("frecuencia",""),
                        m.get("duracion_dias") or None))
    
            for e in data.get("estudios", []):
                if e.get("tipo","").strip():
                    conn.execute("""
                        INSERT INTO estudio
                            (atencion_id, tipo, descripcion, resultado, fecha)
                        VALUES (?,?,?,?,?)
                    """, (atencion_id, e["tipo"],
                        e.get("descripcion",""),
                        e.get("resultado",""),
                        e.get("fecha", date.today().isoformat())))
    
            # marcar turno como atendido
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