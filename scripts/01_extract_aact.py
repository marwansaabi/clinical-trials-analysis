"""Copia las tablas necesarias de AACT (base de datos de ClinicalTrials.gov) a un DuckDB local.

Requisitos: cuenta gratuita en https://aact.ctti-clinicaltrials.org y un archivo .env con
AACT_USER y AACT_PASSWORD (ver .env.example).
Uso: python scripts/01_extract_aact.py
Resultado: data/aact.duckdb, sobre el que se ejecutan las consultas de la carpeta sql/.
"""
import os
from pathlib import Path

import duckdb
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# Tablas que vamos a usar (esquema ctgov de AACT)
TABLES = [
    "studies",            # una fila por ensayo: fase, estado, fechas, motivo de parada, tamaño
    "conditions",         # enfermedades tal y como las escribe el patrocinador
    "browse_conditions",  # enfermedades normalizadas con términos MeSH
    "interventions",      # fármacos, dispositivos, procedimientos...
    "sponsors",           # patrocinador principal y colaboradores (industria, NIH, otros)
    "countries",          # países donde se realiza cada ensayo
    "facilities",         # centros concretos (ciudad, país)
    "designs",            # diseño: aleatorizado, enmascaramiento, propósito
    "calculated_values",  # campos calculados por AACT (duración, número de centros...)
]


def main():
    user, pwd = os.getenv("AACT_USER"), os.getenv("AACT_PASSWORD")
    if not user or not pwd:
        raise SystemExit("Falta AACT_USER/AACT_PASSWORD en el archivo .env")
    (ROOT / "data").mkdir(exist_ok=True)
    con = duckdb.connect(str(ROOT / "data" / "aact.duckdb"))
    con.sql("INSTALL postgres; LOAD postgres;")
    try:
        con.sql(f"ATTACH 'host=aact-db.ctti-clinicaltrials.org port=5432 dbname=aact user={user} password={pwd}' "
                "AS aact_remote (TYPE postgres, READ_ONLY)")
    except duckdb.Error as e:
        # No mostrar la contraseña en el mensaje de error
        raise SystemExit("No se pudo conectar a AACT: " + str(e).replace(pwd, "****"))
    for t in TABLES:
        print(f"Copiando {t}...", flush=True)
        con.sql(f"CREATE OR REPLACE TABLE {t} AS SELECT * FROM aact_remote.ctgov.{t}")
        n = con.sql(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {n:,} filas")
    con.sql("DETACH aact_remote")
    con.close()
    print("Listo: data/aact.duckdb")


if __name__ == "__main__":
    main()
