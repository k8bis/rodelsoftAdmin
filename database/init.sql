-- Crear tablas base (InnoDB y utf8mb4)
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(100) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS clients (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_client_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Catálogo de aplicaciones
CREATE TABLE IF NOT EXISTS applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_app_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Permisos (usuario + cliente + app)
CREATE TABLE IF NOT EXISTS permissions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  client_id INT NOT NULL,
  app_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_permissions_user   FOREIGN KEY (user_id)  REFERENCES users(id)    ON DELETE CASCADE,
  CONSTRAINT fk_permissions_client FOREIGN KEY (client_id) REFERENCES clients(id)  ON DELETE CASCADE,
  CONSTRAINT fk_permissions_app    FOREIGN KEY (app_id)   REFERENCES applications(id) ON DELETE CASCADE,
  UNIQUE KEY uniq_user_client_app (user_id, client_id, app_id),
  KEY idx_permissions_user (user_id),
  KEY idx_permissions_client (client_id),
  KEY idx_permissions_app (app_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seeds
INSERT IGNORE INTO users (id, username, email, password) VALUES
(1,'admin','admin@rodelsoft.com','adminpass'),
(2,'admin-rs','admin_garage@trodelsoft.com','adminrs'),
(3,'admin-gr','admin_realstate@rodelsoft.com','admingr');

INSERT IGNORE INTO clients (id, name) VALUES
(1,'RodelSoft'),
(2,'MEDA gestion de bienes raices'),
(3,'RoDel blackGarage Mecanica Automotriz');

INSERT IGNORE INTO applications (id, name, description) VALUES
(1,'Rodel-RealState','App de RodelSoft para la gestion de rentas y ventas de bienes raices'),
(2,'Rodel-Garage','App de RodelSoft para la gestion de mantenimiento y servicio de autos');

INSERT IGNORE INTO permissions (user_id, client_id, app_id) VALUES
(1,1,1), -- admin       - RodelSoft     - Rodel-RealState
(1,1,2), -- admin       - RodelSoft     - Rodel-Garage
(1,2,1), -- admin       - MEDA          - Rodel-RealState
(1,3,2), -- admin       - blackGarage   - Rodel-Garage
(2,1,1), -- admin-rs    - RodelSoft     - Rodel-RealState
(2,2,1), -- admin-rs    - MEDA          - Rodel-RealState
(3,1,2), -- admin-rs    - RodelSoft     - Rodel-Garage
(3,3,2); -- admin-gr    - blackGarage   - Rodel-Garage
