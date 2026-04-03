-- =====================================================================
-- RodelSoft Admin - 20-seed.sql
-- Seed oficial Fase 9.3 (DEV/DEMO endurecido)
-- =====================================================================

SET NAMES utf8mb4;
SET time_zone = '-06:00';

-- =========================
-- USUARIOS
-- =========================
-- NOTA FASE 9.3:
-- Seeds solo para entorno DEV/DEMO.
-- Passwords de ejemplo intencionalmente no productivas.
-- El login de app-hija-1 migra automáticamente a bcrypt al primer login exitoso.
-- Usuarios creados desde authz-service ya se almacenan con bcrypt.
INSERT IGNORE INTO users (id, username, email, password) VALUES
  (1,'admin','admin@rodelsoft.local','ChangeMe-Admin-123!'),
  (2,'admin-rs','admin_garage@rodelsoft.local','ChangeMe-Garage-123!'),
  (3,'admin-gr','admin_realstate@rodelsoft.local','ChangeMe-RealState-123!'),
  (4,'agarcia','agarcia@demo.local','ChangeMe-User-123!'),
  (5,'admin-pos','admin_pos@rodelsoft.local','ChangeMe-POS-123!');

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
     '/app2/',
     '/', 'redirect'),

  (2, 'Rodel-Garage', 'rodel-garage',
     'App de RodelSoft para la gestion de mantenimiento y servicio de autos',
     'http://app-hija-2:3002',
     '/app2/',
     '/', 'redirect'),

  (3, 'Rodel-POS', 'rodel-pos',
     'App de RodelSoft para punto de venta',
     'http://rodelsoft-pos:8000',
     '/pos/',
     '/', 'redirect'),

  (4, 'RodelSoft Notes External', 'rodelsoft-notes-external',
     'Primera app externa real fuera del stack principal',
     'http://192.168.100.26:8010',
     '/notes/',
     '/', 'dynamic_proxy');

-- =========================
-- MEMBRESIAS USUARIO-CLIENTE
-- =========================
-- Estructura real validada en proyecto: user_client_memberships existe
-- y se usa como control de pertenencia por cliente.
INSERT IGNORE INTO user_client_memberships
  (user_id, client_id, role, status, created_by)
VALUES
  (1, 1, 'owner', 'active', 'seed'),
  (2, 3, 'client_admin', 'active', 'seed'),
  (3, 2, 'client_admin', 'active', 'seed'),
  (4, 4, 'client_admin', 'active', 'seed'),
  (5, 1, 'client_admin', 'active', 'seed');

-- =========================
-- SUSCRIPCIONES CLIENTE-APP
-- =========================
-- Estructura real validada: client_app_subscriptions con status / is_enabled
INSERT IGNORE INTO client_app_subscriptions
  (client_id, app_id, status, plan_code, start_date, end_date, is_enabled, created_by, notes)
VALUES
  (1, 1, 'active', 'internal', NOW(), NULL, 1, 'seed', 'RodelSoft acceso interno'),
  (1, 2, 'active', 'internal', NOW(), NULL, 1, 'seed', 'RodelSoft acceso interno'),
  (1, 3, 'active', 'internal', NOW(), NULL, 1, 'seed', 'RodelSoft acceso interno'),
  (1, 4, 'active', 'internal', NOW(), NULL, 1, 'seed', 'RodelSoft acceso interno'),

  (2, 1, 'active', 'demo', NOW(), DATE_ADD(NOW(), INTERVAL 90 DAY), 1, 'seed', 'Demo MEDA'),
  (3, 2, 'active', 'demo', NOW(), DATE_ADD(NOW(), INTERVAL 90 DAY), 1, 'seed', 'Demo Garage'),
  (4, 3, 'active', 'demo', NOW(), DATE_ADD(NOW(), INTERVAL 90 DAY), 1, 'seed', 'Demo POS');

-- =========================
-- PERMISOS
-- =========================
-- roles válidos reales usados en proyecto:
-- app_client_admin, member
INSERT IGNORE INTO permissions (user_id, client_id, app_id, role) VALUES
  (1, 1, 1, 'app_client_admin'),
  (1, 1, 2, 'app_client_admin'),
  (1, 1, 3, 'app_client_admin'),
  (1, 1, 4, 'app_client_admin'),

  (2, 3, 2, 'app_client_admin'),
  (3, 2, 1, 'app_client_admin'),
  (4, 4, 3, 'app_client_admin'),
  (5, 1, 3, 'app_client_admin');