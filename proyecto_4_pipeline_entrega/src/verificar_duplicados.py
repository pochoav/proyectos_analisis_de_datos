#Diagnóstico de la base de datos
import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "market_data.db")

def escalar(con, sql):
    return con.execute(sql).fetchone()[0]

def consulta(con, sql):
    return pd.read_sql_query(sql, con)

def revisar_tabla(con, tabla, columnas_clave):
    """Compara filas totales contra registros únicos según la clave dada."""
    clave = ", ".join(columnas_clave)
    filas = escalar(con, f"SELECT COUNT(*) FROM {tabla}")
    unicas = escalar(con, f"SELECT COUNT(*) FROM (SELECT DISTINCT {clave} FROM {tabla})")
    print(f"Filas totales:           {filas}")
    print(f"Registros únicos ({clave}): {unicas}")
    print(f"Filas sobrantes:         {filas - unicas}")

    print("\nCuántas veces aparece cada registro:")
    print(consulta(con, f"""
        SELECT veces, COUNT(*) AS registros FROM (
            SELECT COUNT(*) AS veces FROM {tabla} GROUP BY {clave}
        ) GROUP BY veces ORDER BY veces
    """).to_string(index=False))
    return filas - unicas

def verificar():
    con = sqlite3.connect(DB_PATH)

    print("=" * 60)
    print("1. PRECIOS (clave: ticker + fecha)")
    print("=" * 60)
    sobrantes_precios = revisar_tabla(con, "precios", ["ticker", "fecha"])
    print("\nPor ticker:")
    print(consulta(con, """
        SELECT ticker, COUNT(*) AS filas, COUNT(DISTINCT fecha) AS fechas_unicas,
               MIN(fecha) AS desde, MAX(fecha) AS hasta
        FROM precios GROUP BY ticker
    """).to_string(index=False))
    nulos = escalar(con, "SELECT COUNT(*) FROM precios WHERE cierre IS NULL OR volumen IS NULL")
    print(f"\nFilas con cierre o volumen vacío: {nulos}")

    print("\n" + "=" * 60)
    print("2. NOTICIAS (clave: ticker + fecha + titular)")
    print("=" * 60)
    sobrantes_noticias = revisar_tabla(con, "noticias", ["ticker", "fecha", "titular"])
    print("\nPor ticker:")
    print(consulta(con, """
        SELECT ticker, COUNT(*) AS filas,
               COUNT(DISTINCT fecha || '|' || titular) AS unicas,
               MIN(fecha) AS desde, MAX(fecha) AS hasta
        FROM noticias GROUP BY ticker
    """).to_string(index=False))

    repetidos = escalar(con, """
        SELECT COUNT(*) FROM (
            SELECT ticker, titular FROM noticias
            GROUP BY ticker, titular HAVING COUNT(DISTINCT fecha) > 1
        )
    """)
    print(f"\nTitulares repetidos con fechas DISTINTAS (posibles republicaciones): {repetidos}")

    vacios = escalar(con, """
        SELECT COUNT(*) FROM noticias
        WHERE titular IS NULL OR TRIM(titular) = '' OR titular = '[Removed]'
    """)
    print(f"Titulares vacíos o '[Removed]': {vacios}")

    print("\n" + "=" * 60)
    if sobrantes_precios == 0 and sobrantes_noticias == 0:
        print("✅ No hay duplicados exactos.")
    else:
        print(f"⚠️ Duplicados: {sobrantes_precios} en precios, {sobrantes_noticias} en noticias.")
    con.close()

if __name__ == "__main__":
    verificar()