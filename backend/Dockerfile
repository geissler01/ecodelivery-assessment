FROM python:3.13-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar/ejecutar psycopg2 si hiciera falta
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer el puerto 8000
EXPOSE 8000

# Ejecutar con uvicorn en 0.0.0.0:8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
