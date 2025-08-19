SET client_min_messages = WARNING;
CREATE SCHEMA IF NOT EXISTS public;

CREATE TABLE IF NOT EXISTS public.estado (
  estado_id SERIAL PRIMARY KEY,
  codigo    VARCHAR(2) UNIQUE NOT NULL,
  nombre    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS public.ciudad (
  ciudad_id SERIAL PRIMARY KEY,
  nombre    TEXT NOT NULL,
  estado_id INTEGER NOT NULL REFERENCES public.estado(estado_id) ON DELETE RESTRICT,
  CONSTRAINT ciudad_unq UNIQUE (nombre, estado_id)
);

CREATE TABLE IF NOT EXISTS public.empresa (
  empresa_id SERIAL PRIMARY KEY,
  nombre     TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS public.departamento (
  departamento_id SERIAL PRIMARY KEY,
  nombre          TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS public.contacto (
  contacto_id     SERIAL PRIMARY KEY,
  first_name      TEXT NOT NULL,
  last_name       TEXT NOT NULL,
  email           TEXT UNIQUE NOT NULL,
  empresa_id      INTEGER REFERENCES public.empresa(empresa_id) ON DELETE SET NULL,
  departamento_id INTEGER REFERENCES public.departamento(departamento_id) ON DELETE SET NULL,
  creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.direccion (
  contacto_id INTEGER PRIMARY KEY REFERENCES public.contacto(contacto_id) ON DELETE CASCADE,
  ciudad_id   INTEGER REFERENCES public.ciudad(ciudad_id) ON DELETE SET NULL,
  address     TEXT,
  zip         TEXT
);

CREATE TABLE IF NOT EXISTS public.telefono (
  contacto_id INTEGER NOT NULL REFERENCES public.contacto(contacto_id) ON DELETE CASCADE,
  tipo        TEXT NOT NULL,
  numero      TEXT NOT NULL,
  PRIMARY KEY (contacto_id, tipo)
);

CREATE TABLE IF NOT EXISTS public.contactos (
  first_name   TEXT,
  last_name    TEXT,
  company_name TEXT,
  address      TEXT,
  city         TEXT,
  state        TEXT,
  zip          TEXT,
  phone1       TEXT,
  phone2       TEXT,
  email        TEXT UNIQUE,
  department   TEXT
);

CREATE OR REPLACE FUNCTION public.touch_actualizado_en() RETURNS trigger AS $$
BEGIN
  NEW.actualizado_en := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS contacto_touch ON public.contacto;
CREATE TRIGGER contacto_touch
BEFORE UPDATE ON public.contacto
FOR EACH ROW EXECUTE FUNCTION public.touch_actualizado_en();
