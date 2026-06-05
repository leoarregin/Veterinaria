import sqlite3

# Ruta a tu base de datos SQLite
DB_PATH = "hospital_veterinario.db"

SQL = """
UPDATE turno
SET fecha_hora =
    strftime('%Y-', fecha_hora) ||
    strftime('%m-%d', 'now') ||
    strftime(' %H:%M:%S', fecha_hora);
"""

def actualizar_fechas():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(SQL)

        filas_afectadas = cursor.rowcount
        conn.commit()

        print(f"Proceso finalizado. Registros actualizados: {filas_afectadas}")

    except sqlite3.Error as e:
        print(f"Error SQLite: {e}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    actualizar_fechas()