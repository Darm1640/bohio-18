@echo off
REM ============================================
REM SCRIPT PARA ACTUALIZAR PORTAL MYBOHIO
REM Nuevo layout con barra superior horizontal
REM ============================================

echo.
echo ========================================
echo  ACTUALIZACION PORTAL MYBOHIO
echo  Nuevo layout: Barra superior
echo ========================================
echo.

REM Solicitar confirmación
echo Este script va a:
echo  1. Actualizar el modulo bohio_real_estate
echo  2. Activar el nuevo layout de barra superior
echo.
set /p confirm="Continuar? (S/N): "
if /i not "%confirm%"=="S" (
    echo Operacion cancelada.
    pause
    exit /b
)

echo.
echo [1/3] Actualizando modulo bohio_real_estate...
echo.

REM Ejecutar desde directorio temporal para evitar problemas de permisos
cd /d "%TEMP%"

"C:\Program Files\Odoo 18.0.20250830\python\python.exe" ^
"C:\Program Files\Odoo 18.0.20250830\server\odoo-bin" ^
-c "C:\Program Files\Odoo 18.0.20250830\server\odoo.conf" ^
-d bohio_db ^
-u bohio_real_estate ^
--stop-after-init

if errorlevel 1 (
    echo.
    echo [ERROR] La actualizacion fallo.
    echo.
    echo Posibles soluciones:
    echo  1. Ejecutar este archivo como Administrador
    echo  2. Detener el servicio Odoo primero: net stop odoo18
    echo  3. Actualizar desde la interfaz de Odoo
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Modulo actualizado correctamente!
echo.

echo [3/3] Instrucciones finales:
echo.
echo  1. Iniciar/Reiniciar servicio Odoo:
echo     net start odoo18
echo.
echo  2. Limpiar cache del navegador:
echo     Chrome/Firefox: Ctrl + Shift + R
echo.
echo  3. Acceder al portal:
echo     http://localhost:8069/mybohio
echo.
echo  4. Verificar barra superior con:
echo     - Logo BOHIO blanco
echo     - Menu horizontal con iconos
echo     - Dropdown usuario derecha
echo.
echo ========================================
echo  ACTUALIZACION COMPLETADA
echo ========================================
echo.

pause
