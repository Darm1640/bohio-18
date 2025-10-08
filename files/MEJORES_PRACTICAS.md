# BOHIO Real Estate - Mejores Prácticas y Guía Técnica

## 📚 Tabla de Contenidos

1. [Mejores Prácticas de Desarrollo](#mejores-prácticas-de-desarrollo)
2. [Optimización de Rendimiento](#optimización-de-rendimiento)
3. [Accesibilidad](#accesibilidad)
4. [Diseño Responsivo](#diseño-responsivo)
5. [Modo Oscuro](#modo-oscuro)
6. [Seguridad](#seguridad)
7. [SEO](#seo)
8. [Testing](#testing)
9. [Deployment](#deployment)

---

## 🎯 Mejores Prácticas de Desarrollo

### Estructura de Código

#### HTML/XML

```xml
<!-- ✅ CORRECTO: Estructura semántica -->
<section class="bohio-services">
    <h2>Nuestros Servicios</h2>
    <div class="row">
        <article class="col-md-4">
            <h3>Servicio 1</h3>
            <p>Descripción</p>
        </article>
    </div>
</section>

<!-- ❌ INCORRECTO: No usar div para todo -->
<div class="services">
    <div class="title">Nuestros Servicios</div>
    <div>
        <div>
            <div>Servicio 1</div>
            <div>Descripción</div>
        </div>
    </div>
</div>
```

#### CSS

```css
/* ✅ CORRECTO: Usar variables CSS */
:root {
    --color-primary: #E31E24;
    --spacing-md: 1rem;
}

.button {
    background-color: var(--color-primary);
    padding: var(--spacing-md);
}

/* ❌ INCORRECTO: Valores hardcodeados */
.button {
    background-color: #E31E24;
    padding: 16px;
}
```

#### JavaScript

```javascript
// ✅ CORRECTO: Código modular y organizado
const PropertySearch = {
    init() {
        this.setupEventListeners();
        this.loadData();
    },
    
    setupEventListeners() {
        // ...
    },
    
    loadData() {
        // ...
    }
};

// ❌ INCORRECTO: Código espagueti
function init() {
    document.querySelector('.btn').addEventListener('click', function() {
        // 100 líneas de código aquí
    });
}
```

### Nomenclatura

#### Clases CSS (BEM - Block Element Modifier)

```css
/* ✅ CORRECTO */
.property-card { }
.property-card__image { }
.property-card__title { }
.property-card--featured { }

/* ❌ INCORRECTO */
.propertyCard { }
.property_image { }
.featuredProperty { }
```

#### Variables JavaScript (camelCase)

```javascript
// ✅ CORRECTO
const propertyPrice = 1000000;
const hasImage = true;
const userPreferences = {};

// ❌ INCORRECTO
const PropertyPrice = 1000000;
const has_image = true;
const user_pref = {};
```

### Comentarios

```javascript
/**
 * Calcula el precio final de una propiedad
 * @param {number} basePrice - Precio base de la propiedad
 * @param {number} discount - Porcentaje de descuento (0-100)
 * @returns {number} Precio final calculado
 */
function calculateFinalPrice(basePrice, discount) {
    return basePrice - (basePrice * discount / 100);
}
```

---

## ⚡ Optimización de Rendimiento

### Lazy Loading de Imágenes

```html
<!-- Implementación -->
<img data-src="/path/to/image.jpg" 
     src="/path/to/placeholder.jpg"
     class="lazy"
     alt="Descripción"/>

<script>
// Observer para lazy loading
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    document.querySelectorAll('img.lazy').forEach(img => {
        imageObserver.observe(img);
    });
}
</script>
```

### Optimización de Imágenes

```bash
# Usar herramientas de compresión
# ImageMagick
convert original.jpg -quality 85 -resize 1920x1080 optimized.jpg

# WebP para navegadores modernos
convert original.jpg -quality 85 optimized.webp
```

### Code Splitting

```javascript
// Cargar módulos bajo demanda
async function loadPropertyDetails(propertyId) {
    const module = await import('./property-details.js');
    module.showDetails(propertyId);
}
```

### Minificación

```bash
# CSS
cssnano bohio_custom_styles.css bohio_custom_styles.min.css

# JavaScript
uglifyjs bohio_custom_scripts.js -o bohio_custom_scripts.min.js -c -m
```

### Caching

```javascript
// Service Worker para caching
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});
```

### Métricas de Rendimiento

```javascript
// Medir rendimiento
const observer = new PerformanceObserver(list => {
    for (const entry of list.getEntries()) {
        console.log(entry.name, entry.startTime);
    }
});

observer.observe({ entryTypes: ['measure', 'navigation'] });
```

---

## ♿ Accesibilidad

### ARIA Labels

```html
<!-- ✅ CORRECTO -->
<button aria-label="Cerrar modal" class="close-btn">
    <i class="fa fa-times" aria-hidden="true"></i>
</button>

<!-- ❌ INCORRECTO -->
<button class="close-btn">
    <i class="fa fa-times"></i>
</button>
```

### Navegación por Teclado

```javascript
// Trap focus en modal
function trapFocus(element) {
    const focusableElements = element.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    element.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            if (e.shiftKey && document.activeElement === firstElement) {
                lastElement.focus();
                e.preventDefault();
            } else if (!e.shiftKey && document.activeElement === lastElement) {
                firstElement.focus();
                e.preventDefault();
            }
        }
    });
}
```

### Contraste de Colores

```css
/* ✅ CORRECTO: Ratio mínimo 4.5:1 para texto normal */
.text-primary {
    color: #111827; /* Negro sobre blanco */
    background: #ffffff;
}

/* ✅ CORRECTO: Ratio mínimo 3:1 para texto grande */
.heading {
    color: #374151;
    background: #ffffff;
}
```

### Screen Readers

```html
<!-- Contenido oculto visualmente pero accesible -->
<span class="sr-only">
    Número de habitaciones: 3
</span>

<style>
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
}
</style>
```

---

## 📱 Diseño Responsivo

### Mobile First

```css
/* ✅ CORRECTO: Mobile First */
.property-card {
    width: 100%;
}

@media (min-width: 768px) {
    .property-card {
        width: 50%;
    }
}

@media (min-width: 1024px) {
    .property-card {
        width: 33.333%;
    }
}

/* ❌ INCORRECTO: Desktop First */
.property-card {
    width: 33.333%;
}

@media (max-width: 1024px) {
    .property-card {
        width: 50%;
    }
}
```

### Breakpoints Consistentes

```css
:root {
    --breakpoint-sm: 640px;
    --breakpoint-md: 768px;
    --breakpoint-lg: 1024px;
    --breakpoint-xl: 1280px;
    --breakpoint-2xl: 1536px;
}
```

### Touch Targets

```css
/* Mínimo 44x44px para elementos táctiles */
.btn,
.link,
.checkbox {
    min-width: 44px;
    min-height: 44px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}
```

### Viewport Meta Tag

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
```

---

## 🌙 Modo Oscuro

### Implementación Completa

```css
/* Variables para ambos modos */
:root {
    --bg-primary: #ffffff;
    --text-primary: #111827;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #1a1a1a;
        --text-primary: #f0f0f0;
    }
}

/* Usar variables */
body {
    background-color: var(--bg-primary);
    color: var(--text-primary);
}
```

### Toggle Manual

```javascript
const DarkModeToggle = {
    init() {
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme) {
            this.setTheme(savedTheme);
        } else if (prefersDark) {
            this.setTheme('dark');
        }
    },
    
    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    },
    
    toggle() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }
};
```

### Transiciones Suaves

```css
* {
    transition: background-color 0.3s ease, color 0.3s ease;
}

/* Excepto para elementos interactivos */
button, a, input {
    transition: all 0.15s ease;
}
```

---

## 🔐 Seguridad

### XSS Prevention

```javascript
// ✅ CORRECTO: Sanitizar inputs
function sanitizeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Usar textContent en lugar de innerHTML
element.textContent = userInput;

// ❌ INCORRECTO
element.innerHTML = userInput;
```

### CSRF Protection

```html
<!-- Incluir token en formularios -->
<form method="post">
    <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>
    <!-- otros campos -->
</form>
```

### Content Security Policy

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline'; 
               style-src 'self' 'unsafe-inline';">
```

---

## 🔍 SEO

### Meta Tags Esenciales

```html
<!-- Título optimizado -->
<title>Apartamento en Venta - 3 Habitaciones - Bogotá | BOHIO</title>

<!-- Descripción -->
<meta name="description" content="Hermoso apartamento de 3 habitaciones en venta en Bogotá. 120m², excelente ubicación. Contáctanos en BOHIO Inmobiliaria.">

<!-- Open Graph -->
<meta property="og:title" content="Apartamento en Venta - 3 Habitaciones - Bogotá">
<meta property="og:description" content="Hermoso apartamento de 3 habitaciones...">
<meta property="og:image" content="https://bohio.com/images/property-123.jpg">
<meta property="og:url" content="https://bohio.com/property/123">
<meta property="og:type" content="website">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Apartamento en Venta - 3 Habitaciones">
<meta name="twitter:description" content="Hermoso apartamento de 3 habitaciones...">
<meta name="twitter:image" content="https://bohio.com/images/property-123.jpg">

<!-- Canonical URL -->
<link rel="canonical" href="https://bohio.com/property/123">
```

### Structured Data

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "RealEstateListing",
  "name": "Apartamento en Venta - 3 Habitaciones",
  "description": "Hermoso apartamento de 3 habitaciones...",
  "url": "https://bohio.com/property/123",
  "image": "https://bohio.com/images/property-123.jpg",
  "price": "250000000",
  "priceCurrency": "COP",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Carrera 15 #93-30",
    "addressLocality": "Bogotá",
    "addressRegion": "Cundinamarca",
    "postalCode": "110221",
    "addressCountry": "CO"
  },
  "numberOfRooms": "3",
  "numberOfBathroomsTotal": "2",
  "floorSize": {
    "@type": "QuantitativeValue",
    "value": "120",
    "unitCode": "MTK"
  }
}
</script>
```

### Sitemap

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://bohio.com/</loc>
        <lastmod>2025-10-08</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://bohio.com/properties</loc>
        <lastmod>2025-10-08</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
</urlset>
```

---

## 🧪 Testing

### Tests Unitarios (JavaScript)

```javascript
describe('PropertySearch', () => {
    it('should sync min and max prices', () => {
        const priceMin = document.getElementById('price_min');
        const priceMax = document.getElementById('price_max');
        
        priceMin.value = '1000000';
        priceMin.dispatchEvent(new Event('blur'));
        
        expect(priceMax.value).toBe('1000000');
    });
});
```

### Tests de Integración

```javascript
describe('Property Search Integration', () => {
    it('should filter properties by price range', async () => {
        const response = await fetch('/properties?price_min=1000000&price_max=2000000');
        const properties = await response.json();
        
        properties.forEach(property => {
            expect(property.price).toBeGreaterThanOrEqual(1000000);
            expect(property.price).toBeLessThanOrEqual(2000000);
        });
    });
});
```

### Tests E2E (Cypress)

```javascript
describe('Property Search Flow', () => {
    it('should search and view property details', () => {
        cy.visit('/properties');
        cy.get('#property_type').select('apartment');
        cy.get('#city_filter').select('Bogotá');
        cy.get('button[type="submit"]').click();
        
        cy.get('.property-card').first().click();
        cy.url().should('include', '/property/');
        cy.get('.property-details').should('be.visible');
    });
});
```

---

## 🚀 Deployment

### Checklist Pre-Deployment

- [ ] Minificar CSS y JavaScript
- [ ] Optimizar imágenes
- [ ] Verificar todos los enlaces
- [ ] Probar en múltiples navegadores
- [ ] Probar en múltiples dispositivos
- [ ] Verificar accesibilidad
- [ ] Ejecutar Lighthouse
- [ ] Revisar errores de consola
- [ ] Configurar HTTPS
- [ ] Configurar CDN
- [ ] Habilitar compresión GZIP
- [ ] Configurar cache headers
- [ ] Crear backup de base de datos

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name bohio.com www.bohio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bohio.com www.bohio.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json;

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://localhost:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Monitoreo

```javascript
// Error tracking
window.addEventListener('error', (event) => {
    // Enviar a servicio de tracking (ej: Sentry)
    console.error('Error:', event.error);
});

// Performance monitoring
const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
        // Enviar métricas a servicio de analytics
        console.log(entry.name, entry.duration);
    }
});

observer.observe({ entryTypes: ['navigation', 'resource'] });
```

---

## 📊 Métricas y KPIs

### Performance Metrics

- **First Contentful Paint (FCP):** < 1.8s
- **Largest Contentful Paint (LCP):** < 2.5s
- **Time to Interactive (TTI):** < 3.8s
- **Cumulative Layout Shift (CLS):** < 0.1

### User Experience Metrics

- **Bounce Rate:** < 40%
- **Pages per Session:** > 3
- **Average Session Duration:** > 3min
- **Conversion Rate:** > 2%

---

**Actualizado:** Octubre 2025  
**Mantenido por:** Equipo de Desarrollo BOHIO
