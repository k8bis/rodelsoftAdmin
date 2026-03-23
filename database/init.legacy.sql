-- =====================================================================
-- RodelSoft Admin - INIT (MySQL 8, InnoDB, utf8mb4)
-- Esquema completo con catálogo de aplicaciones (slug/upstream) y
-- permisos con rol por (user_id, client_id, app_id)
-- =====================================================================

SET NAMES utf8mb4;
SET time_zone = '+00:00';

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
-- APLICACIONES (catálogo)
--  - slug: identificador legible y único (deep-link)
--  - upstream: destino al que Nginx debe enrutar
--  - entry_path: ruta base dentro del servicio (normalmente '/')
-- =========================
CREATE TABLE IF NOT EXISTS applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  slug VARCHAR(120) NOT NULL,
  description TEXT,
  upstream VARCHAR(255) NOT NULL DEFAULT 'http://app-hija-1:8000',
  entry_path VARCHAR(120) NOT NULL DEFAULT '/',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_app_name (name),
  UNIQUE KEY uniq_app_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- PERMISOS
--  - relación N:M con alcance (usuario + cliente + app)
--  - role: control de administración por tenencia (app+cliente)
-- =========================
CREATE TABLE IF NOT EXISTS permissions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  client_id INT NOT NULL,
  app_id INT NOT NULL,
  role ENUM('app_client_admin','member') NOT NULL DEFAULT 'member',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_permissions_user    FOREIGN KEY (user_id)  REFERENCES users(id)        ON DELETE CASCADE,
  CONSTRAINT fk_permissions_client  FOREIGN KEY (client_id) REFERENCES clients(id)      ON DELETE CASCADE,
  CONSTRAINT fk_permissions_app     FOREIGN KEY (app_id)   REFERENCES applications(id)  ON DELETE CASCADE,
  UNIQUE KEY uniq_user_client_app (user_id, client_id, app_id),
  KEY idx_permissions_user (user_id),
  KEY idx_permissions_client (client_id),
  KEY idx_permissions_app (app_id),
  KEY idx_perm_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- ADMINS GLOBALES (opcional)
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
  a.upstream     AS upstream,
  a.entry_path   AS entry_path,
  p.role         AS role,
  p.created_at   AS granted_at
FROM permissions p
JOIN users u   ON u.id = p.user_id
JOIN clients c ON c.id = p.client_id
JOIN applications a ON a.id = p.app_id;

-- =====================================================================
-- SEEDS
-- =====================================================================

-- Usuarios
INSERT IGNORE INTO users (id, username, email, password) VALUES
  (1,'admin','admin@rodelsoft.com','adminpass'),
  (2,'admin-rs','admin_garage@trodelsoft.com','adminrs'),
  (3,'admin-gr','admin_realstate@rodelsoft.com','admingr');

-- Admin global
INSERT IGNORE INTO system_admins (user_id) VALUES (1);

-- Clientes
INSERT IGNORE INTO clients (id, name) VALUES
  (1,'RodelSoft'),
  (2,'MEDA gestion de bienes raices'),
  (3,'RoDel blackGarage Mecanica Automotriz');

-- Aplicaciones (ajusta upstream según docker-compose)
INSERT IGNORE INTO applications (id, name, slug, description, upstream, entry_path) VALUES
  (1, 'Rodel-RealState', 'rodel-realstate',
     'App de RodelSoft para la gestion de rentas y ventas de bienes raices',
     'http://app-hija-1:8000', '/'),
  (2, 'Rodel-Garage', 'rodel-garage',
     'App de RodelSoft para la gestion de mantenimiento y servicio de autos',
     'http://app-hija-2:3002', '/');

-- Permisos con rol por tenencia
INSERT IGNORE INTO permissions (user_id, client_id, app_id, role) VALUES
  (1,1,1,'app_client_admin'), -- admin   en RodelSoft + RealState
  (1,1,2,'member'),           -- admin   en RodelSoft + Garage
  (1,2,1,'member'),           -- admin   en MEDA      + RealState

  (2,1,1,'member'),           -- admin-rs en RodelSoft + RealState
  (2,2,1,'member'),           -- admin-rs en MEDA      + RealState

  (3,3,2,'app_client_admin'); -- admin-gr en blackGarage + Garage
