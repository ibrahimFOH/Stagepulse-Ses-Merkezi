ALTER TABLE public.sesm_store_settings
  ADD COLUMN IF NOT EXISTS measurement_settings jsonb NOT NULL
  DEFAULT '{"advanced_rta_enabled": true, "microphone_correction_enabled": true}'::jsonb;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'sesm_store_settings_measurement_settings_object'
      AND conrelid = 'public.sesm_store_settings'::regclass
  ) THEN
    ALTER TABLE public.sesm_store_settings
      ADD CONSTRAINT sesm_store_settings_measurement_settings_object
      CHECK (jsonb_typeof(measurement_settings) = 'object');
  END IF;
END
$$;
