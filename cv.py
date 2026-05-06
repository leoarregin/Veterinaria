"""
agregar_constantes_vitales.py
Agrega columnas de constantes vitales a la tabla 'atencion' existente.
Ejecutar UNA sola vez desde la raíz del proyecto:
    python agregar_constantes_vitales.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "hospital_veterinario.db"


def columnas_existentes(conn: sqlite3.Connection, tabla: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({tabla})").fetchall()
    return {row[1] for row in rows}


def migrar():
    with sqlite3.connect(DB_PATH) as conn:
        existentes = columnas_existentes(conn, "atencion")

        # Definición de cada columna nueva:
        # (nombre, tipo, default)
        nuevas = [
            ("temperatura_c",    "REAL",    None),   # °C
            ("peso_consulta_kg", "REAL",    None),   # kg al momento de la consulta
            ("fc_rpm",           "INTEGER", None),   # frecuencia cardíaca (rpm)
            ("fr_rpm",           "INTEGER", None),   # frecuencia respiratoria (rpm)
            ("trc_seg",          "REAL",    None),   # tiempo de relleno capilar (seg)
            ("mucosas",          "TEXT",    None),   # rosadas, pálidas, cianóticas…
            ("condicion_corporal","INTEGER",None),   # escala 1-9
            ("dolor",            "INTEGER", None),   # escala 0-10
        ]

        agregadas = []
        omitidas  = []

        for nombre, tipo, default in nuevas:
            if nombre in existentes:
                omitidas.append(nombre)
                continue
            if default is not None:
                conn.execute(
                    f"ALTER TABLE atencion ADD COLUMN {nombre} {tipo} DEFAULT {default}"
                )
            else:
                conn.execute(
                    f"ALTER TABLE atencion ADD COLUMN {nombre} {tipo}"
                )
            agregadas.append(nombre)

        if agregadas:
            print(f"✅ Columnas agregadas: {', '.join(agregadas)}")
        if omitidas:
            print(f"ℹ️  Ya existían (omitidas): {', '.join(omitidas)}")
        if not agregadas and not omitidas:
            print("⚠️  No se realizó ningún cambio.")

        # Verificar resultado final
        print("\nEstructura actual de 'atencion':")
        for row in conn.execute("PRAGMA table_info(atencion)").fetchall():
            print(f"  {row[1]:25s} {row[2]}")


if __name__ == "__main__":
    migrar()