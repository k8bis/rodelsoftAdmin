-- =====================================================================
-- RodelSoft Admin - 10-schema.sql
-- Modelo oficial Fase 3.1 (solo estructura)
-- =====================================================================

SET NAMES utf8mb4;
SET time_zone = '-06:00';

-- =========================
-- USUARIOS
-- =========================
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(100) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- CLIENTES
-- =========================
CREATE TABLE IF NOT EXISTS clients (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_client_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- APLICACIONES
-- =========================
CREATE TABLE IF NOT EXISTS applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  slug VARCHAR(120) NOT NULL,
  description TEXT,
  internal_url VARCHAR(255) NOT NULL,
  public_url VARCHAR(255) NOT NULL,
  entry_path VARCHAR(120) NOT NULL DEFAULT '/',
  launch_mode ENUM('redirect','dynamic_proxy') NOT NULL DEFAULT 'redirect',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  health_path VARCHAR(120) NOT NULL DEFAULT '/health',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  UNIQUE KEY uniq_app_name (name),
  UNIQUE KEY uniq_app_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- PERMISOS
-- =========================
CREATE TABLE IF NOT EXISTS permissions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  client_id INT NOT NULL,
  app_id INT NOT NULL,
  role ENUM('app_client_admin','member') NOT NULL DEFAULT 'member',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_permissions_user    FOREIGN KEY (user_id) REFERENCES users(id)       ON DELETE CASCADE,
  CONSTRAINT fk_permissions_client  FOREIGN KEY (client_id) REFERENCES clients(id)    ON DELETE CASCADE,
  CONSTRAINT fk_permissions_app     FOREIGN KEY (app_id) REFERENCES applications(id)  ON DELETE CASCADE,
  UNIQUE KEY uniq_user_client_app (user_id, client_id, app_id),
  KEY idx_permissions_user (user_id),
  KEY idx_permissions_client (client_id),
  KEY idx_permissions_app (app_id),
  KEY idx_perm_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- ADMINS GLOBALES
-- =========================
CREATE TABLE IF NOT EXISTS system_admins (
  user_id INT PRIMARY KEY,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_sysadmin_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- VISTA de conveniencia
-- =========================
CREATE OR REPLACE VIEW v_user_permissions AS
SELECT
  u.id           AS user_id,
  u.username     AS username,
  c.id           AS client_id,
  c.name         AS client,
  a.id           AS app_id,
  a.name         AS app,
  a.slug         AS app_slug,
  a.internal_url AS internal_url,
  a.public_url   AS public_url,
  a.entry_path   AS entry_path,
  a.launch_mode  AS launch_mode,
  p.role         AS role,
  p.created_at   AS granted_at
FROM permissions p
JOIN users u   ON u.id = p.user_id
JOIN clients c ON c.id = p.client_id
JOIN applications a ON a.id = p.app_id;