-- 02_validate_state.sql — Valida que public.contactos.state tenga longitud=2 y solo letras (A-Z)
-- Se asume que `01_init.sql` y `02_seed_contactos.sh` ya corrieron y cargaron datos en `public.contactos`.

\set ON_ERROR_STOP on

DO $$
DECLARE
  invalid_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO invalid_count
  FROM public.contactos
  WHERE state IS NULL
     OR char_length(state) <> 2
     OR state !~ '^[A-Za-z]{2}$';

  IF invalid_count > 0 THEN
    RAISE EXCEPTION 'Validación falló: % filas con "state" inválido (NULL, !=2 o no alfabético). Ejemplos: %',
      invalid_count,
      (SELECT string_agg(coalesce(state,'<NULL>') || ':' || email, ', ')
         FROM (
           SELECT state, email
           FROM public.contactos
           WHERE state IS NULL
              OR char_length(state) <> 2
              OR state !~ '^[A-Za-z]{2}$'
           LIMIT 5
         ) t);
  END IF;
END $$;

-- Al pasar la validación, agregamos una restricción CHECK para futuros inserts/updates
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_contactos_state_alpha2'
  ) THEN
    ALTER TABLE public.contactos
      ADD CONSTRAINT chk_contactos_state_alpha2
      CHECK (state IS NOT NULL AND char_length(state)=2 AND state ~ '^[A-Za-z]{2}$');
  END IF;
END $$;

-- Info de control
SELECT COUNT(*) AS filas_ok FROM public.contactos;
