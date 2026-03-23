-- =====================================================================
-- RodelSoft Admin - SEED (FASE 3)
-- =====================================================================

-- Usuarios
INSERT IGNORE INTO users (id, username, email, password) VALUES
  (1,'admin','admin@rodelsoft.com','adminpass'),
  (2,'admin-rs','admin_garage@trodelsoft.com','adminrs'),
  (3,'admin-gr','admin_realstate@rodelsoft.com','admingr',
  (4,'agarcia','agarcia@arar.com','artur'),
  (5,'admin-pos','admin_pos@rodelsoft.com','adminpos');

-- Admin global
INSERT IGNORE INTO system_admins (user_id) VALUES (1);

-- Clientes
INSERT IGNORE INTO clients (id, name) VALUES
  (1,'RodelSoft'),
  (2,'MEDA gestion de bienes raices'),
  (3,'RoDel blackGarage Mecanica Automotriz'),
  (4,'ARAR Tecnologia y Seguridad');

-- Aplicaciones (modelo profesional)
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

-- Permisos con rol por tenencia
INSERT IGNORE INTO permissions (user_id, client_id, app_id, role) VALUES
  (1,1,1,'member'),
  (1,1,2,'member'),
  (1,2,1,'member'),
  (1,4,3,'member'),

  (2,1,1,'member'),
  (2,2,1,'member'),

  (3,3,2,'member'),
  
  (4, 4, 3, 'member'),

  (5, 4, 3, 'member'),
  (5, 1, 3, 'member');