@echo off
echo ========================================
echo ACTUALIZACION MODULOS - LOGOS BOHIO
echo ========================================
echo.
echo Actualizando modulos con nuevos logos...
echo.

"C:\Program Files\Odoo 18.0.20250830\python\python.exe" "C:\Program Files\Odoo 18.0.20250830\server\odoo-bin" -c "C:\Program Files\Odoo 18.0.20250830\server\odoo.conf" -d bohio_db -u theme_bohio_real_estate,bohio_real_estate --stop-after-init

echo.
echo ========================================
echo ACTUALIZACION COMPLETADA
echo ========================================
echo.
echo Los modulos han sido actualizados.
echo Por favor:
echo 1. Refrescar el navegador con Ctrl + Shift + R
echo 2. Verificar que los logos aparezcan correctamente
echo.
pause
