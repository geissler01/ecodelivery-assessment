import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def reset_db():
    print("=== Recreando airflow_db en PostgreSQL ===")
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "ecodelivery_db"),
            user=os.getenv("POSTGRES_USER", "ecodelivery_user"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            host=os.getenv("POSTGRES_HOST", "100.60.229.203"),
            port=int(os.getenv("POSTGRES_PORT", "5432"))
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("DROP DATABASE IF EXISTS airflow_db WITH (FORCE);")
        cur.execute("CREATE DATABASE airflow_db OWNER " + os.getenv("POSTGRES_USER", "ecodelivery_user") + ";")
        cur.close()
        conn.close()
        print(">>> Base de datos airflow_db recreada limpiamente!")
    except Exception as e:
        print(">>> Advertencia al recrear DB:", e)

if __name__ == "__main__":
    reset_db()
