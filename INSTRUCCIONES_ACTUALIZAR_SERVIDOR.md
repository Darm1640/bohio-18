# INSTRUCCIONES: Actualizar Servidor con los Cambios

## Fecha: 2025-10-12
## Estado: Cambios listos en repositorio, falta actualizar servidor

---

## ✅ ESTADO ACTUAL

1. ✅ Cambios commiteados localmente
2. ✅ Push exitoso a repositorio remoto (origin/main)
3. ⚠️ **FALTA**: Hacer pull en el servidor y reiniciar Odoo

---

## 📝 ARCHIVOS MODIFICADOS

1. `theme_bohio_real_estate/static/src/js/property_detail_gallery.js`
   - Líneas 125-131: Fix de sintaxis en miniaturas del zoom
   - Extraídas variables para evitar comillas simples escapadas

2. `theme_bohio_real_estate/views/property_detail_template.xml`
   - Línea 424: Fix QWeb en modal de Share (`t-att` → `t-attf`)
   - Línea 500: Fix QWeb en modal de Reporte (`t-att` → `t-attf`)

---

## 🚀 PASOS PARA ACTUALIZAR EL SERVIDOR

### OPCIÓN 1: SSH al Servidor (RECOMENDADO)

```bash
# 1. Conectar por SSH
ssh usuario@104.131.70.107

# 2. Ir al directorio del addon
cd /ruta/al/addon/bohio-18

# 3. Hacer pull de los cambios
git pull origin main

# 4. Reiniciar Odoo
sudo systemctl restart odoo
# O si usas supervisorctl:
sudo supervisorctl restart odoo

# 5. Esperar 10-15 segundos

# 6. Verificar logs
tail -f /var/log/odoo/odoo.log
```

### OPCIÓN 2: Panel de Control / cPanel / WHM

Si tienes acceso a un panel de control:

1. Ir a "Git Version Control" o similar
2. Buscar el repositorio `bohio-18`
3. Click en "Pull" o "Update"
4. Ir a "Services"
5. Reiniciar el servicio "Odoo"

### OPCIÓN 3: Usar Script de Actualización Remota

Si el servidor tiene un endpoint de actualización automática:

```bash
# Ejecutar localmente:
python actualizar_servidor_remoto.py
```

---

## 🧹 DESPUÉS DE HACER PULL - LIMPIAR ASSETS

Ejecutar este script localmente para limpiar los assets minificados del servidor:

```bash
python forzar_limpieza_assets.py
```

O manualmente en el servidor:

```bash
# En el servidor, conectado por SSH:
cd /ruta/al/addon

# Eliminar assets compilados
rm -rf /var/lib/odoo/filestore/bohio/assets/*
rm -rf /var/lib/odoo/filestore/bohio/.local/share/Odoo/filestore/bohio/assets/*

# Reiniciar Odoo
sudo systemctl restart odoo
```

---

## 🔍 VERIFICACIÓN POST-ACTUALIZACIÓN

Después de actualizar el servidor, verificar en el navegador:

### 1. Abrir la consola (F12)

Debería mostrar:
```
✅ Property Detail Gallery JS completamente cargado
✅ Imágenes cargadas: [número]
```

**NO debería mostrar**:
```
❌ Uncaught SyntaxError: Unexpected token '&'
```

### 2. Probar el zoom

```javascript
// En la consola:
console.log('zoomImages:', window.zoomImages);
// Debe mostrar un array con URLs de imágenes, NO un array vacío []
```

### 3. Hacer click en una imagen

El zoom debe abrir y mostrar la imagen correctamente, NO una pantalla negra con icono de error.

### 4. Verificar el modal de reporte

```javascript
// En la consola:
console.log('Modal reporte:', document.getElementById('reportModal'));
// Debe mostrar el elemento <div id="reportModal">, NO null
```

---

## 🎯 RESUMEN DE PROBLEMAS Y SOLUCIONES

| # | Problema | Causa | Solución | Estado |
|---|----------|-------|----------|--------|
| 1 | `Unexpected token '&'` | Comillas simples escapadas a `&#39;` en template literals | Extraer valores a variables | ✅ Corregido en repo |
| 2 | Modal de reporte no aparece | Error QWeb `str()` en `t-att-value` | Cambiar a `t-attf-value` | ✅ Corregido en repo |
| 3 | Zoom muestra pantalla negra | Error de sintaxis rompe carga de imágenes | Fix de sintaxis | ✅ Corregido en repo |
| 4 | Assets minificados antiguos | Caché de Odoo | Limpiar assets | ⚠️ Pendiente en servidor |

---

## 📞 SI TIENES PROBLEMAS

### Problema: No tengo acceso SSH al servidor

**Solución**:
1. Contactar al administrador del servidor
2. Enviar los archivos por FTP/SFTP
3. Solicitar que ejecuten:
   ```bash
   cd /ruta/al/addon/bohio-18
   git pull
   sudo systemctl restart odoo
   ```

### Problema: El error persiste después de actualizar

**Posibles causas**:
1. Los cambios no se aplicaron → Verificar con `git log` en el servidor
2. Assets no se regeneraron → Limpiar manualmente (ver arriba)
3. Caché del navegador → Hacer Ctrl + Shift + Delete, borrar caché

**Solución**:
```bash
# En el servidor:
cd /ruta/al/addon/bohio-18
git log --oneline -3

# Debe mostrar:
# 878d1d3e Update property_detail_gallery.js
# 0deee3ef Update property_detail_template.xml
```

### Problema: Odoo no reinicia

**Verificar logs**:
```bash
# En el servidor:
tail -100 /var/log/odoo/odoo.log
```

Buscar errores relacionados con:
- `theme_bohio_real_estate`
- `property_detail_gallery`
- `SyntaxError`
- `ImportError`

---

## ✅ CHECKLIST FINAL

- [ ] Conectar al servidor por SSH (u otro método)
- [ ] Hacer `git pull origin main` en el directorio del addon
- [ ] Verificar que los cambios se aplicaron (`git log`)
- [ ] Reiniciar servicio de Odoo
- [ ] Esperar 10-15 segundos
- [ ] Ejecutar `forzar_limpieza_assets.py` localmente
- [ ] Abrir navegador en https://104.131.70.107/property/15360
- [ ] Presionar Ctrl + Shift + R (hard refresh)
- [ ] Verificar en consola que NO hay error de sintaxis
- [ ] Probar abrir zoom de una imagen
- [ ] Verificar que se ve la imagen correctamente
- [ ] Probar modal de reporte
- [ ] Confirmar que funciona correctamente

---

**¿Tienes acceso SSH al servidor en 104.131.70.107?**

Si no, necesitamos:
1. Usuario y contraseña SSH/SFTP
2. Ruta completa del addon en el servidor
3. O contactar al administrador del servidor

Una vez tengamos eso, podemos proceder con la actualización.
