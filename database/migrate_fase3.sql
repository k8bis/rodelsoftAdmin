-- ==========================================================
-- MIGRACIÓN FASE 3 - applications
-- ==========================================================

-- 1) Agregar columnas nuevas
ALTER TABLE applications
  ADD COLUMN internal_url VARCHAR(255) NULL AFTER description,
  ADD COLUMN public_url   VARCHAR(255) NULL AFTER internal_url,
  ADD COLUMN launch_mode ENUM('redirect','dynamic_proxy') NOT NULL DEFAULT 'redirect' AFTER entry_path;

-- 2) Migrar datos desde upstream -> internal_url
UPDATE applications
SET internal_url = upstream
WHERE internal_url IS NULL;

-- 3) Definir public_url según app actual
UPDATE applications
SET public_url = 'http://localhost:8000'
WHERE id = 1 AND (public_url IS NULL OR public_url = '');

UPDATE applications
SET public_url = 'http://localhost:3002'
WHERE id = 2 AND (public_url IS NULL OR public_url = '');

UPDATE applications
SET public_url = 'http://localhost:8001'
WHERE id = 3 AND (public_url IS NULL OR public_url = '');

-- 4) Asegurar launch_mode
UPDATE applications
SET launch_mode = 'redirect'
WHERE launch_mode IS NULL OR launch_mode = '';

-- 5) Hacer obligatorias las nuevas columnas
ALTER TABLE applications
  MODIFY COLUMN internal_url VARCHAR(255) NOT NULL,
  MODIFY COLUMN public_url   VARCHAR(255) NOT NULL;

-- ==========================================================
-- NOTA:
-- upstream se conserva temporalmente por compatibilidad.
-- Lo quitaremos después si quieres en una fase posterior.
-- ==========================================================
ALTER TABLE applications
  ADD COLUMN health_path VARCHAR(120) NOT NULL DEFAULT '/health' AFTER updated_at,
  ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1 AFTER health_path;