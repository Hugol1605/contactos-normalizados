-- 01_init.sql — estructura staging + trigger de actualización
SET client_min_messages TO warning;
CREATE SCHEMA IF NOT EXISTS public;
CREATE TABLE IF NOT EXISTS public.contactos (
  contacto_id   BIGSERIAL PRIMARY KEY,
  first_name    VARCHAR(100) NOT NULL,
  last_name     VARCHAR(100) NOT NULL,
  company_name  VARCHAR(255),
  address       VARCHAR(255),
  city          VARCHAR(120),
  state         CHAR(2) NOT NULL CHECK (state ~ '^[A-Za-z]{2}$'),
  zip           VARCHAR(10),
  phone1        VARCHAR(20),
  phone2        VARCHAR(20),
  email         VARCHAR(255) UNIQUE NOT NULL,
  department    VARCHAR(150),
  creado_en     TIMESTAMP NOT NULL DEFAULT now(),
  actualizado_en TIMESTAMP NOT NULL DEFAULT now()
);
CREATE OR REPLACE FUNCTION public.touch_actualizado_en()
RETURNS trigger AS $$
BEGIN
  NEW.actualizado_en := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_touch_actualizado_en') THEN
    CREATE TRIGGER trg_touch_actualizado_en
      BEFORE UPDATE ON public.contactos
      FOR EACH ROW EXECUTE FUNCTION public.touch_actualizado_en();
  END IF;
END;
$$;
