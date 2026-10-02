CREATE DATABASE IF NOT EXISTS bd_turbidez;
USE bd_turbidez;

-- Limpieza de estructura previa
DROP TABLE IF EXISTS comandos;
DROP TABLE IF EXISTS lecturas;
DROP TABLE IF EXISTS sensor_temperatura;
DROP TABLE IF EXISTS sensor_ph;
DROP TABLE IF EXISTS sensor_turbidez;
DROP TABLE IF EXISTS sensor_profundidad;
DROP TABLE IF EXISTS config_estado;

-- 1. Tablas independientes solo para los 3 sensores físicos reales
CREATE TABLE sensor_temperatura (
    id INT AUTO_INCREMENT PRIMARY KEY,
    valor FLOAT NOT NULL
) ENGINE=InnoDB;

CREATE TABLE sensor_ph (
    id INT AUTO_INCREMENT PRIMARY KEY,
    valor FLOAT NOT NULL
) ENGINE=InnoDB;

CREATE TABLE sensor_turbidez (
    id INT AUTO_INCREMENT PRIMARY KEY,
    valor FLOAT NOT NULL
) ENGINE=InnoDB;

-- 2. Tabla Relacional 'lecturas'
-- Almacena referencias a los 3 sensores físicos + la profundidad fijada manualmente
CREATE TABLE lecturas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_temperatura INT NOT NULL,
    id_ph INT NOT NULL,
    id_turbidez INT NOT NULL,
    profundidad FLOAT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_temperatura FOREIGN KEY (id_temperatura) REFERENCES sensor_temperatura(id) ON DELETE CASCADE,
    CONSTRAINT fk_ph FOREIGN KEY (id_ph) REFERENCES sensor_ph(id) ON DELETE CASCADE,
    CONSTRAINT fk_turbidez FOREIGN KEY (id_turbidez) REFERENCES sensor_turbidez(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Tabla de Comandos para el control de bombas
CREATE TABLE comandos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comando CHAR(1) NOT NULL,
    ejecutado TINYINT DEFAULT 0,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;