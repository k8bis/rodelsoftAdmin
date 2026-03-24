-- =====================================================================
-- RodelSoft Admin - 20-seed.sql
-- Seed oficial Fase 3.1 (datos base de pruebas)
-- =====================================================================

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- =========================
-- USUARIOS
-- =========================
INSERT IGNORE INTO users (id, username, email, password) VALUES
  (1,'admin','admin@rodelsoft.com','adminpass'),
  (2,'admin-rs','admin_garage@rodelsoft.com','adminrs'),
  (3,'admin-gr','admin_realstate@rodelsoft.com','admingr'),
  (4,'agarcia','agarcia@arar.com','artur'),
  (5,'admin-pos','admin_pos@rodelsoft.com','adminpos');

-- =========================
-- ADMINS GLOBALES
-- =========================
INSERT IGNORE INTO system_admins (user_id) VALUES
  (1);

-- =========================
-- CLIENTES
-- =========================
INSERT IGNORE INTO clients (id, name) VALUES
  (1,'RodelSoft'),
  (2,'MEDA gestion de bienes raices'),
  (3,'RoDel blackGarage Mecanica Automotriz'),
  (4,'ARAR Tecnologia y Seguridad');

-- =========================
-- APLICACIONES
-- =========================
INSERT IGNORE INTO applications (
  id, name, slug, description, internal_url, public_url, entry_path, launch_mode
) VALUES
  (1, 'Rodel-RealState', 'rodel-realstate',
     'App de RodelSoft para la gestion de rentas y ventas de bienes raices',
     'http://app-hija-1:8000',
     'http://localhost:8000',
     '/', 'redirect'),

  (2, 'Rodel-Garage', 'rodel-garage',
     'App de RodelSoft para la gestion de mantenimiento y servicio de autos',
     'http://app-hija-2:3002',
     'http://localhost:3002',
     '/', 'redirect'),

  (3, 'Rodel-POS', 'rodel-pos',
     'App de RodelSoft para punto de venta',
     'http://rodelsoft-pos:8000',
     'http://localhost:8001',
     '/', 'redirect');

-- =========================
-- PERMISOS
-- Basado en tu estado real actual de pruebas
-- =========================
INSERT IGNORE INTO permissions (id, user_id, client_id, app_id, role, created_at) VALUES
  (1, 1, 1, 1, 'app_client_admin', '2026-03-21 20:06:09'),
  (2, 1, 1, 2, 'member',           '2026-03-21 20:06:09'),
  (3, 1, 2, 1, 'member',           '2026-03-21 20:06:09'),
  (4, 2, 1, 1, 'member',           '2026-03-21 20:06:09'),
  (5, 2, 2, 1, 'member',           '2026-03-21 20:06:09'),
  (6, 3, 3, 2, 'app_client_admin', '2026-03-21 20:06:09'),
  (7, 4, 4, 3, 'app_client_admin', '2026-03-18 00:00:00'),
  (8, 5, 4, 3, 'app_client_admin', '2026-03-18 00:00:00'),
  (9, 5, 1, 3, 'app_client_admin', '2026-03-18 00:00:00'),
  (10,1, 4, 3, 'app_client_admin', '2026-03-22 19:59:33');