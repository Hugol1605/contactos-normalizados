/* 03_modelo_normalizado_contactos.sql — modelo normalizado + vista */
CREATE TABLE IF NOT EXISTS public.estado (
  estado_id BIGSERIAL PRIMARY KEY,
  codigo CHAR(2) NOT NULL CHECK (codigo ~ '^[A-Za-z]{2}$'),
  nombre TEXT,
  CONSTRAINT uq_estado_codigo UNIQUE (codigo)
);
CREATE TABLE IF NOT EXISTS public.ciudad (
  ciudad_id BIGSERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  estado_id BIGINT NOT NULL REFERENCES public.estado(estado_id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT uq_ciudad UNIQUE (nombre, estado_id)
);
CREATE TABLE IF NOT EXISTS public.empresa (
  empresa_id BIGSERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  CONSTRAINT uq_empresa_nombre UNIQUE (nombre)
);
CREATE TABLE IF NOT EXISTS public.departamento (
  departamento_id BIGSERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  CONSTRAINT uq_departamento_nombre UNIQUE (nombre)
);
CREATE TABLE IF NOT EXISTS public.contacto (
  contacto_id BIGSERIAL PRIMARY KEY,
  first_name VARCHAR(100) NOT NULL,
  last_name  VARCHAR(100) NOT NULL,
  email      VARCHAR(255) UNIQUE NOT NULL,
  empresa_id BIGINT REFERENCES public.empresa(empresa_id) ON UPDATE CASCADE ON DELETE SET NULL,
  departamento_id BIGINT REFERENCES public.departamento(departamento_id) ON UPDATE CASCADE ON DELETE SET NULL,
  creado_en     TIMESTAMP NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMP NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS public.direccion (
  direccion_id BIGSERIAL PRIMARY KEY,
  contacto_id BIGINT NOT NULL REFERENCES public.contacto(contacto_id) ON UPDATE CASCADE ON DELETE CASCADE,
  ciudad_id BIGINT REFERENCES public.ciudad(ciudad_id) ON UPDATE CASCADE ON DELETE SET NULL,
  address TEXT,
  zip   VARCHAR(10)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_direccion_contacto ON public.direccion(contacto_id);
CREATE TABLE IF NOT EXISTS public.telefono (
  telefono_id BIGSERIAL PRIMARY KEY,
  contacto_id BIGINT NOT NULL REFERENCES public.contacto(contacto_id) ON UPDATE CASCADE ON DELETE CASCADE,
  tipo TEXT NOT NULL CHECK (tipo IN ('principal','alterno')),
  numero VARCHAR(20) NOT NULL,
  CONSTRAINT uq_telefono_contacto_tipo UNIQUE (contacto_id, tipo)
);
CREATE INDEX IF NOT EXISTS idx_contacto_nombre ON public.contacto(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_ciudad_estado ON public.ciudad(estado_id);
CREATE INDEX IF NOT EXISTS idx_direccion_ciudad ON public.direccion(ciudad_id);
INSERT INTO public.estado (codigo)
SELECT DISTINCT upper(state)
FROM public.contactos
WHERE state ~ '^[A-Za-z]{2}$'
ON CONFLICT (codigo) DO NOTHING;
INSERT INTO public.ciudad (nombre, estado_id)
SELECT DISTINCT c.city, e.estado_id
FROM public.contactos c
JOIN public.estado e ON e.codigo = upper(c.state)
WHERE c.city IS NOT NULL AND c.city <> ''
ON CONFLICT (nombre, estado_id) DO NOTHING;
INSERT INTO public.empresa (nombre)
SELECT DISTINCT company_name FROM public.contactos
WHERE company_name IS NOT NULL AND company_name <> ''
ON CONFLICT (nombre) DO NOTHING;
INSERT INTO public.departamento (nombre)
SELECT DISTINCT department FROM public.contactos
WHERE department IS NOT NULL AND department <> ''
ON CONFLICT (nombre) DO NOTHING;
INSERT INTO public.contacto (first_name, last_name, email, empresa_id, departamento_id)
SELECT c.first_name,
       c.last_name,
       lower(c.email),
       (SELECT em.empresa_id FROM public.empresa em WHERE em.nombre = c.company_name),
       (SELECT dp.departamento_id FROM public.departamento dp WHERE dp.nombre = c.department)
FROM public.contactos c
WHERE c.email IS NOT NULL AND c.email <> ''
ON CONFLICT (email) DO UPDATE
  SET first_name = EXCLUDED.first_name,
      last_name  = EXCLUDED.last_name;
INSERT INTO public.direccion (contacto_id, ciudad_id, address, zip)
SELECT ct.contacto_id,
       ci.ciudad_id,
       c.address,
       c.zip
FROM public.contactos c
JOIN public.contacto ct ON ct.email = lower(c.email)
LEFT JOIN public.estado e ON e.codigo = upper(c.state)
LEFT JOIN public.ciudad ci ON ci.nombre = c.city AND ci.estado_id = e.estado_id
ON CONFLICT (contacto_id) DO NOTHING;
INSERT INTO public.telefono (contacto_id, tipo, numero)
SELECT ct.contacto_id, 'principal', c.phone1
FROM public.contactos c
JOIN public.contacto ct ON ct.email = lower(c.email)
WHERE c.phone1 IS NOT NULL AND c.phone1 <> ''
ON CONFLICT (contacto_id, tipo) DO NOTHING;
INSERT INTO public.telefono (contacto_id, tipo, numero)
SELECT ct.contacto_id, 'alterno', c.phone2
FROM public.contactos c
JOIN public.contacto ct ON ct.email = lower(c.email)
WHERE c.phone2 IS NOT NULL AND c.phone2 <> ''
ON CONFLICT (contacto_id, tipo) DO NOTHING;
CREATE OR REPLACE VIEW public.v_contactos_flat AS
SELECT
  ct.first_name,
  ct.last_name,
  em.nombre AS company_name,
  dir.address,
  ci.nombre AS city,
  es.codigo AS state,
  dir.zip,
  t1.numero AS phone1,
  t2.numero AS phone2,
  ct.email,
  dp.nombre AS department
FROM public.contacto ct
LEFT JOIN public.empresa em ON em.empresa_id = ct.empresa_id
LEFT JOIN public.departamento dp ON dp.departamento_id = ct.departamento_id
LEFT JOIN public.direccion dir ON dir.contacto_id = ct.contacto_id
LEFT JOIN public.ciudad ci ON ci.ciudad_id = dir.ciudad_id
LEFT JOIN public.estado es ON es.estado_id = ci.estado_id
LEFT JOIN public.telefono t1 ON t1.contacto_id = ct.contacto_id AND t1.tipo = 'principal'
LEFT JOIN public.telefono t2 ON t2.contacto_id = ct.contacto_id AND t2.tipo = 'alterno';
