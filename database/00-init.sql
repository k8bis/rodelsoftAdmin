-- =====================================================================
-- RodelSoft Admin - 00-init.sql
-- Bootstrap mínimo para contenedor MySQL
-- =====================================================================

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- Si tu contenedor ya crea la DB por MYSQL_DATABASE, esto es suficiente.
-- Si quisieras forzar creación manual en otro escenario:
-- CREATE DATABASE IF NOT EXISTS proyecto_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE proyecto_db;