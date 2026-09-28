# Elimina duplicados exactos conservando la primera copia de cada registro.
import os
import shutil
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "market_data.db")
RESPALDO = os.path.join(BASE_DIR, "data", "market_data_respaldo.db")


def limpiar():
    if input("Se creará un respaldo y se borrarán duplicados. Escribe SI para continuar: ") != "SI":
        print("Cancelado, no se modificó nada.")
        return

    shutil.copy2(DB_PATH, RESPALDO)
    print(f"Respaldo creado en {RESPALDO}")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
        DELETE FROM precios WHERE id NOT IN (
            SELECT MIN(id) FROM precios GROUP BY ticker, fecha)
    """)
    print(f"Precios duplicados eliminados:  {cur.rowcount}")

    cur.execute("""
        DELETE FROM noticias WHERE id NOT IN (
            SELECT MIN(id) FROM noticias GROUP BY ticker, fecha, titular)
    """)
    print(f"Noticias duplicadas eliminadas: {cur.rowcount}")

    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_precios_unico ON precios (ticker, fecha)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_noticias_unico ON noticias (ticker, fecha, titular)")

    con.commit()
    con.execute("VACUUM")
    con.close()
    print("Limpieza terminada.")


if __name__ == "__main__":
    limpiar()