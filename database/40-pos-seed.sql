-- =====================================================================
-- RodelSoft Admin - 40-pos-seed.sql
-- Seed oficial POS DB (demo MVP)
-- =====================================================================

SET NAMES utf8mb4;
SET time_zone = '-06:00';

USE pos_db;

-- =========================
-- CATEGORÍAS
-- =========================
INSERT IGNORE INTO pos_categories (id, name, description, color, is_active) VALUES
  (1, 'Bebidas', 'Bebidas', '#0066FF', 1);

-- =========================
-- PRODUCTOS
-- =========================
INSERT IGNORE INTO pos_products (
  id, name, description, price, cost, sku, barcode, category_id, stock_quantity, min_stock, is_active
) VALUES
  (1, 'Coca Cola', 'Refresco 355ml', 10.00, 9.00, '1212', '1212', 1, 84, 10, 1),
  (2, 'Sprite', 'Refresco 355ml', 10.00, 9.00, '1213', '1213', 1, 92, 10, 1),
  (3, 'Chaparrita', 'Refresco 355ml', 10.00, 9.00, '1211', '1211', 1, 90, 10, 1),
  (4, 'Pepsi', 'Refresco 355ml', 10.00, 9.00, '1200', '1200', 1, 95, 10, 1);