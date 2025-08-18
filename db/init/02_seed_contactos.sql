-- 02_seed_contactos.sql — staging + dedupe + upsert
\set ON_ERROR_STOP on
\echo 'Seeding CSV (staging) -> public.contactos'

-- staging sin constraints (acepta duplicados)
CREATE UNLOGGED TABLE IF NOT EXISTS public.contactos_seed (
  first_name    VARCHAR(100) NOT NULL,
  last_name     VARCHAR(100) NOT NULL,
  company_name  VARCHAR(255),
  address       VARCHAR(255),
  city          VARCHAR(120),
  state         CHAR(2) NOT NULL,
  zip           VARCHAR(10),
  phone1        VARCHAR(20),
  phone2        VARCHAR(20),
  email         VARCHAR(255) NOT NULL,
  department    VARCHAR(150)
);
TRUNCATE TABLE public.contactos_seed;

\encoding UTF8
-- 1) carga del CSV (ruta dentro del contenedor db)
\copy public.contactos_seed (first_name,last_name,company_name,address,city,state,zip,phone1,phone2,email,department) FROM '/docker-entrypoint-initdb.d/contacts.csv' WITH (FORMAT csv, HEADER true);

-- 2) dedupe + UPSERT a la tabla final
INSERT INTO public.contactos
(first_name,last_name,company_name,address,city,state,zip,phone1,phone2,email,department)
SELECT
  s.first_name,
  s.last_name,
  s.company_name,
  s.address,
  s.city,
  upper(s.state),
  s.zip,
  s.phone1,
  s.phone2,
  lower(s.email),
  s.department
FROM (
  SELECT DISTINCT ON (lower(email))
         first_name,last_name,company_name,address,city,state,zip,phone1,phone2,email,department
  FROM public.contactos_seed
  WHERE email IS NOT NULL AND email <> ''
  ORDER BY lower(email)
) AS s
ON CONFLICT (email) DO UPDATE
  SET first_name = EXCLUDED.first_name,
      last_name  = EXCLUDED.last_name,
      company_name = EXCLUDED.company_name,
      address = EXCLUDED.address,
      city = EXCLUDED.city,
      state = EXCLUDED.state,
      zip = EXCLUDED.zip,
      phone1 = EXCLUDED.phone1,
      phone2 = EXCLUDED.phone2,
      department = EXCLUDED.department;

-- 3) conteo
SELECT COUNT(*) AS contactos_cargados FROM public.contactos;
