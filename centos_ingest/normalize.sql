BEGIN;

-- N:M para múltiples departamentos por contacto
CREATE TABLE IF NOT EXISTS public.contacto_departamento (
  contacto_id     BIGINT NOT NULL REFERENCES public.contacto(contacto_id) ON DELETE CASCADE,
  departamento_id BIGINT NOT NULL REFERENCES public.departamento(departamento_id) ON DELETE RESTRICT,
  PRIMARY KEY (contacto_id, departamento_id)
);

-- Fuente deduplicada por email (elige fila “principal” por email)
DROP TABLE IF EXISTS tmp_src;
CREATE TEMP TABLE tmp_src AS
WITH c AS (
  SELECT
    TRIM(first_name)   AS first_name,
    TRIM(last_name)    AS last_name,
    TRIM(company_name) AS company_name,
    TRIM(address)      AS address,
    TRIM(city)         AS city,
    UPPER(TRIM(state)) AS state,
    TRIM(zip)          AS zip,
    TRIM(phone1)       AS phone1,
    TRIM(phone2)       AS phone2,
    TRIM(email)        AS email,
    TRIM(department)   AS department,
    LOWER(TRIM(email))     AS email_key,
    LOWER(TRIM(department)) AS dept_key
  FROM public.contactos
  WHERE email IS NOT NULL AND TRIM(email) <> ''
),
w AS (
  SELECT c.*,
         COUNT(*) OVER (PARTITION BY email_key, dept_key) AS dept_count
  FROM c
)
SELECT DISTINCT ON (email_key)
  first_name, last_name, company_name, address, city, state, zip, phone1, phone2, email,
  NULLIF(department,'') AS department
FROM w
ORDER BY
  email_key,
  CASE WHEN department IS NOT NULL AND department <> '' THEN 0 ELSE 1 END,
  dept_count DESC,
  department,
  CASE WHEN company_name IS NOT NULL AND company_name <> '' THEN 0 ELSE 1 END,
  CASE WHEN address      IS NOT NULL AND address      <> '' THEN 0 ELSE 1 END;

CREATE INDEX ON tmp_src (state);
CREATE INDEX ON tmp_src (email);
CREATE INDEX ON tmp_src (city);

-- Todos los departamentos del CSV (aunque no queden en tmp_src)
DROP TABLE IF EXISTS tmp_dept_all;
CREATE TEMP TABLE tmp_dept_all AS
SELECT DISTINCT TRIM(department) AS nombre
FROM public.contactos
WHERE TRIM(department) <> '';

-- Dimensiones
INSERT INTO public.estado(codigo, nombre)
SELECT DISTINCT s.state AS codigo, s.state AS nombre
FROM tmp_src s
WHERE s.state ~ '^[A-Z]{2}$'
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO public.ciudad(nombre, estado_id)
SELECT DISTINCT TRIM(s.city) AS nombre, e.estado_id
FROM tmp_src s
JOIN public.estado e ON e.codigo = s.state
WHERE TRIM(s.city) <> ''
ON CONFLICT (nombre, estado_id) DO NOTHING;

INSERT INTO public.empresa(nombre)
SELECT DISTINCT TRIM(s.company_name)
FROM tmp_src s
WHERE TRIM(s.company_name) <> ''
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO public.departamento(nombre)
SELECT nombre
FROM tmp_dept_all
ON CONFLICT (nombre) DO NOTHING;

-- Contacto (uno por email)
INSERT INTO public.contacto(first_name, last_name, email, empresa_id, departamento_id)
SELECT
  s.first_name,
  s.last_name,
  s.email,
  e.empresa_id,
  d.departamento_id   -- opcional como “principal”
FROM tmp_src s
LEFT JOIN public.empresa      e ON e.nombre = TRIM(s.company_name)
LEFT JOIN public.departamento d ON d.nombre = TRIM(s.department)
ON CONFLICT (email) DO UPDATE
SET first_name = EXCLUDED.first_name,
    last_name  = EXCLUDED.last_name,
    empresa_id = EXCLUDED.empresa_id,
    departamento_id = EXCLUDED.departamento_id,
    actualizado_en  = now();

-- Direcciones
INSERT INTO public.direccion(contacto_id, ciudad_id, address, zip)
SELECT
  ct.contacto_id,
  ci.ciudad_id,
  NULLIF(s.address,'') AS address,
  NULLIF(s.zip,'')     AS zip
FROM tmp_src s
JOIN public.contacto ct ON ct.email = s.email
LEFT JOIN public.estado es ON es.codigo = s.state
LEFT JOIN public.ciudad ci ON ci.nombre = TRIM(s.city) AND ci.estado_id = es.estado_id
ON CONFLICT (contacto_id) DO UPDATE
SET ciudad_id = EXCLUDED.ciudad_id,
    address   = EXCLUDED.address,
    zip       = EXCLUDED.zip;

-- Teléfonos
INSERT INTO public.telefono(contacto_id, tipo, numero)
SELECT ct.contacto_id, 'principal'::text, s.phone1
FROM tmp_src s
JOIN public.contacto ct ON ct.email = s.email
WHERE s.phone1 IS NOT NULL AND TRIM(s.phone1) <> ''
ON CONFLICT (contacto_id, tipo) DO UPDATE SET numero = EXCLUDED.numero;

INSERT INTO public.telefono(contacto_id, tipo, numero)
SELECT ct.contacto_id, 'alterno'::text, s.phone2
FROM tmp_src s
JOIN public.contacto ct ON ct.email = s.email
WHERE s.phone2 IS NOT NULL AND TRIM(s.phone2) <> ''
ON CONFLICT (contacto_id, tipo) DO UPDATE SET numero = EXCLUDED.numero;

-- ***NUEVO***: TODAS las combinaciones email–departamento (N:M)
INSERT INTO public.contacto_departamento (contacto_id, departamento_id)
SELECT DISTINCT
  c.contacto_id,
  d.departamento_id
FROM (
  SELECT DISTINCT LOWER(TRIM(email)) AS email_key, TRIM(department) AS department
  FROM public.contactos
  WHERE TRIM(email) <> '' AND TRIM(department) <> ''
) s
JOIN public.contacto     c ON LOWER(c.email) = s.email_key
JOIN public.departamento d ON d.nombre = s.department
ON CONFLICT (contacto_id, departamento_id) DO NOTHING;

COMMIT;
