-- ============================================================================
-- SCRIPT: Crear Índices Trigram para Optimización de Búsquedas
-- Módulo: theme_bohio_real_estate
-- Propósito: Mejorar rendimiento de autocompletado y búsquedas parciales
-- Mejora Esperada: 20-25x más rápido en búsquedas parciales
-- ============================================================================

-- PASO 1: Verificar y crear extensión pg_trgm
-- ============================================================================
-- NOTA: Requiere permisos de superusuario en PostgreSQL
-- Si no tienes permisos, pide al DBA que ejecute esta línea

DO $$
BEGIN
    -- Intentar crear extensión (solo si no existe)
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    RAISE NOTICE 'Extensión pg_trgm verificada/creada exitosamente';
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'No se pudo crear pg_trgm. Requiere permisos de superusuario. Error: %', SQLERRM;
END $$;

-- Verificar que pg_trgm esté disponible
SELECT
    CASE
        WHEN COUNT(*) > 0 THEN 'pg_trgm está instalado correctamente'
        ELSE 'pg_trgm NO está instalado - Los índices no funcionarán'
    END as status
FROM pg_extension
WHERE extname = 'pg_trgm';


-- PASO 2: Verificar función unaccent (ya debería estar en Odoo)
-- ============================================================================
SELECT
    CASE
        WHEN COUNT(*) > 0 THEN 'unaccent está disponible'
        ELSE 'unaccent NO está disponible - Considerar instalar unaccent extension'
    END as status
FROM pg_proc
WHERE proname = 'unaccent';


-- PASO 3: Crear Índices Trigram para res.city (Ciudades)
-- ============================================================================
-- Índice trigram básico para búsquedas parciales
DROP INDEX IF EXISTS idx_res_city_name_trgm;
CREATE INDEX idx_res_city_name_trgm
ON res_city USING gin (name gin_trgm_ops);

-- Índice trigram con unaccent para búsquedas sin acentos
-- IMPORTANTE: Solo crear si unaccent está disponible
DO $$
BEGIN
    DROP INDEX IF EXISTS idx_res_city_name_trgm_unaccent;

    -- Verificar si unaccent existe
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'unaccent') THEN
        -- Crear índice funcional con unaccent
        EXECUTE 'CREATE INDEX idx_res_city_name_trgm_unaccent
                 ON res_city USING gin (unaccent(name) gin_trgm_ops)';
        RAISE NOTICE 'Índice unaccent para res_city creado';
    ELSE
        RAISE WARNING 'unaccent no disponible - Índice unaccent NO creado';
    END IF;
END $$;

-- Verificar creación
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE tablename = 'res_city'
    AND indexname LIKE '%trgm%'
ORDER BY indexname;


-- PASO 4: Crear Índices Trigram para region.region (Barrios)
-- ============================================================================
DROP INDEX IF EXISTS idx_region_region_name_trgm;
CREATE INDEX idx_region_region_name_trgm
ON region_region USING gin (name gin_trgm_ops);

-- Índice con unaccent
DO $$
BEGIN
    DROP INDEX IF EXISTS idx_region_region_name_trgm_unaccent;

    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'unaccent') THEN
        EXECUTE 'CREATE INDEX idx_region_region_name_trgm_unaccent
                 ON region_region USING gin (unaccent(name) gin_trgm_ops)';
        RAISE NOTICE 'Índice unaccent para region_region creado';
    END IF;
END $$;

-- Verificar creación
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE tablename = 'region_region'
    AND indexname LIKE '%trgm%'
ORDER BY indexname;


-- PASO 5: Crear Índices Trigram para project.worksite (Proyectos)
-- ============================================================================
DROP INDEX IF EXISTS idx_project_worksite_name_trgm;
CREATE INDEX idx_project_worksite_name_trgm
ON project_worksite USING gin (name gin_trgm_ops);

-- Índice con unaccent
DO $$
BEGIN
    DROP INDEX IF EXISTS idx_project_worksite_name_trgm_unaccent;

    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'unaccent') THEN
        EXECUTE 'CREATE INDEX idx_project_worksite_name_trgm_unaccent
                 ON project_worksite USING gin (unaccent(name) gin_trgm_ops)';
        RAISE NOTICE 'Índice unaccent para project_worksite creado';
    END IF;
END $$;

-- Verificar creación
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE tablename = 'project_worksite'
    AND indexname LIKE '%trgm%'
ORDER BY indexname;


-- PASO 6: Crear Índices Trigram para product.template (Propiedades)
-- ============================================================================
-- IMPORTANTE: Solo para registros donde is_property = true (índice parcial)
-- Esto reduce el tamaño del índice significativamente

-- Índice para nombre de propiedad
DROP INDEX IF EXISTS idx_product_template_name_trgm_property;
CREATE INDEX idx_product_template_name_trgm_property
ON product_template USING gin (name gin_trgm_ops)
WHERE is_property = true;

-- Índice para código de propiedad (default_code)
DROP INDEX IF EXISTS idx_product_template_code_trgm_property;
CREATE INDEX idx_product_template_code_trgm_property
ON product_template USING gin (default_code gin_trgm_ops)
WHERE is_property = true AND default_code IS NOT NULL;

-- Índice para código de barras (barcode)
DROP INDEX IF EXISTS idx_product_template_barcode_trgm_property;
CREATE INDEX idx_product_template_barcode_trgm_property
ON product_template USING gin (barcode gin_trgm_ops)
WHERE is_property = true AND barcode IS NOT NULL;

-- Verificar creación
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE tablename = 'product_template'
    AND indexname LIKE '%trgm%'
ORDER BY indexname;


-- PASO 7: Analizar Tablas para Actualizar Estadísticas
-- ============================================================================
-- Esto ayuda al query planner a usar los índices correctamente
ANALYZE res_city;
ANALYZE region_region;
ANALYZE project_worksite;
ANALYZE product_template;


-- PASO 8: Resumen de Índices Creados
-- ============================================================================
SELECT
    schemaname as schema,
    tablename as table,
    indexname as index,
    pg_size_pretty(pg_relation_size(indexrelid)) as size,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE indexname LIKE '%trgm%'
ORDER BY tablename, indexname;


-- PASO 9: Benchmark ANTES vs DESPUÉS
-- ============================================================================
-- Ejecuta estos queries ANTES y DESPUÉS de crear los índices para comparar

-- Benchmark 1: Búsqueda ciudad
EXPLAIN ANALYZE
SELECT * FROM res_city WHERE name ILIKE '%monter%';

-- Benchmark 2: Búsqueda región
EXPLAIN ANALYZE
SELECT * FROM region_region WHERE name ILIKE '%centro%';

-- Benchmark 3: Búsqueda proyecto
EXPLAIN ANALYZE
SELECT * FROM project_worksite WHERE name ILIKE '%torre%';

-- Benchmark 4: Búsqueda propiedad por nombre
EXPLAIN ANALYZE
SELECT * FROM product_template
WHERE is_property = true
    AND name ILIKE '%apartamento%';

-- Benchmark 5: Búsqueda propiedad por código
EXPLAIN ANALYZE
SELECT * FROM product_template
WHERE is_property = true
    AND default_code ILIKE '%BOH%';


-- PASO 10: Configuración Opcional de Similarity
-- ============================================================================
-- Si quieres usar búsqueda difusa (fuzzy search), ajusta el threshold

-- Ver threshold actual
SHOW pg_trgm.similarity_threshold;

-- Cambiar threshold (0.3 es default, valores más bajos = más permisivo)
-- SET pg_trgm.similarity_threshold = 0.3;

-- Ejemplo de búsqueda difusa con similarity
-- SELECT name, word_similarity('monterai', name) as sim
-- FROM res_city
-- WHERE word_similarity('monterai', name) > 0.3
-- ORDER BY sim DESC
-- LIMIT 10;


-- ============================================================================
-- NOTAS FINALES
-- ============================================================================

/*
RENDIMIENTO ESPERADO:
- Búsquedas parciales: 20-25x más rápido
- Autocompletado: 8-10x más rápido
- Memoria adicional: ~2-3 MB por tabla
- Mantenimiento: Automático

MONITOREO:
Para ver uso de índices después de un tiempo:

SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE indexname LIKE '%trgm%'
ORDER BY idx_scan DESC;

ROLLBACK (si necesitas eliminar índices):

DROP INDEX IF EXISTS idx_res_city_name_trgm;
DROP INDEX IF EXISTS idx_res_city_name_trgm_unaccent;
DROP INDEX IF EXISTS idx_region_region_name_trgm;
DROP INDEX IF EXISTS idx_region_region_name_trgm_unaccent;
DROP INDEX IF EXISTS idx_project_worksite_name_trgm;
DROP INDEX IF EXISTS idx_project_worksite_name_trgm_unaccent;
DROP INDEX IF EXISTS idx_product_template_name_trgm_property;
DROP INDEX IF EXISTS idx_product_template_code_trgm_property;
DROP INDEX IF EXISTS idx_product_template_barcode_trgm_property;

*/

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
SELECT '✅ Script completado exitosamente' as status;
