import sqlite3
from datetime import datetime
import hashlib
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from app.models.user import User


class UserRepository:
    def __init__(self, db_path: str | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        self.db_path = Path(db_path) if db_path else base_dir / "hospital_veterinario.db"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL DEFAULT '',
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Activo',
                    last_access TEXT NOT NULL
                )
                """
            )
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
            if "password_hash" not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''")
            if "email" not in columns:
                conn.execute("ALTER TABLE users ADD COLUMN email TEXT NOT NULL DEFAULT ''")
            total = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
            if total == 0:
                now = datetime.now().isoformat(timespec="minutes")
                seed = [
                    ("admin", "", generate_password_hash("admin123"), "Administrador General", "Administrador", "Activo", now),
                    ("recepcion1", "", generate_password_hash("recepcion123"), "Laura Fernandez", "Recepcionista", "Activo", now),
                    ("vetmartinez", "", generate_password_hash("vet123"), "Dra. Martinez", "Veterinario", "Activo", now),
                    ("admincont", "", generate_password_hash("cont123"), "Carlos Perez", "Administrativo", "Inactivo", now),
                ]
                conn.executemany(
                    """
                    INSERT INTO users (username, email, password_hash, full_name, role, status, last_access)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    seed,
                )
            self._backfill_seed_passwords(conn)
            self._import_login_users(conn)

    def list_all(self) -> list[User]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        return [self._row_to_user(row) for row in rows]

    def list_by_role(self, role: str) -> list[User]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM users WHERE lower(role) = lower(?) AND lower(status) = 'activo' ORDER BY full_name",
                (role,),
            ).fetchall()
        return [self._row_to_user(row) for row in rows]

    def get_by_id(self, user_id: int) -> User | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._row_to_user(row) if row else None

    def create(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str,
        status: str,
        last_access: str,
        email: str = "",
    ) -> None:
        with self._connect() as conn:
            self._ensure_unique_login(conn, username, email)
            conn.execute(
                """
                INSERT INTO users (username, email, password_hash, full_name, role, status, last_access)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (username, email, generate_password_hash(password), full_name, role, status, last_access),
            )

    def update(
        self,
        user_id: int,
        username: str,
        full_name: str,
        role: str,
        status: str,
        last_access: str,
        email: str = "",
    ) -> None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id FROM users
                WHERE id != ? AND (lower(username) = lower(?) OR (? != '' AND lower(email) = lower(?)))
                """,
                (user_id, username, email, email),
            ).fetchone()
            if row:
                raise ValueError("El usuario o email ya esta registrado.")
            conn.execute(
                """
                UPDATE users
                SET username = ?, email = ?, full_name = ?, role = ?, status = ?, last_access = ?
                WHERE id = ?
                """,
                (username, email, full_name, role, status, last_access, user_id),
            )

    def delete(self, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def authenticate(self, login: str, password: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM users
                WHERE lower(username) = lower(?) OR lower(email) = lower(?)
                """,
                (login, login),
            ).fetchone()
            if row is None or row["status"] != "Activo":
                return None
            if not self._password_matches(row["password_hash"], password):
                return None
            now = datetime.now().isoformat(timespec="minutes")
            conn.execute("UPDATE users SET last_access = ? WHERE id = ?", (now, row["id"]))
            updated = dict(row)
            updated["last_access"] = now
            return self._row_to_user(updated)

    def get_by_username_or_email(self, login: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM users
                WHERE lower(username) = lower(?) OR lower(email) = lower(?)
                """,
                (login, login),
            ).fetchone()
        return self._row_to_user(row) if row else None

    def _row_to_user(self, row: sqlite3.Row | dict) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            full_name=row["full_name"],
            role=row["role"],
            status=row["status"],
            last_access=datetime.fromisoformat(row["last_access"]),
            email=row["email"] if "email" in row.keys() else "",
        )

    def _ensure_unique_login(self, conn: sqlite3.Connection, username: str, email: str) -> None:
        row = conn.execute(
            """
            SELECT id FROM users
            WHERE lower(username) = lower(?) OR (? != '' AND lower(email) = lower(?))
            """,
            (username, email, email),
        ).fetchone()
        if row:
            raise ValueError("El usuario o email ya esta registrado.")

    def _password_matches(self, password_hash: str, password: str) -> bool:
        if password_hash.startswith(("scrypt:", "pbkdf2:", "argon2:")):
            return check_password_hash(password_hash, password)
        return hashlib.sha256(password.encode()).hexdigest() == password_hash

    def _import_login_users(self, conn: sqlite3.Connection) -> None:
        login_db = self.db_path.parent.parent / "Login" / "login" / "usuarios.db"
        if not login_db.exists():
            return
        with sqlite3.connect(login_db) as login_conn:
            login_conn.row_factory = sqlite3.Row
            rows = login_conn.execute(
                """
                SELECT usuario, nombre, apellido, email, password_hash, fecha_registro
                FROM usuarios
                """
            ).fetchall()
        for row in rows:
            exists = conn.execute(
                """
                SELECT id FROM users
                WHERE lower(username) = lower(?) OR lower(email) = lower(?)
                """,
                (row["usuario"], row["email"]),
            ).fetchone()
            if exists:
                continue
            full_name = f"{row['nombre']} {row['apellido']}".strip()
            last_access = row["fecha_registro"].replace(" ", "T")[:16]
            conn.execute(
                """
                INSERT INTO users (username, email, password_hash, full_name, role, status, last_access)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (row["usuario"], row["email"], row["password_hash"], full_name, "Administrativo", "Activo", last_access),
            )

    def _backfill_seed_passwords(self, conn: sqlite3.Connection) -> None:
        default_passwords = {
            "admin": "admin123",
            "recepcion1": "recepcion123",
            "vetmartinez": "vet123",
            "admincont": "cont123",
        }
        for username, password in default_passwords.items():
            conn.execute(
                """
                UPDATE users
                SET password_hash = ?
                WHERE username = ? AND password_hash = ''
                """,
                (generate_password_hash(password), username),
            )
