-- Script de creación de base de datos para RPA Productos
-- SQLite Database Schema

-- Crear tabla de productos
CREATE TABLE IF NOT EXISTS Productos (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    price REAL NOT NULL CHECK (price > 0),
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    fecha_insercion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_productos_category ON Productos(category);
CREATE INDEX IF NOT EXISTS idx_productos_price ON Productos(price);
CREATE INDEX IF NOT EXISTS idx_productos_fecha ON Productos(fecha_insercion);

-- Crear vista para estadísticas por categoría
CREATE VIEW IF NOT EXISTS v_estadisticas_categoria AS
SELECT 
    category,
    COUNT(*) as total_productos,
    AVG(price) as precio_promedio,
    MIN(price) as precio_minimo,
    MAX(price) as precio_maximo,
    MAX(fecha_insercion) as ultima_actualizacion
FROM Productos
GROUP BY category
ORDER BY total_productos DESC;

-- Crear vista para resumen general
CREATE VIEW IF NOT EXISTS v_resumen_general AS
SELECT 
    COUNT(*) as total_productos,
    AVG(price) as precio_promedio_general,
    MIN(price) as precio_minimo_general,
    MAX(price) as precio_maximo_general,
    COUNT(DISTINCT category) as total_categorias,
    MAX(fecha_insercion) as ultima_actualizacion
FROM Productos;

-- Insertar datos de configuración (opcional)
CREATE TABLE IF NOT EXISTS configuracion (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    descripcion TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configuraciones iniciales
INSERT OR IGNORE INTO configuracion (clave, valor, descripcion) VALUES
('version_schema', '1.0', 'Versión del esquema de base de datos'),
('fecha_creacion', datetime('now'), 'Fecha de creación de la base de datos'),
('proyecto', 'RPA_Productos_PIX', 'Nombre del proyecto RPA');

-- Trigger para actualizar fecha de modificación
CREATE TRIGGER IF NOT EXISTS trigger_productos_update 
    AFTER UPDATE ON Productos
    FOR EACH ROW
BEGIN
    UPDATE Productos 
    SET fecha_insercion = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Comentarios sobre el esquema
-- La tabla Productos almacena la información básica de cada producto
-- Los índices mejoran el rendimiento de consultas por categoría, precio y fecha
-- Las vistas proporcionan estadísticas precalculadas
-- El trigger mantiene actualizada la fecha de modificación
