# 🔄 INSTRUCCIONES: Actualizar Logos en Odoo

**Fecha:** 2025-10-11
**Problema:** Los logos nuevos están en los archivos pero NO se ven en el navegador
**Causa:** Los módulos necesitan ser actualizados en Odoo

---

## ✅ ARCHIVOS YA MODIFICADOS (LISTOS)

### **Logos Copiados:**
- ✅ `theme_bohio_real_estate/static/src/img/logo-negro.png`
- ✅ `theme_bohio_real_estate/static/src/img/logo-blanco.png`
- ✅ `bohio_real_estate/static/img/logo-blanco.png`

### **Archivos XML Actualizados:**
1. ✅ `theme_bohio_real_estate/views/headers/header_template.xml` → Logo negro
2. ✅ `theme_bohio_real_estate/views/footers/footer_template.xml` → Logo blanco
3. ✅ `theme_bohio_real_estate/views/layout/loader_template.xml` → Logo negro
4. ✅ `bohio_real_estate/views/portal/common/portal_layout.xml` → Logo blanco

---

## 🔄 PASO 1: Actualizar Módulos desde Odoo Web

### **Opción A: Actualizar desde Aplicaciones (RECOMENDADO)**

1. **Abrir Odoo en el navegador:**
   ```
   http://localhost:8069
   ```

2. **Iniciar sesión** como administrador
   - Usuario: `admin`
   - Contraseña: `admin` (o la que uses)

3. **Ir a Aplicaciones:**
   - Click en el menú principal (9 cuadrados arriba a la izquierda)
   - Click en "Aplicaciones"

4. **Actualizar módulo theme_bohio_real_estate:**
   - En el buscador de aplicaciones, escribir: `theme_bohio_real_estate`
   - Hacer click en el módulo (debería mostrar un botón verde "Instalado")
   - Click en el botón de 3 puntos verticales `⋮` en la esquina superior derecha del módulo
   - Click en "Actualizar"
   - Esperar a que termine (puede tomar 10-30 segundos)

5. **Actualizar módulo bohio_real_estate:**
   - Repetir el mismo proceso para `bohio_real_estate`
   - En el buscador, escribir: `bohio_real_estate`
   - Click en el botón de 3 puntos `⋮`
   - Click en "Actualizar"
   - Esperar a que termine

6. **Verificar actualización:**
   - Debería ver un mensaje verde "Actualización exitosa" o similar

---

### **Opción B: Modo Desarrollador + Actualizar Lista**

Si la Opción A no funciona:

1. **Activar Modo Desarrollador:**
   - Ajustes (Settings) → Activar Modo Desarrollador
   - O agregar `?debug=1` a la URL: `http://localhost:8069/web?debug=1`

2. **Actualizar Lista de Aplicaciones:**
   - Aplicaciones → Click en 3 puntos arriba a la derecha
   - Click en "Actualizar Lista de Aplicaciones"
   - Confirmar

3. **Actualizar módulos:**
   - Buscar `theme_bohio_real_estate` → Actualizar
   - Buscar `bohio_real_estate` → Actualizar

---

## 🔄 PASO 2: Limpiar Caché del Navegador

**IMPORTANTE:** Después de actualizar los módulos, DEBES limpiar el caché del navegador:

### **Chrome / Edge:**
```
Ctrl + Shift + R
```
o
```
F12 → Application → Clear storage → Clear site data
```

### **Firefox:**
```
Ctrl + Shift + Delete → Imágenes y archivos en caché → Limpiar ahora
```

### **Si aún no funciona:**
Limpiar caché completo:
1. Abrir ventana de incógnito/privada
2. Ir a `http://localhost:8069`
3. Verificar si los logos aparecen

---

## ✅ PASO 3: Verificar que los Logos Aparezcan

### **Website Público (theme_bohio_real_estate):**

1. **Header:**
   - Ir a homepage: `http://localhost:8069`
   - Verificar logo **NEGRO** en header (fondo blanco)
   - Ruta: `/theme_bohio_real_estate/static/src/img/logo-negro.png`

2. **Footer:**
   - Scroll hasta abajo de cualquier página
   - Verificar logo **BLANCO** en footer (fondo negro)
   - Ruta: `/theme_bohio_real_estate/static/src/img/logo-blanco.png`

3. **Loader (Pantalla de carga):**
   - Navegar entre páginas rápidamente
   - Verificar logo **NEGRO** en pantalla de carga
   - Ruta: `/theme_bohio_real_estate/static/src/img/logo-negro.png`

### **Portal MyBOHIO (bohio_real_estate):**

1. **Navbar del Portal:**
   - Ir a: `http://localhost:8069/mybohio`
   - Iniciar sesión con un usuario del portal
   - Verificar logo **BLANCO** en navbar roja
   - Ruta: `/bohio_real_estate/static/img/logo-blanco.png`

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### **Problema 1: "Los logos siguen siendo los antiguos"**

**Causa:** Caché del navegador

**Solución:**
```
1. Ctrl + Shift + R (forzar recarga)
2. Si no funciona: Abrir DevTools (F12)
3. Network tab → Disable cache (marcar checkbox)
4. Recargar página
```

---

### **Problema 2: "Error 404 - No se encuentra el logo"**

**Causa:** Los archivos no se copiaron correctamente

**Verificar:**
```bash
# Verificar que existen los archivos
dir "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\static\src\img\logo-negro.png"
dir "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\static\src\img\logo-blanco.png"
dir "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\bohio_real_estate\static\img\logo-blanco.png"
```

**Si no existen**, copiar nuevamente:
```bash
cp "C:\Users\darm1\Downloads\PAGINA WEB BOHIO-20250925T171508Z-1-003\PAGINA WEB BOHIO\Logo Negro transpartente.png" "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\static\src\img\logo-negro.png"

cp "C:\Users\darm1\Downloads\PAGINA WEB BOHIO-20250925T171508Z-1-003\PAGINA WEB BOHIO\Logo Blanco.png" "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\static\src\img\logo-blanco.png"

cp "C:\Users\darm1\Downloads\PAGINA WEB BOHIO-20250925T171508Z-1-003\PAGINA WEB BOHIO\Logo Blanco.png" "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\bohio_real_estate\static\img\logo-blanco.png"
```

Luego actualizar módulos nuevamente.

---

### **Problema 3: "Odoo no detecta los módulos para actualizar"**

**Causa:** Odoo no reconoce cambios en archivos estáticos

**Solución:**
1. **Reiniciar el servidor Odoo:**
   ```
   Servicios de Windows → Buscar "Odoo" → Reiniciar servicio
   ```

   O desde línea de comandos (como Administrador):
   ```batch
   net stop odoo-server-18.0
   net start odoo-server-18.0
   ```

2. **Verificar que el servidor reinició:**
   - Ir a `http://localhost:8069`
   - Debería cargar normalmente

3. **Actualizar módulos** (Opción A o B de arriba)

---

### **Problema 4: "El portal sigue mostrando el logo con filtro CSS"**

**Causa:** El módulo `bohio_real_estate` no se actualizó

**Verificar HTML renderizado:**
1. F12 → Inspeccionar elemento del logo
2. Debería ver:
   ```html
   <!-- ✅ CORRECTO -->
   <img src="/bohio_real_estate/static/img/logo-blanco.png"
        alt="BOHIO"
        style="height: 40px;">
   ```

   NO debería ver:
   ```html
   <!-- ❌ INCORRECTO (versión vieja) -->
   <img src="/bohio_real_estate/static/img/logo-horizontal-bohio.png"
        alt="BOHIO"
        style="height: 40px; filter: brightness(0) invert(1);">
   ```

**Si sigue viendo la versión incorrecta:**
1. Actualizar módulo `bohio_real_estate` nuevamente
2. Limpiar caché navegador
3. Reiniciar servidor Odoo si es necesario

---

## 📋 CHECKLIST FINAL

Usa esta lista para verificar que todo está correcto:

### **Website Público:**
- [ ] Header muestra logo negro sobre fondo blanco
- [ ] Logo negro se ve nítido (sin filtro CSS)
- [ ] Footer muestra logo blanco sobre fondo negro
- [ ] Logo blanco se ve nítido (sin filtro CSS)
- [ ] Loader muestra logo negro

### **Portal MyBOHIO:**
- [ ] Navbar muestra logo blanco sobre gradient rojo
- [ ] Logo blanco se ve nítido (sin filtro CSS)
- [ ] No hay `filter: brightness(0) invert(1)` en el HTML

### **Navegador:**
- [ ] No hay errores 404 en consola (F12 → Console)
- [ ] Los logos cargan correctamente (F12 → Network → buscar "logo")

---

## 🆘 ÚLTIMO RECURSO: Actualización Manual

Si NADA de lo anterior funciona:

1. **Borrar assets compilados:**
   ```
   Ajustes → Técnico → Assets → Borrar todos los assets
   ```

2. **Reiniciar servidor Odoo**

3. **Actualizar módulos en modo debug:**
   ```
   http://localhost:8069/web?debug=assets
   ```

4. **Forzar recompilación de assets:**
   - Modo desarrollador ON
   - Aplicaciones → theme_bohio_real_estate → Actualizar
   - Esperar mensaje de éxito

---

## ✅ RESULTADO ESPERADO

Después de seguir estos pasos:

| Ubicación | Logo | Fondo | Sin Filtro CSS |
|-----------|------|-------|----------------|
| Header Website | Negro | Blanco | ✅ |
| Footer Website | Blanco | Negro | ✅ |
| Loader | Negro | Blanco | ✅ |
| Portal MyBOHIO | Blanco | Rojo Gradient | ✅ |

---

**FIN DE LAS INSTRUCCIONES**

Si después de seguir TODOS estos pasos los logos no aparecen, por favor reporta:
1. Captura de pantalla del HTML (inspeccionar elemento)
2. Errores en consola del navegador (F12)
3. Versión exacta de Odoo que estás usando
