#!/usr/bin/env bash
set -euo pipefail
echo "[centos_ingest] Iniciando ingesta desde /data/contacts.csv"
: "${POSTGRES_USER:?POSTGRES_USER requerido}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD requerido}"
: "${POSTGRES_DB:?POSTGRES_DB requerido}"
export PGPASSWORD="${POSTGRES_PASSWORD}"

# 👇 Re-crear SIEMPRE la tabla staging SIN UNIQUE
psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "
DROP TABLE IF EXISTS public.contactos;
CREATE TABLE public.contactos (
  first_name   TEXT,
  last_name    TEXT,
  company_name TEXT,
  address      TEXT,
  city         TEXT,
  state        TEXT,
  zip          TEXT,
  phone1       TEXT,
  phone2       TEXT,
  email        TEXT,
  department   TEXT
);
"

# CSV montado
if [ ! -f /data/contacts.csv ]; then
  echo "[centos_ingest] ERROR: No existe /data/contacts.csv"
  exit 2
fi

# Carga cruda
psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 \
  -c "\\copy public.contactos (first_name,last_name,company_name,address,city,state,zip,phone1,phone2,email,department) FROM '/data/contacts.csv' CSV HEADER;"

# Diagnóstico útil
psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) AS staging_rows FROM public.contactos;"
psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT email, COUNT(*) AS c FROM public.contactos GROUP BY email HAVING COUNT(*)>1 ORDER BY c DESC LIMIT 5;"

# Normalización
psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f /opt/app/normalize.sql

# Conteo final
psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tA -c "SELECT 'contactos='||COUNT(*) FROM public.contacto;"
echo "[centos_ingest] Ingesta completada"
