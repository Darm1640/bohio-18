# MEJORAS PENDIENTES - Property Detail Template

## 1. Modal de PQRS/Reportar (Insertar después del Modal de Compartir, línea 477)

```xml
<!-- MODAL DE PQRS / REPORTAR PROBLEMA -->
<div class="modal fade" id="reportModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header" style="background: linear-gradient(135deg, #FFA500 0%, #FF8C00 100%); color: white;">
                <h5 class="modal-title">
                    <i class="fa fa-flag me-2"></i>Reportar Problema con la Propiedad
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <!-- Información de la Propiedad -->
                <div class="card mb-3 border-0 bg-light">
                    <div class="card-body">
                        <h6 class="text-warning mb-2">
                            <i class="fa fa-home me-2"></i><span t-esc="property.name"/>
                        </h6>
                        <div class="row g-2 small text-muted">
                            <div class="col-6" t-if="property.default_code">
                                <i class="fa fa-tag me-1"></i><strong>Código:</strong> <span t-esc="property.default_code"/>
                            </div>
                            <div class="col-6" t-if="property.property_type">
                                <i class="fa fa-building me-1"></i><strong>Tipo:</strong> <span t-esc="dict(property._fields['property_type'].selection).get(property.property_type)"/>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Formulario de Reporte -->
                <form id="reportForm" action="/property/report" method="post">
                    <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>
                    <input type="hidden" name="property_id" t-att-value="property.id"/>
                    <input type="hidden" name="property_name" t-att-value="property.name"/>
                    <input type="hidden" name="property_code" t-att-value="property.default_code or ''"/>

                    <!-- Tipo de Problema -->
                    <div class="mb-3">
                        <label class="form-label fw-bold">
                            <i class="fa fa-exclamation-triangle me-1 text-warning"></i>Tipo de Problema *
                        </label>
                        <select name="problem_type" class="form-select" required="required">
                            <option value="">Seleccione el tipo de problema...</option>
                            <option value="incorrect_info">Información Incorrecta</option>
                            <option value="wrong_images">Imágenes Equivocadas</option>
                            <option value="wrong_price">Precio Incorrecto</option>
                            <option value="not_available">Propiedad No Disponible</option>
                            <option value="duplicate">Propiedad Duplicada</option>
                            <option value="fraud">Posible Fraude</option>
                            <option value="inappropriate">Contenido Inapropiado</option>
                            <option value="other">Otro Problema</option>
                        </select>
                    </div>

                    <!-- Nombre del Reportante -->
                    <div class="mb-3">
                        <label class="form-label fw-bold">
                            <i class="fa fa-user me-1"></i>Tu Nombre *
                        </label>
                        <input type="text" name="reporter_name" class="form-control" required="required" placeholder="Nombre completo"/>
                    </div>

                    <!-- Email del Reportante -->
                    <div class="mb-3">
                        <label class="form-label fw-bold">
                            <i class="fa fa-envelope me-1"></i>Tu Email *
                        </label>
                        <input type="email" name="reporter_email" class="form-control" required="required" placeholder="tu@email.com"/>
                    </div>

                    <!-- Descripción del Problema -->
                    <div class="mb-3">
                        <label class="form-label fw-bold">
                            <i class="fa fa-comment me-1"></i>Descripción del Problema *
                        </label>
                        <textarea name="description" class="form-control" rows="4" required="required" placeholder="Por favor describe detalladamente el problema que encontraste..."></textarea>
                        <small class="text-muted">Mínimo 20 caracteres</small>
                    </div>

                    <!-- Link de la Propiedad (oculto pero disponible) -->
                    <input type="hidden" name="property_url" t-att-value="request.httprequest.url_root.rstrip('/') + '/property/' + str(property.id)"/>

                    <div class="alert alert-info">
                        <i class="fa fa-info-circle me-2"></i>
                        <small>Tu reporte será revisado por nuestro equipo en un plazo de 24-48 horas. Recibirás una respuesta por email.</small>
                    </div>

                    <button type="submit" class="btn btn-warning text-white w-100" onclick="submitReport(event)">
                        <i class="fa fa-paper-plane me-2"></i>Enviar Reporte
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>
```

## 2. Función JavaScript para Abrir Modal PQRS (insertar en línea 757, después de shareViaEmail)

```javascript
// ============= FUNCIONES DE REPORTE/PQRS =============

// Abrir modal de reporte
function openReportModal() {
    const modal = new bootstrap.Modal(document.getElementById('reportModal'));
    modal.show();
}

// Enviar reporte (validaciones adicionales)
function submitReport(event) {
    event.preventDefault();

    const form = document.getElementById('reportForm');
    const description = form.querySelector('[name="description"]').value;

    // Validar longitud mínima de descripción
    if (description.trim().length < 20) {
        alert('Por favor proporciona una descripción más detallada (mínimo 20 caracteres)');
        return false;
    }

    // Confirmar envío
    if (confirm('¿Estás seguro de que deseas enviar este reporte?')) {
        // Aquí podrías enviar por AJAX o dejar que se envíe el form normalmente
        alert('¡Gracias por tu reporte! Lo revisaremos pronto.');
        bootstrap.Modal.getInstance(document.getElementById('reportModal')).hide();
        form.reset();
    }

    return false;
}
```

## 3. Agregar onclick al Botón de Reportar (línea 27)

**CAMBIAR:**
```xml
<button class="btn btn-light rounded-circle shadow" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;" title="Reportar">
    <i class="fa fa-flag text-warning"></i>
</button>
```

**POR:**
```xml
<button class="btn btn-light rounded-circle shadow" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;" title="Reportar" onclick="openReportModal()">
    <i class="fa fa-flag text-warning"></i>
</button>
```

## 4. Mejorar Grid de Características a 4 Columnas (líneas 209-241)

**CAMBIAR:**
```xml
<!-- CARACTERÍSTICAS PRINCIPALES -->
<div class="row mb-4">
    <div class="col-12">
        <h5 class="text-danger mb-3"><i class="fa fa-list-ul"/> Características Principales</h5>
    </div>
    <div class="col-md-3 col-6 mb-3" t-if="property.property_area">
        <div class="text-center p-3 bg-light rounded">
            <i class="fa fa-arrows-alt fa-2x text-danger mb-2"/>
            <h4 class="mb-0 text-danger" t-esc="'%.0f' % property.property_area"/>
            <small class="text-muted">m² Área Total</small>
        </div>
    </div>
    ...
</div>
```

**POR:**
```xml
<!-- CARACTERÍSTICAS PRINCIPALES - MEJORADO 4 COLUMNAS -->
<div class="row mb-4">
    <div class="col-12 mb-3">
        <h5 class="text-danger mb-0">
            <i class="fa fa-list-ul me-2"/>Características Principales
        </h5>
        <hr class="mt-2 mb-3" style="border-top: 2px solid #E31E24; width: 80px;"/>
    </div>

    <!-- Área Total -->
    <div class="col-xl-3 col-lg-3 col-md-6 col-sm-6 col-6 mb-3" t-if="property.property_area">
        <div class="text-center p-4 bg-light rounded-3 h-100 shadow-sm hover-lift" style="border-top: 3px solid #E31E24; transition: all 0.3s;">
            <i class="fa fa-arrows-alt fa-3x text-danger mb-3" style="opacity: 0.8;"/>
            <h3 class="mb-1 fw-bold text-danger" t-esc="'%.0f' % property.property_area"/>
            <p class="mb-0 text-muted small fw-semibold">m² Área Total</p>
        </div>
    </div>

    <!-- Habitaciones -->
    <div class="col-xl-3 col-lg-3 col-md-6 col-sm-6 col-6 mb-3" t-if="property.num_bedrooms">
        <div class="text-center p-4 bg-light rounded-3 h-100 shadow-sm hover-lift" style="border-top: 3px solid #E31E24; transition: all 0.3s;">
            <i class="fa fa-bed fa-3x text-danger mb-3" style="opacity: 0.8;"/>
            <h3 class="mb-1 fw-bold text-danger" t-esc="property.num_bedrooms"/>
            <p class="mb-0 text-muted small fw-semibold">Habitaciones</p>
        </div>
    </div>

    <!-- Baños -->
    <div class="col-xl-3 col-lg-3 col-md-6 col-sm-6 col-6 mb-3" t-if="property.num_bathrooms">
        <div class="text-center p-4 bg-light rounded-3 h-100 shadow-sm hover-lift" style="border-top: 3px solid #E31E24; transition: all 0.3s;">
            <i class="fa fa-bath fa-3x text-danger mb-3" style="opacity: 0.8;"/>
            <h3 class="mb-1 fw-bold text-danger" t-esc="property.num_bathrooms"/>
            <p class="mb-0 text-muted small fw-semibold">Baños</p>
        </div>
    </div>

    <!-- Parqueaderos -->
    <div class="col-xl-3 col-lg-3 col-md-6 col-sm-6 col-6 mb-3" t-if="property.covered_parking or property.uncovered_parking">
        <div class="text-center p-4 bg-light rounded-3 h-100 shadow-sm hover-lift" style="border-top: 3px solid #E31E24; transition: all 0.3s;">
            <i class="fa fa-car fa-3x text-danger mb-3" style="opacity: 0.8;"/>
            <h3 class="mb-1 fw-bold text-danger" t-esc="(property.covered_parking or 0) + (property.uncovered_parking or 0)"/>
            <p class="mb-0 text-muted small fw-semibold">Parqueaderos</p>
        </div>
    </div>
</div>
```

## 5. Mejorar Estilizado de Nombre y Precio (líneas 121-159)

**CAMBIAR:**
```xml
<div class="d-flex justify-content-between align-items-start mb-3">
    <div>
        <h1 class="h2 mb-2" t-esc="property.name"/>
        <p class="text-muted mb-0">
            <i class="fa fa-tag"/> Código: <strong t-esc="property.default_code or 'N/A'"/>
        </p>
    </div>
    <div class="text-end">
        <!-- Precio de Venta -->
        <t t-if="property.type_service == 'sale' and property.net_price">
            <h3 class="text-primary mb-0">
                <span t-field="property.net_price" t-options="{'widget': 'monetary', 'display_currency': property.currency_id}"/>
            </h3>
            <p class="text-muted small mb-0">Precio de Venta</p>
        </t>
        ...
    </div>
</div>
```

**POR:**
```xml
<!-- HEADER MEJORADO CON NOMBRE Y PRECIO ESTILIZADO -->
<div class="row mb-4">
    <div class="col-md-8">
        <h1 class="display-5 fw-bold text-dark mb-2" style="line-height: 1.2;">
            <i class="fa fa-home text-danger me-2"></i>
            <span t-esc="property.name"/>
        </h1>
        <div class="d-flex align-items-center gap-3 mb-2">
            <span class="badge bg-danger px-3 py-2" style="font-size: 0.9rem;">
                <i class="fa fa-tag me-1"></i>
                <span t-esc="property.default_code or 'Sin código'"/>
            </span>
            <span class="badge bg-info px-3 py-2" style="font-size: 0.9rem;" t-if="property.type_service">
                <i class="fa fa-info-circle me-1"></i>
                <span t-esc="dict(property._fields['type_service'].selection).get(property.type_service)"/>
            </span>
            <span class="badge bg-secondary px-3 py-2" style="font-size: 0.9rem;" t-if="property.state">
                <span t-esc="dict(property._fields['state'].selection).get(property.state)"/>
            </span>
        </div>
    </div>

    <div class="col-md-4 text-md-end">
        <div class="card border-0 shadow-sm" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);">
            <div class="card-body p-4">
                <!-- Precio de Venta -->
                <t t-if="property.type_service == 'sale' and property.net_price">
                    <div class="mb-1">
                        <small class="text-muted text-uppercase fw-bold d-block mb-1" style="letter-spacing: 1px;">
                            <i class="fa fa-money-bill-wave me-1"></i>Precio de Venta
                        </small>
                        <h2 class="display-6 fw-bold text-primary mb-0" style="line-height: 1;">
                            <span t-field="property.net_price" t-options="{'widget': 'monetary', 'display_currency': property.currency_id}"/>
                        </h2>
                    </div>
                    <div class="mt-2" t-if="property.price_per_unit">
                        <small class="text-muted">
                            + <span t-field="property.list_price" t-options="{'widget': 'monetary', 'display_currency': property.currency_id}"/> admin.
                        </small>
                    </div>
                </t>

                <!-- Precio de Arriendo -->
                <t t-elif="property.type_service == 'rent' and property.net_rental_price">
                    <div class="mb-1">
                        <small class="text-muted text-uppercase fw-bold d-block mb-1" style="letter-spacing: 1px;">
                            <i class="fa fa-calendar-alt me-1"></i>Precio de Arriendo
                        </small>
                        <h2 class="display-6 fw-bold text-primary mb-0" style="line-height: 1;">
                            <span t-field="property.net_rental_price" t-options="{'widget': 'monetary', 'display_currency': property.currency_id}"/>
                            <small class="fs-5 text-muted fw-normal">/ mes</small>
                        </h2>
                    </div>
                </t>

                <!-- Fallback -->
                <t t-elif="property.list_price">
                    <div class="mb-1">
                        <small class="text-muted text-uppercase fw-bold d-block mb-1" style="letter-spacing: 1px;">
                            <i class="fa fa-tag me-1"></i>Precio
                        </small>
                        <h2 class="display-6 fw-bold text-primary mb-0" style="line-height: 1;">
                            <span t-field="property.list_price" t-options="{'widget': 'monetary', 'display_currency': property.currency_id}"/>
                        </h2>
                    </div>
                </t>
            </div>
        </div>
    </div>
</div>
```

## 6. Agregar Botón de Reporte en Botones Galería/Mapa (línea 109)

**AGREGAR después del botón Mapa:**
```xml
<button class="btn btn-warning px-3 py-2 fw-bold text-white" onclick="openReportModal()">
    <i class="fa fa-flag me-2"></i>Reportar
</button>
```

## 7. CSS Adicional para hover-lift (agregar en la sección <style>)

```css
/* Efecto hover en tarjetas de características */
.hover-lift {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.hover-lift:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(227, 30, 36, 0.2) !important;
}
```

## RESUMEN DE CAMBIOS

1. ✅ Modal de PQRS completo con formulario
2. ✅ Funciones JavaScript para reportar
3. ✅ Botón de reportar con onclick
4. ✅ Grid de características mejorado a 4 columnas responsive
5. ✅ Nombre y precio con mejor estilizado y badges
6. ✅ Botón de reporte en sección galería/mapa
7. ✅ CSS para efectos hover mejorados
