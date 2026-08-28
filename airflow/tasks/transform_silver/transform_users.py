"""
Transformación Silver: Limpieza y Enriquecimiento de Usuarios (Silver.users)
"""
import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

DWH_URI = os.getenv(
    "AIRFLOW_DWH_URI",
    "postgresql+psycopg2://ecodelivery_user:ecodelivery_user_01**@postgres:5432/ecodelivery_dwh"
)

def get_age_group(age: int) -> str:
    if age <= 25:
        return "18-25"
    elif age <= 35:
        return "26-35"
    elif age <= 50:
        return "36-50"
    else:
        return "50+"

def transform_users():
    logger.info(">>> [SILVER] Procesando y enriqueciendo usuarios...")
    engine_dwh = create_engine(DWH_URI)

    # 1. Asegurar esquema y tabla silver.users
    with engine_dwh.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver.users (
                user_id UUID PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                gender VARCHAR(20),
                age INT,
                age_group VARCHAR(50),
                dob_date DATE,
                phone VARCHAR(50),
                avatar_url VARCHAR(500),
                zona_principal VARCHAR(50),
                tipo_vehiculo_predilecto VARCHAR(50),
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                is_verified BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE,
                silver_processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

    # 2. Leer Bronze raw_users y raw_randomuser_profiles
    with engine_dwh.connect() as conn:
        res_users = conn.execute(text("""
            SELECT id, email, full_name, role, telefono, zona_principal, 
                   tipo_vehiculo_predilecto, is_active, is_verified, created_at, updated_at 
            FROM bronze.raw_users
            ORDER BY created_at ASC
        """))
        df_users = pd.DataFrame(res_users.fetchall(), columns=res_users.keys())

        res_random = conn.execute(text("""
            SELECT user_index, gender, age, dob_date, phone, picture_url 
            FROM bronze.raw_randomuser_profiles
            ORDER BY user_index ASC
        """))
        df_random = pd.DataFrame(res_random.fetchall(), columns=res_random.keys())

    if df_users.empty:
        logger.warning(">>> [SILVER] bronze.raw_users está vacío. Abortando.")
        return 0

    # 3. Enriquecimiento controlado respetando integridad de negocio
    silver_records = []
    num_random = len(df_random)

    for idx, row in df_users.iterrows():
        # Match determinista con perfil de randomuser
        rand_profile = df_random.iloc[idx % num_random] if num_random > 0 else None
        
        # Edad y Grupo Etario
        raw_age = rand_profile["age"] if rand_profile is not None else "30"
        try:
            age = int(raw_age)
        except (ValueError, TypeError):
            age = 30
        age_group = get_age_group(age)

        # Género (Male/Female)
        gender = rand_profile["gender"] if rand_profile is not None else "Unknown"

        # Fecha de Nacimiento
        dob_date = rand_profile["dob_date"] if rand_profile is not None else "1995-01-01"

        # Teléfono: Preservar si ya existe en BD, de lo contrario enriquecer con formato limpio
        phone = row["telefono"] if row["telefono"] and str(row["telefono"]).strip() else (
            rand_profile["phone"] if rand_profile is not None else f"+57 300 000 {idx:04d}"
        )

        # Avatar URL
        avatar_url = rand_profile["picture_url"] if rand_profile is not None else ""

        # Flags booleanos
        is_active = str(row["is_active"]).lower() in ["true", "1", "t"]
        is_verified = str(row["is_verified"]).lower() in ["true", "1", "t"]

        silver_records.append({
            "user_id": row["id"],
            "full_name": str(row["full_name"]).strip(),
            "email": str(row["email"]).strip(),
            "role": str(row["role"]).strip().lower(),
            "gender": gender,
            "age": age,
            "age_group": age_group,
            "dob_date": dob_date,
            "phone": phone,
            "avatar_url": avatar_url,
            "zona_principal": row["zona_principal"] if row["zona_principal"] else None,
            "tipo_vehiculo_predilecto": row["tipo_vehiculo_predilecto"] if row["tipo_vehiculo_predilecto"] else None,
            "is_active": is_active,
            "is_verified": is_verified,
            "created_at": row["created_at"] if row["created_at"] else "2026-08-01 00:00:00+00",
            "updated_at": row["updated_at"] if row["updated_at"] else "2026-08-01 00:00:00+00",
        })

    # 4. UPSERT Idempotente en silver.users
    with engine_dwh.begin() as conn:
        for rec in silver_records:
            conn.execute(text("""
                INSERT INTO silver.users (
                    user_id, full_name, email, role, gender, age, age_group,
                    dob_date, phone, avatar_url, zona_principal, tipo_vehiculo_predilecto,
                    is_active, is_verified, created_at, updated_at, silver_processed_at
                ) VALUES (
                    :user_id, :full_name, :email, :role, :gender, :age, :age_group,
                    :dob_date, :phone, :avatar_url, :zona_principal, :tipo_vehiculo_predilecto,
                    :is_active, :is_verified, :created_at, :updated_at, CURRENT_TIMESTAMP
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    email = EXCLUDED.email,
                    role = EXCLUDED.role,
                    gender = EXCLUDED.gender,
                    age = EXCLUDED.age,
                    age_group = EXCLUDED.age_group,
                    dob_date = EXCLUDED.dob_date,
                    phone = EXCLUDED.phone,
                    avatar_url = EXCLUDED.avatar_url,
                    zona_principal = EXCLUDED.zona_principal,
                    tipo_vehiculo_predilecto = EXCLUDED.tipo_vehiculo_predilecto,
                    is_active = EXCLUDED.is_active,
                    is_verified = EXCLUDED.is_verified,
                    updated_at = EXCLUDED.updated_at,
                    silver_processed_at = CURRENT_TIMESTAMP;
            """), rec)

    logger.info(f">>> [SILVER] {len(silver_records)} usuarios transformados y enriquecidos en silver.users.")
    return len(silver_records)
