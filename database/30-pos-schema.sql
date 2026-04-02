-- =====================================================================
-- RodelSoft Admin - 30-pos-schema.sql
-- Esquema oficial POS DB (Fase 4.3)
-- =====================================================================

SET NAMES utf8mb4;
SET time_zone = '-06:00';

USE pos_db;

-- =========================
-- CATEGORÍAS
-- =========================
CREATE TABLE IF NOT EXISTS pos_categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT NULL,
  color VARCHAR(7) NULL DEFAULT '#0066FF',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_pos_categories_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- PRODUCTOS
-- =========================
CREATE TABLE IF NOT EXISTS pos_products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  description TEXT NULL,
  price DECIMAL(12,2) NOT NULL,
  cost DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  sku VARCHAR(50) NULL,
  barcode VARCHAR(50) NULL,
  category_id INT NULL,
  stock_quantity INT NOT NULL DEFAULT 0,
  min_stock INT NOT NULL DEFAULT 0,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  image_url VARCHAR(500) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_pos_products_category
    FOREIGN KEY (category_id) REFERENCES pos_categories(id)
    ON DELETE SET NULL,

  UNIQUE KEY uniq_pos_products_sku (sku),
  UNIQUE KEY uniq_pos_products_barcode (barcode),
  KEY idx_pos_products_category (category_id),
  KEY idx_pos_products_active (is_active),
  KEY idx_pos_products_stock (stock_quantity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- VENTAS
-- IMPORTANTE:
-- client_id / app_id / created_by ya quedan obligatorios
-- =========================
CREATE TABLE IF NOT EXISTS pos_sales (
  id INT AUTO_INCREMENT PRIMARY KEY,

  client_id INT NOT NULL,
  app_id INT NOT NULL,
  created_by VARCHAR(100) NOT NULL,

  total_amount DECIMAL(12,2) NOT NULL,
  tax_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  discount_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  payment_method VARCHAR(50) NOT NULL DEFAULT 'cash',
  status VARCHAR(20) NOT NULL DEFAULT 'completed',
  notes TEXT NULL,

  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,

  KEY idx_pos_sales_client (client_id),
  KEY idx_pos_sales_app (app_id),
  KEY idx_pos_sales_created_by (created_by),
  KEY idx_pos_sales_created_at (created_at),
  KEY idx_pos_sales_client_app_date (client_id, app_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================
-- DETALLE DE VENTA
-- =========================
CREATE TABLE IF NOT EXISTS pos_sale_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sale_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(12,2) NOT NULL,
  total_price DECIMAL(12,2) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_pos_sale_items_sale
    FOREIGN KEY (sale_id) REFERENCES pos_sales(id)
    ON DELETE CASCADE,

  CONSTRAINT fk_pos_sale_items_product
    FOREIGN KEY (product_id) REFERENCES pos_products(id)
    ON DELETE RESTRICT,

  KEY idx_pos_sale_items_sale (sale_id),
  KEY idx_pos_sale_items_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;