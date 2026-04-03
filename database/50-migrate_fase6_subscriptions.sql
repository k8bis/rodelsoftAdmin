-- =========================================================
-- RodelSoft Platform
-- FASE 6.0.A / Bootstrap compatible
-- Hardening de modelo actual + suscripciones + memberships
-- =========================================================

USE proyecto_db;

SET NAMES utf8mb4;
SET time_zone = '-06:00';

-- ---------------------------------------------------------
-- 1) Crear client_app_subscriptions (si no existe)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS client_app_subscriptions (
  id INT NOT NULL AUTO_INCREMENT,
  client_id INT NOT NULL,
  app_id INT NOT NULL,
  status enum('trial','active','suspended','expired') NOT NULL DEFAULT 'trial',
  plan_code varchar(50) DEFAULT NULL,
  start_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  end_date DATETIME NULL,
  is_enabled tinyint(1) NOT NULL DEFAULT '1',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
  created_by varchar(100) DEFAULT NULL,
  notes varchar(255) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cas_client_app (client_id, app_id),
  KEY idx_cas_client (client_id),
  KEY idx_cas_app (app_id),
  KEY idx_cas_status (status),
  CONSTRAINT fk_cas_client
    FOREIGN KEY (client_id) REFERENCES clients(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_cas_app
    FOREIGN KEY (app_id) REFERENCES applications(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------
-- 2) Crear user_client_memberships (si no existe)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_client_memberships (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  client_id INT NOT NULL,
  role ENUM('client_admin','member') NOT NULL DEFAULT 'member',
  status ENUM('active','inactive') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_ucm_user_client (user_id, client_id),
  KEY idx_ucm_user (user_id),
  KEY idx_ucm_client (client_id),
  KEY idx_ucm_role (role),
  KEY idx_ucm_status (status),
  CONSTRAINT fk_ucm_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_ucm_client
    FOREIGN KEY (client_id) REFERENCES clients(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------------------------
-- 3) Backfill memberships desde permissions
-- ---------------------------------------------------------
INSERT INTO user_client_memberships (user_id, client_id, role, status)
SELECT
  p.user_id,
  p.client_id,
  CASE
    WHEN MAX(CASE WHEN p.role = 'app_client_admin' THEN 1 ELSE 0 END) = 1
      THEN 'client_admin'
    ELSE 'member'
  END AS role,
  'active' AS status
FROM permissions p
GROUP BY p.user_id, p.client_id
ON DUPLICATE KEY UPDATE
  role = VALUES(role),
  status = 'active';

-- ---------------------------------------------------------
-- 4) Backfill subscriptions desde permissions
--    Regla: si existe permiso client+app, existe suscripción activa
-- ---------------------------------------------------------
INSERT INTO client_app_subscriptions (
  client_id,
  app_id,
  status,
  plan_code,
  start_date,
  is_enabled,
  created_by,
  notes
)
SELECT
  p.client_id,
  p.app_id,
  'active' AS status,
  'legacy-bootstrap' AS plan_code,
  CURRENT_TIMESTAMP AS start_date,
  1 AS is_enabled,
  'fase9-bootstrap' AS created_by,
  'Backfill inicial desde permissions' AS notes
FROM permissions p
GROUP BY p.client_id, p.app_id
ON DUPLICATE KEY UPDATE
  status = 'active',
  is_enabled = 1;

-- ---------------------------------------------------------
-- 5) Corregir vista v_user_permissions
-- ---------------------------------------------------------
DROP VIEW IF EXISTS v_user_permissions;

CREATE VIEW v_user_permissions AS
SELECT
  u.id AS user_id,
  u.username AS username,
  c.id AS client_id,
  c.name AS client,
  a.id AS app_id,
  a.name AS app,
  a.slug AS app_slug,
  a.internal_url AS internal_url,
  a.public_url AS public_url,
  a.entry_path AS entry_path,
  p.role AS role,
  p.created_at AS granted_at
FROM permissions p
JOIN users u ON u.id = p.user_id
JOIN clients c ON c.id = p.client_id
JOIN applications a ON a.id = p.app_id;

-- ---------------------------------------------------------
-- 6) Validación rápida manual
-- ---------------------------------------------------------
-- SHOW TABLES;
-- SELECT * FROM user_client_memberships;
-- SELECT * FROM client_app_subscriptions;
-- SHOW CREATE VIEW v_user_permissions;