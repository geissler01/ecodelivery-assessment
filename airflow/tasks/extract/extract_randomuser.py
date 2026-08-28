"""
Tarea de Extracción: Perfiles Demográficos (RandomUser API -> Bronze.raw_randomuser_profiles)
"""
import os
import json
import logging
import requests
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

DWH_URI = os.getenv(
    "AIRFLOW_DWH_URI",
    "postgresql+psycopg2://ecodelivery_user:ecodelivery_user_01**@postgres:5432/ecodelivery_dwh"
)

def extract_randomuser():
    logger.info(">>> [BRONZE] Consumiendo RandomUser API para enriquecimiento demográfico...")
    engine_dwh = create_engine(DWH_URI)

    # 1. Asegurar esquema y tabla en DWH
    with engine_dwh.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bronze.raw_randomuser_profiles (
                user_index INT,
                gender VARCHAR(20),
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                email VARCHAR(255),
                age VARCHAR(10),
                dob_date VARCHAR(50),
                phone VARCHAR(50),
                picture_url VARCHAR(500),
                raw_json JSONB,
                ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

    url = "https://randomuser.me/api/?results=150&seed=ecodelivery_2026&inc=gender,name,location,email,dob,phone,picture"
    try:
        response = requests.get(url, timeout=12)
        response.raise_for_status()
        data = response.json().get("results", [])
        logger.info(f">>> [BRONZE] {len(data)} perfiles obtenidos exitosamente de RandomUser API.")
    except Exception as e:
        logger.warning(f">>> [BRONZE] Error al conectar con RandomUser API ({e}). Generando perfiles deterministas de respaldo...")
        data = []
        for i in range(1, 151):
            gender = "female" if i % 2 == 0 else "male"
            age = 20 + ((i * 7) % 45)
            data.append({
                "gender": gender,
                "name": {"first": f"Nombre{i}", "last": f"Apellido{i}"},
                "email": f"backup_user_{i}@example.com",
                "dob": {"age": age, "date": f"{2026-age}-05-15T00:00:00.000Z"},
                "phone": f"+57 300 {100 + (i % 899)} {1000 + i}",
                "picture": {"medium": f"https://randomuser.me/api/portraits/{'women' if gender=='female' else 'men'}/{i % 99}.jpg"}
            })

    records = []
    for idx, user in enumerate(data, start=1):
        gender = user.get("gender", "unknown").capitalize()
        first_name = user.get("name", {}).get("first", "")
        last_name = user.get("name", {}).get("last", "")
        email = user.get("email", "")
        dob_info = user.get("dob", {})
        age = str(dob_info.get("age", 25))
        dob_date = str(dob_info.get("date", "1995-01-01T00:00:00.000Z"))[:10]
        phone = str(user.get("phone", f"+57 300 {idx:03d} {idx:04d}"))
        picture_url = user.get("picture", {}).get("medium", "")

        records.append({
            "user_index": idx,
            "gender": gender,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "age": age,
            "dob_date": dob_date,
            "phone": phone,
            "picture_url": picture_url,
            "raw_json": json.dumps(user)
        })

    # 3. Inserción masiva en Bronze
    with engine_dwh.begin() as conn:
        conn.execute(text("TRUNCATE TABLE bronze.raw_randomuser_profiles;"))
        conn.execute(text("""
            INSERT INTO bronze.raw_randomuser_profiles (
                user_index, gender, first_name, last_name, email, age,
                dob_date, phone, picture_url, raw_json, ingestion_timestamp
            ) VALUES (
                :user_index, :gender, :first_name, :last_name, :email, :age,
                :dob_date, :phone, :picture_url, :raw_json, CURRENT_TIMESTAMP
            )
        """), records)

    logger.info(f">>> [BRONZE] {len(records)} perfiles demográficos insertados en bronze.raw_randomuser_profiles.")
    return len(records)
