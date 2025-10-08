# BOHIO Real Estate - Biblioteca de Componentes

## 📦 Componentes Reutilizables

Esta guía contiene componentes pre-diseñados que puedes usar en tu sitio web de BOHIO.

---

## 🏠 Tarjeta de Propiedad

### Variante 1: Tarjeta Estándar

```xml
<div class="property-card card h-100 border-0 shadow-sm rounded-3">
    <!-- Imagen -->
    <div class="position-relative">
        <img src="property-image.jpg" 
             class="card-img-top" 
             style="height: 250px; object-fit: cover;"
             alt="Nombre de propiedad"/>
        
        <!-- Precio -->
        <div class="position-absolute top-0 end-0 m-3">
            <span class="badge bg-danger px-3 py-2 fs-6">
                $3.000.000
            </span>
        </div>
        
        <!-- Estado -->
        <div class="position-absolute top-0 start-0 m-3">
            <span class="badge bg-primary">Arriendo</span>
        </div>
        
        <!-- Botón de favorito -->
        <button class="btn btn-light btn-sm rounded-circle position-absolute bottom-0 end-0 m-3"
                data-favorite data-property-id="123">
            <i class="fa fa-heart-o"></i>
        </button>
    </div>

    <!-- Contenido -->
    <div class="card-body">
        <h5 class="card-title mb-2">
            <a href="/property/123" class="text-decoration-none text-dark">
                Casa Doble, Monta verde
            </a>
        </h5>
        
        <p class="text-muted small mb-3">
            <i class="fa fa-map-marker-alt me-1"></i>
            Barrio Norte, Bogotá
        </p>

        <!-- Características -->
        <div class="property-features d-flex justify-content-between mb-3">
            <span class="feature-item text-muted small">
                <img src="/img/habitacion-8.png" style="width: 20px; height: 20px;"/>
                <strong>3</strong>
            </span>
            <span class="feature-item text-muted small">
                <img src="/img/baño_1-8.png" style="width: 20px; height: 20px;"/>
                <strong>2</strong>
            </span>
            <span class="feature-item text-muted small">
                <img src="/img/areas_1-8.png" style="width: 20px; height: 20px;"/>
                <strong>120</strong> m²
            </span>
        </div>

        <a href="/property/123" class="btn btn-outline-danger w-100">
            Ver Detalles
        </a>
    </div>
</div>
```

### Variante 2: Tarjeta Compacta

```xml
<div class="property-card-compact card border-0 shadow-sm">
    <div class="row g-0">
        <div class="col-4">
            <img src="property-image.jpg" 
                 class="img-fluid h-100" 
                 style="object-fit: cover;"
                 alt="Propiedad"/>
        </div>
        <div class="col-8">
            <div class="card-body p-3">
                <h6 class="mb-1">Casa Doble, Monta verde</h6>
                <p class="text-muted small mb-2">
                    <i class="fa fa-map-marker-alt"></i> Bogotá
                </p>
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-danger fw-bold">$3.000.000</span>
                    <a href="/property/123" class="btn btn-sm btn-outline-danger">
                        Ver
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## 🔍 Formularios de Búsqueda

### Búsqueda Rápida (Hero)

```xml
<div class="quick-search bg-white p-4 rounded-3 shadow-lg">
    <form action="/properties" method="get">
        <div class="row g-3">
            <div class="col-md-3">
                <label class="form-label small mb-1">Inmueble</label>
                <select name="property_type" class="form-select">
                    <option value="">Tipo</option>
                    <option value="apartment">Apartamento</option>
                    <option value="house">Casa</option>
                    <option value="office">Oficina</option>
                </select>
            </div>
            
            <div class="col-md-3">
                <label class="form-label small mb-1">Ciudad</label>
                <input type="text" name="city" class="form-control" 
                       placeholder="¿Dónde buscas?"/>
            </div>
            
            <div class="col-md-2">
                <label class="form-label small mb-1">Habitaciones</label>
                <input type="number" name="bedrooms" class="form-control" 
                       placeholder="N°" min="0"/>
            </div>
            
            <div class="col-md-2">
                <label class="form-label small mb-1">Baños</label>
                <input type="number" name="bathrooms" class="form-control" 
                       placeholder="N°" min="0"/>
            </div>
            
            <div class="col-md-2">
                <label class="form-label small mb-1">&#160;</label>
                <button type="submit" class="btn btn-danger w-100">
                    Buscar
                </button>
            </div>
        </div>
    </form>
</div>
```

### Búsqueda Avanzada

```xml
<div class="advanced-search bg-white p-4 rounded-3 shadow">
    <form action="/properties" method="get">
        <div class="row g-3">
            <!-- Filtros básicos -->
            <div class="col-md-4">
                <label class="form-label">Tipo de Servicio</label>
                <select name="type_service" class="form-select">
                    <option value="">Todos</option>
                    <option value="sale">Venta</option>
                    <option value="rent">Arriendo</option>
                </select>
            </div>
            
            <!-- Filtros de ubicación -->
            <div class="col-md-4">
                <label class="form-label">Departamento</label>
                <select name="state_id" class="form-select">
                    <option value="">Todos</option>
                </select>
            </div>
            
            <div class="col-md-4">
                <label class="form-label">Ciudad</label>
                <select name="city_id" class="form-select">
                    <option value="">Todas</option>
                </select>
            </div>
            
            <!-- Filtros de precio -->
            <div class="col-md-6">
                <label class="form-label">Precio Mínimo</label>
                <input type="number" name="price_min" class="form-control" 
                       placeholder="$0" step="100000"/>
            </div>
            
            <div class="col-md-6">
                <label class="form-label">Precio Máximo</label>
                <input type="number" name="price_max" class="form-control" 
                       placeholder="Sin límite" step="100000"/>
            </div>
            
            <!-- Botones de acción -->
            <div class="col-12">
                <div class="d-flex gap-2 justify-content-end">
                    <button type="reset" class="btn btn-outline-secondary">
                        Limpiar
                    </button>
                    <button type="submit" class="btn btn-danger">
                        <i class="fa fa-search me-1"></i> Buscar
                    </button>
                </div>
            </div>
        </div>
    </form>
</div>
```

---

## 🎨 Secciones de Contenido

### Sección de Servicios

```xml
<section class="bohio-services py-5">
    <div class="container">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <span class="badge bg-danger px-3 py-2">Nuestros servicios</span>
            </div>
            <div class="d-flex gap-2">
                <button class="btn btn-danger btn-sm rounded-circle">
                    <i class="fa fa-chevron-left"></i>
                </button>
                <button class="btn btn-danger btn-sm rounded-circle">
                    <i class="fa fa-chevron-right"></i>
                </button>
            </div>
        </div>
        
        <div class="row g-4">
            <div class="col-md-2 col-6">
                <div class="service-card text-center p-3 h-100 bg-white rounded-3 shadow-sm">
                    <div class="service-icon mb-2">
                        <img src="/img/service-icon.gif" 
                             style="width: 60px; height: 60px;"/>
                    </div>
                    <h6 class="mb-0">Nombre del Servicio</h6>
                </div>
            </div>
            <!-- Repetir para más servicios -->
        </div>
    </div>
</section>
```

### Sección de Testimonios

```xml
<section class="bohio-testimonials py-5">
    <div class="container">
        <div class="mb-4">
            <span class="badge bg-danger px-3 py-2">Testimonios</span>
        </div>
        <h2 class="mb-5">
            Ellos ya vivieron <span class="text-danger fw-bold">la experiencia bohío</span>
        </h2>
        
        <div class="row g-4">
            <div class="col-md-3">
                <div class="testimonial-card p-4 bg-white rounded-3 shadow-sm h-100">
                    <div class="d-flex align-items-center mb-3">
                        <img src="/web/image/avatar.jpg" 
                             class="rounded-circle me-3" 
                             style="width: 50px; height: 50px;"
                             alt="Cliente"/>
                        <div>
                            <h6 class="mb-0">Nombre Cliente</h6>
                            <div class="stars text-warning small">
                                <i class="fa fa-star"></i>
                                <i class="fa fa-star"></i>
                                <i class="fa fa-star"></i>
                                <i class="fa fa-star"></i>
                                <i class="fa fa-star"></i>
                            </div>
                        </div>
                    </div>
                    <p class="small text-muted mb-0">
                        "Excelente servicio y atención. Muy recomendado."
                    </p>
                </div>
            </div>
            <!-- Repetir para más testimonios -->
        </div>
    </div>
</section>
```

---

## 🎭 Modales

### Modal de Búsqueda por Código

```xml
<div class="modal fade" id="codeSearchModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="fa fa-qrcode me-2"></i> Buscar por Código
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label">Código de Propiedad</label>
                    <input type="text" id="property_code_input" 
                           class="form-control" 
                           placeholder="Ej: BOH-001"/>
                </div>
                <div id="code_search_result" class="alert" style="display:none;"></div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    Cancelar
                </button>
                <button type="button" class="btn btn-danger" id="search_by_code_btn">
                    <i class="fa fa-search"></i> Buscar
                </button>
            </div>
        </div>
    </div>
</div>
```

### Modal de Comparación

```xml
<div class="modal fade" id="compareModal" tabindex="-1">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Comparar Propiedades</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Característica</th>
                                <th>Propiedad 1</th>
                                <th>Propiedad 2</th>
                                <th>Propiedad 3</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Precio</td>
                                <td>$3.000.000</td>
                                <td>$2.500.000</td>
                                <td>$3.500.000</td>
                            </tr>
                            <tr>
                                <td>Habitaciones</td>
                                <td>3</td>
                                <td>2</td>
                                <td>4</td>
                            </tr>
                            <!-- Más características -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## 🔔 Alertas y Notificaciones

### Alerta de Éxito

```xml
<div class="alert alert-success alert-dismissible fade show" role="alert">
    <i class="fa fa-check-circle me-2"></i>
    <strong>¡Éxito!</strong> Tu búsqueda se ha guardado correctamente.
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>
```

### Alerta de Error

```xml
<div class="alert alert-danger alert-dismissible fade show" role="alert">
    <i class="fa fa-exclamation-circle me-2"></i>
    <strong>Error:</strong> No se pudo completar la operación.
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>
```

### Toast Notification

```xml
<div class="position-fixed bottom-0 end-0 p-3" style="z-index: 11">
    <div class="toast show" role="alert">
        <div class="toast-header">
            <i class="fa fa-bell text-danger me-2"></i>
            <strong class="me-auto">BOHIO</strong>
            <small>Ahora</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            Nueva propiedad disponible en tu búsqueda guardada.
        </div>
    </div>
</div>
```

---

## 📊 Estadísticas y Contadores

### Contador Animado

```xml
<div class="stat-counter text-center">
    <div class="counter-number display-4 fw-bold text-danger" 
         data-count="1500">0</div>
    <p class="text-muted">Propiedades Vendidas</p>
</div>

<script>
function animateCounter(element) {
    const target = parseInt(element.dataset.count);
    const duration = 2000;
    const increment = target / (duration / 16);
    let current = 0;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

document.querySelectorAll('.counter-number').forEach(animateCounter);
</script>
```

---

## 🎨 Badges y Etiquetas

### Badge de Estado

```xml
<!-- Nuevo -->
<span class="badge bg-success">
    <i class="fa fa-star me-1"></i> Nuevo
</span>

<!-- Destacado -->
<span class="badge bg-warning text-dark">
    <i class="fa fa-fire me-1"></i> Destacado
</span>

<!-- Reservado -->
<span class="badge bg-info">
    <i class="fa fa-clock me-1"></i> Reservado
</span>

<!-- Vendido -->
<span class="badge bg-secondary">
    <i class="fa fa-check me-1"></i> Vendido
</span>
```

---

## 🔘 Botones

### Botones Primarios

```xml
<!-- Danger (Principal) -->
<button class="btn btn-danger">
    <i class="fa fa-search me-1"></i> Buscar
</button>

<!-- Outline -->
<button class="btn btn-outline-danger">
    Ver Detalles
</button>

<!-- Con ícono -->
<button class="btn btn-danger">
    <i class="fa fa-heart me-1"></i> Agregar a Favoritos
</button>

<!-- Loading State -->
<button class="btn btn-danger" disabled>
    <span class="spinner-border spinner-border-sm me-1"></span>
    Cargando...
</button>
```

### Grupo de Botones

```xml
<div class="btn-group" role="group">
    <button type="button" class="btn btn-outline-danger active">
        <i class="fa fa-th"></i> Grid
    </button>
    <button type="button" class="btn btn-outline-danger">
        <i class="fa fa-list"></i> Lista
    </button>
    <button type="button" class="btn btn-outline-danger">
        <i class="fa fa-map"></i> Mapa
    </button>
</div>
```

---

## 🎯 Call to Action (CTA)

### CTA Banner

```xml
<section class="cta-banner bg-danger text-white py-5">
    <div class="container">
        <div class="row align-items-center">
            <div class="col-md-8">
                <h2 class="mb-2">¿Tienes una propiedad para vender?</h2>
                <p class="mb-md-0">Déjanos ayudarte a encontrar el comprador perfecto</p>
            </div>
            <div class="col-md-4 text-md-end">
                <a href="/contacto" class="btn btn-light btn-lg">
                    Contáctanos
                </a>
            </div>
        </div>
    </div>
</section>
```

---

## 📱 Componentes Móviles

### Menú Hamburguesa

```xml
<button class="navbar-toggler" type="button" 
        data-bs-toggle="collapse" 
        data-bs-target="#navbarNav">
    <span class="navbar-toggler-icon"></span>
</button>

<div class="collapse navbar-collapse" id="navbarNav">
    <ul class="navbar-nav ms-auto">
        <li class="nav-item">
            <a class="nav-link" href="/">Inicio</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/properties">Propiedades</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/services">Servicios</a>
        </li>
    </ul>
</div>
```

---

## 💬 Chat Widget (Placeholder)

```xml
<div class="chat-widget position-fixed bottom-0 end-0 m-3">
    <button class="btn btn-danger rounded-circle" 
            style="width: 60px; height: 60px;">
        <i class="fa fa-comment fa-lg"></i>
    </button>
</div>
```

---

**Nota:** Todos estos componentes están diseñados para ser compatibles con modo oscuro automáticamente. Las variables CSS definidas en `bohio_custom_styles.css` se encargan de los ajustes de color.

**Última actualización:** Octubre 2025
