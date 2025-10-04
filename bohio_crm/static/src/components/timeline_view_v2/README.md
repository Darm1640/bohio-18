# BOHIO TIMELINE VIEW V2

## ¿Qué hay de nuevo?

Esta es la versión mejorada de la Vista Timeline con arquitectura correcta basada en las mejores prácticas de Odoo 18.

### Mejoras Principales

#### 1. **Modelo Reactivo Correcto**
- Usa `useState` de OWL para reactividad automática
- Actualización en tiempo real de campos
- Sincronización automática con backend cada 30 segundos
- No requiere recargar manualmente

#### 2. **Chatter Nativo Integrado**
- Componente `<Chatter/>` nativo de Odoo 18
- Actividades, mensajes, seguidores automáticos
- Actualización en tiempo real de chatter
- Interfaz consistente con Odoo

#### 3. **Información Completa de Cliente**
- Dirección completa (calle, ciudad, estado, país, código postal)
- Contactos secundarios si es empresa (hasta 5)
- Diferenciación entre persona y empresa
- Función y datos de contacto de cada persona

#### 4. **Precios Dinámicos**
- Muestra `rent_value_from` si `service_interested == 'rent'`
- Muestra `sale_value_from` si `service_interested == 'sale'`
- Etiquetas correctas: "Arriendo/mes" vs "Venta"
- Se aplica a recomendaciones y comparación

#### 5. **Configuración de Usuario**
- Usuario puede elegir qué campos mostrar comprimidos
- Configuración guardada en localStorage
- Personalización por usuario

---

## Cómo Usar

### Acceso
```
Menú: CRM → Timeline V2 (Mejorada)
```

### Navegación

1. **Sidebar Izquierdo**: Lista de oportunidades
   - Búsqueda por nombre/cliente
   - Filtro por tipo de servicio
   - Click para seleccionar

2. **Contenido Principal**: Datos de la oportunidad
   - Resumen inicial con progreso
   - Etapas clickeables para cambiar
   - Métricas editables (doble clic)
   - Secciones expandibles

3. **Sidebar Derecho**: Chatter nativo
   - Actividades
   - Mensajes
   - Seguidores
   - Adjuntos

### Modo Edición

**Activar:**
- Click en botón "Editar" O
- Doble clic en cualquier campo editable

**Cuando está en modo edición:**
- Todas las secciones se expanden automáticamente
- Todos los campos editables se activan
- Badge "MODO EDICIÓN" visible
- Botones "Guardar" y "Cancelar" disponibles

**Guardar:**
- Click en "Guardar" → Guarda TODOS los cambios en batch
- Una sola llamada al backend
- Notificación de éxito
- Recarga automática de datos

**Cancelar:**
- Click en "Cancelar" → Restaura valores originales
- Descarta todos los cambios
- Vuelve al modo visualización

---

## Arquitectura Técnica

### Componente OWL
```javascript
export class BohioTimelineViewV2 extends Component {
    static template = "bohio_crm.TimelineViewV2";
    static components = { Chatter, FormViewDialog };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            record: null,      // Datos reactivos
            opportunities: [], // Lista de oportunidades
            sections: {},      // Estado de secciones
            isEditMode: false, // Modo edición
        });
    }
}
```

### Actualización Automática
```javascript
_setupAutoRefresh() {
    // Actualizar cada 30 segundos si no está editando
    this.refreshInterval = setInterval(() => {
        if (!this.state.isEditMode && this.state.resId) {
            this._loadRecordData(this.state.resId);
        }
    }, 30000);
}
```

### Guardado en Batch
```javascript
async saveAllChanges() {
    const fieldsToSave = {
        partner_name: this.state.record.partner_name,
        phone: this.state.record.phone,
        // ... todos los campos modificados
    };

    await this.orm.write("crm.lead", [this.state.resId], fieldsToSave);
    // Una sola llamada al backend!
}
```

---

## Datos del Backend

### Campos Nuevos Retornados

```python
def get_timeline_view_data(self):
    return {
        # ... campos existentes ...

        # NUEVO: Información completa del cliente
        'client_info': {
            'is_company': bool,
            'street': str,
            'street2': str,
            'city': str,
            'state_id': str,
            'country_id': str,
            'zip': str,
            'contacts': [
                {
                    'id': int,
                    'name': str,
                    'function': str,
                    'phone': str,
                    'email': str,
                }
            ]
        },
    }
```

### Precios Dinámicos

```python
def _get_property_price_info(self, prop):
    """Obtener precio según tipo de servicio"""
    if self.service_interested == 'rent':
        return {
            'price': prop.rent_value_from,
            'price_formatted': self._format_currency(...),
            'price_label': 'Arriendo/mes',
        }
    elif self.service_interested == 'sale':
        return {
            'price': prop.sale_value_from,
            'price_formatted': self._format_currency(...),
            'price_label': 'Venta',
        }
```

---

## Comparación: V1 vs V2

| Característica | V1 (Original) | V2 (Mejorada) |
|---|---|---|
| **Modelo Reactivo** | Manual | Automático |
| **Actualización** | Manual | Tiempo real |
| **Chatter** | Custom | Nativo |
| **Dirección Cliente** | No | Completa |
| **Contactos Empresa** | No | Hasta 5 |
| **Precios Dinámicos** | Fijo | Según operación |
| **Guardado** | Campo x campo | Batch |
| **Configuración** | No | Personalizable |
| **Performance** | Regular | Optimizada |

---

## Troubleshooting

### El Chatter no aparece
**Problema:** El componente Chatter no se muestra

**Solución:**
1. Verificar que el modelo tiene `mail.thread` heredado
2. Verificar que `state.resId` tiene un valor válido
3. Revisar consola del navegador por errores

### Los campos no se actualizan
**Problema:** Al cambiar un campo no se ve el cambio

**Solución:**
1. Verificar que estás en modo edición
2. Verificar que usas `t-model` en el input
3. Revisar que el campo está en `state.record`

### Error al guardar
**Problema:** Click en "Guardar" da error

**Solución:**
1. Revisar consola del navegador
2. Verificar que todos los campos existen en el modelo Python
3. Revisar permisos del usuario

---

## TODO / Próximas Mejoras

- [ ] Agregar secciones completas expandibles (Cliente, Preferencias, etc.)
- [ ] Implementar modal de configuración de campos visibles
- [ ] Agregar widget de propiedades comparadas en sidebar
- [ ] Implementar drag & drop para reordenar propiedades
- [ ] Agregar modo offline con sincronización
- [ ] Exportar a PDF/Excel desde la vista
- [ ] Agregar filtros avanzados en sidebar

---

## Para Desarrolladores

### Estructura de Archivos
```
timeline_view_v2/
├── bohio_timeline_view_v2.js    # Componente OWL
├── bohio_timeline_view_v2.xml   # Template
└── README.md                     # Esta documentación
```

### Registrado en
- `__manifest__.py`: assets backend
- `bohio_timeline_view_actions.xml`: acción cliente
- Registry: `registry.category("actions").add("bohio_timeline_view_v2", ...)`

### Extender el Componente

```javascript
import { BohioTimelineViewV2 } from "./bohio_timeline_view_v2";

class MyCustomTimeline extends BohioTimelineViewV2 {
    setup() {
        super.setup();
        // Tu lógica personalizada
    }

    async saveAllChanges() {
        // Lógica custom antes de guardar
        await super.saveAllChanges();
        // Lógica custom después de guardar
    }
}
```

---

## Referencias

- [Odoo 18 OWL Documentation](https://www.odoo.com/documentation/18.0/developer/reference/frontend/owl_components.html)
- [Chatter Widget](https://www.odoo.com/documentation/18.0/developer/reference/frontend/chatter.html)
- [useState Hook](https://www.odoo.com/documentation/18.0/developer/reference/frontend/hooks.html)
- [BOHIO CRM Module](../../../README.md)
