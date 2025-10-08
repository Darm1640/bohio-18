# Mejoras de Accesibilidad - Theme Bohio Real Estate

## Fecha: 2025-10-08

## Problemas Corregidos

### 1. Error aria-hidden en Modal
**Problema Original:**
```
Blocked aria-hidden on an element because its descendant retained focus.
Element with focus: <button.btn-close>
Ancestor with aria-hidden: <div.modal fade#codeSearchModal>
```

**Causa:**
El modal tenía `aria-hidden="true"` que entraba en conflicto cuando el botón de cerrar obtenía el foco.

**Solución Aplicada:**
- Removido `aria-hidden="true"` del elemento modal en `properties_shop_template.xml`
- Bootstrap maneja automáticamente el estado aria-hidden según el estado del modal
- Mejorada la etiqueta aria-label del botón de cerrar de "Close" a "Cerrar"

**Archivos Modificados:**
- `views/properties_shop_template.xml` (línea 285)

### 2. Uso Innecesario de aria-hidden con display:none
**Problema:**
Uso redundante de `aria-hidden` en elementos que ya usan `display: none`

**Solución:**
- Removido `mapaWrap.setAttribute('aria-hidden', !isMapa)` de `properties_list_map.js`
- Documentado que `display: none` ya oculta elementos de tecnologías asistivas

**Archivos Modificados:**
- `static/src/js/properties_list_map.js` (línea 356)

### 3. Etiquetas aria-label Genéricas
**Problema:**
Botones de cerrar con etiquetas genéricas "Remove" que no especifican qué se está eliminando

**Solución:**
- Mejorada etiqueta a `aria-label="Eliminar ${loc.display}"` para dar contexto específico
- Usuarios de lectores de pantalla ahora saben exactamente qué ubicación están eliminando

**Archivos Modificados:**
- `static/src/js/search/search_bar.js` (línea 153)

## Mejores Prácticas Implementadas

### Modales
- No usar `aria-hidden="true"` en modales Bootstrap
- Dejar que Bootstrap maneje automáticamente los estados ARIA
- Usar `aria-labelledby` para conectar el título del modal
- Incluir `aria-label` descriptivo en botones de cerrar

### Elementos Ocultos/Mostrados
- No usar `aria-hidden` cuando ya se usa `display: none`
- `display: none` automáticamente oculta de tecnologías asistivas
- Solo usar `aria-hidden` cuando el elemento es visualmente visible pero debe ocultarse de lectores de pantalla

### Botones de Acción
- Siempre incluir `aria-label` descriptivo en botones que solo tienen iconos
- Las etiquetas deben ser específicas y contextuales
- Usar idioma español consistentemente

## Verificación de Accesibilidad

### Herramientas Recomendadas
1. **Lighthouse** (Chrome DevTools) - Auditoría de accesibilidad
2. **axe DevTools** - Análisis detallado WCAG
3. **WAVE** - Evaluación visual de accesibilidad
4. **NVDA/JAWS** - Pruebas con lectores de pantalla

### Checklist de Accesibilidad
- [x] Modales sin conflictos aria-hidden
- [x] Todos los botones tienen etiquetas descriptivas
- [x] No hay uso redundante de aria-hidden
- [x] Etiquetas en español consistente
- [x] Controles interactivos accesibles por teclado
- [x] Foco visible en elementos interactivos

## Pruebas Realizadas

### Navegación por Teclado
- Tab: Navegación entre campos funcional
- Enter: Activación de botones correcta
- Escape: Cierre de modales operativo

### Lectores de Pantalla
- Anuncios de modales claros
- Descripción de botones específica
- Navegación de formularios lógica

## Referencias
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Bootstrap Accessibility](https://getbootstrap.com/docs/5.3/getting-started/accessibility/)
