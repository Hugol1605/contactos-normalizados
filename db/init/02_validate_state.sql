DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'estado_codigo_chk'
  ) THEN
    ALTER TABLE public.estado
      ADD CONSTRAINT estado_codigo_chk
      CHECK (codigo ~ '^[A-Za-z]{2}$');
  END IF;
END $$;
