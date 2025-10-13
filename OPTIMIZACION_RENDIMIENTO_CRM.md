# ⚡ OPTIMIZACIÓN RENDIMIENTO CRM - Odoo 18

**Fecha:** 2025-10-11
**Problema:** Warnings de rendimiento en consola al abrir módulo CRM
**Impacto:** Interfaz lenta, scroll entrecortado, animaciones lentas

---

## 🔍 WARNINGS DETECTADOS

### **1. requestAnimationFrame Handlers Lentos**
```
[Violation] 'requestAnimationFrame' handler took 1409ms
[Violation] 'requestAnimationFrame' handler took 911ms
[Violation] 'requestAnimationFrame' handler took 542ms
```

**Causa:** JavaScript recalculando layouts/renders muy frecuentemente

---

### **2. Forced Reflows**
```
[Violation] Forced reflow while executing JavaScript took 1336ms
[Violation] Forced reflow while executing JavaScript took 591ms
[Violation] Forced reflow while executing JavaScript took 479ms
```

**Causa:** Lectura y escritura del DOM mezcladas, forzando recalcular layout

---

### **3. Non-Passive Event Listeners**
```
[Violation] Added non-passive event listener to a scroll-blocking event
```

**Causa:** Event listeners en scroll sin flag `passive: true`

---

## 💡 SOLUCIONES TÉCNICAS

### **Solución 1: Limitar Registros por Página en Vista Kanban**

**Problema:** Cargar 50+ oportunidades simultáneamente

**Archivo:** `bohio_crm/views/crm_lead_views.xml`

**Agregar:**
```xml
<record id="crm_lead_view_kanban" model="ir.ui.view">
    <field name="name">crm.lead.kanban.optimized</field>
    <field name="model">crm.lead</field>
    <field name="inherit_id" ref="crm.crm_lead_view_kanban"/>
    <field name="arch" type="xml">
        <!-- Limitar a 20 registros por carga -->
        <kanban position="attributes">
            <attribute name="limit">20</attribute>
        </kanban>
    </field>
</record>
```

**Beneficio:** Reduce carga inicial de 50+ a 20 registros

---

### **Solución 2: Lazy Loading de Imágenes**

**Problema:** Avatares de usuarios cargando todos a la vez

**Archivo:** Cualquier vista kanban con avatares

**Cambiar:**
```xml
<!-- ANTES -->
<img t-att-src="kanban_image('res.users', 'avatar_128', record.user_id.raw_value)"/>

<!-- DESPUÉS -->
<img t-att-src="kanban_image('res.users', 'avatar_128', record.user_id.raw_value)"
     loading="lazy"/>
```

**Beneficio:** Carga imágenes solo cuando son visibles

---

### **Solución 3: Desactivar Animaciones Pesadas (Opcional)**

**Problema:** Transiciones CSS complejas

**Archivo:** `bohio_crm/static/src/scss/crm_kanban.scss`

**Agregar:**
```scss
/* Reducir animaciones en kanban */
.o_kanban_view {
    .o_kanban_record {
        transition: transform 0.1s ease, box-shadow 0.1s ease;

        /* Desactivar animaciones complejas */
        &:hover {
            transition: none;
        }
    }
}
```

---

### **Solución 4: Optimizar JavaScript Personalizado**

**Archivo:** `bohio_crm/static/src/js/crm_kanban_sidebar.js`

**Problema:** Lecturas/escrituras DOM mezcladas

**ANTES (Causa reflow):**
```javascript
// ❌ MAL: Lee y escribe alternadamente
records.forEach(record => {
    const height = element.offsetHeight; // LECTURA
    element.style.height = height + 'px'; // ESCRITURA
});
```

**DESPUÉS (Batch):**
```javascript
// ✅ BIEN: Batch reads, luego batch writes
const heights = records.map(record => element.offsetHeight); // TODAS LAS LECTURAS
heights.forEach((height, index) => {
    records[index].style.height = height + 'px'; // TODAS LAS ESCRITURAS
});
```

---

### **Solución 5: Passive Event Listeners**

**Archivo:** `bohio_crm/static/src/js/*.js`

**Buscar:** Listeners en eventos `scroll`, `touchstart`, `touchmove`

**ANTES:**
```javascript
element.addEventListener('scroll', handleScroll);
```

**DESPUÉS:**
```javascript
element.addEventListener('scroll', handleScroll, { passive: true });
```

**Beneficio:** No bloquea el scroll mientras ejecuta handler

---

### **Solución 6: Virtualización de Listas Largas**

**Problema:** Renderizar 100+ registros en kanban

**Solución:** Usar `<t t-if="kanban_state != 'folded'">` para no renderizar columnas colapsadas

**Ejemplo:**
```xml
<kanban>
    <templates>
        <t t-name="card">
            <!-- Solo renderizar si columna está expandida -->
            <t t-if="!group_by_no_leaf">
                <div class="oe_kanban_content">
                    <!-- Contenido pesado aquí -->
                </div>
            </t>
        </t>
    </templates>
</kanban>
```

---

## 🚀 SOLUCIONES RÁPIDAS (SIN CÓDIGO)

### **1. Reducir Registros Mostrados**

**Configuración → CRM → Vistas:**
- Cambiar "Registros por página" de 80 a 20
- Aplicar filtros por defecto (ej: "Mis oportunidades")

---

### **2. Usar Vista Lista en lugar de Kanban**

**Si el rendimiento es crítico:**
- Vista Lista es ~3x más rápida que Kanban
- Menos JavaScript ejecutándose
- Menos elementos DOM

**Cambiar vista por defecto:**
```xml
<record id="crm_lead_action_mine" model="ir.actions.act_window">
    <field name="view_mode">tree,form,calendar,pivot,graph,activity</field>
    <!-- Nota: "tree" primero en lugar de "kanban" -->
</record>
```

---

### **3. Activar Paginación en Kanban**

**Odoo 18 permite paginación en kanban:**

```xml
<kanban limit="20" can_open="1" class="o_kanban_small_column">
    <!-- Esto fuerza cargar solo 20, con botón "Load more" -->
</kanban>
```

---

### **4. Limpiar Assets Compilados**

**Cache viejo puede causar lentitud:**

```
Ajustes → Técnico → Assets → Borrar todos
```

Luego reiniciar Odoo.

---

## 📊 MÉTRICAS DE MEJORA ESPERADA

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| **Carga inicial CRM** | ~3-5s | ~1-2s | 60% |
| **requestAnimationFrame** | 1409ms | <100ms | 93% |
| **Forced reflows** | 1336ms | <50ms | 96% |
| **FPS durante scroll** | 30-40 | 55-60 | 50% |

---

## 🔧 IMPLEMENTACIÓN RECOMENDADA

### **Prioridad ALTA (Fácil + Gran Impacto):**

1. ✅ Limitar kanban a 20 registros (`limit="20"`)
2. ✅ Agregar `loading="lazy"` a imágenes
3. ✅ Limpiar assets compilados

### **Prioridad MEDIA (Requiere Código):**

4. ⚠️ Optimizar JavaScript (batch DOM reads/writes)
5. ⚠️ Agregar `passive: true` a listeners

### **Prioridad BAJA (Opcional):**

6. 💡 Cambiar vista por defecto a Lista
7. 💡 Desactivar animaciones complejas

---

## 🧪 CÓMO MEDIR MEJORAS

### **Chrome DevTools Performance:**

1. **Abrir DevTools** → Pestaña "Performance"
2. **Grabar** mientras abres CRM
3. **Parar grabación** cuando termine de cargar
4. **Analizar:**
   - Scripting (JavaScript) debería ser <1s
   - Rendering debería ser <500ms
   - Painting debería ser <300ms

### **Lighthouse Audit:**

```
DevTools → Lighthouse → Performance → Generate report
```

**Puntaje objetivo:**
- Performance: >90 (actualmente probablemente <60)
- FCP (First Contentful Paint): <1.5s
- LCP (Largest Contentful Paint): <2.5s

---

## 📝 ARCHIVOS A MODIFICAR (OPCIONAL)

Si decides implementar optimizaciones:

1. `bohio_crm/views/crm_lead_views.xml` → Agregar `limit="20"`
2. `bohio_crm/static/src/js/crm_kanban_sidebar.js` → Batch DOM ops
3. `bohio_crm/static/src/js/crm_quick_create_smart.js` → Passive listeners
4. `bohio_crm/static/src/scss/crm_kanban.scss` → Reducir animaciones

---

## ⚠️ IMPORTANTE

**Estos warnings NO rompen funcionalidad**, solo afectan rendimiento.

**Prioriza:**
1. **Primero:** Actualizar logos (tema principal)
2. **Segundo:** Optimizaciones de rendimiento (si la lentitud es notoria)

Si la interfaz funciona aceptablemente, puedes ignorar estos warnings por ahora.

---

## 🆘 SI LA LENTITUD ES INSOPORTABLE

**Solución temporal inmediata:**

1. **Reducir datos cargados:**
   ```
   CRM → Filtros → "Mis oportunidades" (solo las tuyas)
   ```

2. **Usar Vista Lista:**
   ```
   CRM → Cambiar a vista Lista (ícono de lista)
   ```

3. **Cerrar tabs innecesarias del navegador**

4. **Limpiar caché navegador:**
   ```
   Ctrl + Shift + Delete
   ```

---

**FIN DEL DOCUMENTO**

**Próximo paso recomendado:**
1. Verificar que logos estén actualizados
2. Si lentitud es problemática, implementar Solución 1 (limit="20")
