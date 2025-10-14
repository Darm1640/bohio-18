/**
 * BOHIO Real Estate - Renderizado Mejorado de Proyectos
 * 
 * Reemplazar la función renderProyectoCard() en proyectos_page.xml
 * con esta versión mejorada
 */

function renderProyectoCard(proyecto) {
    // Determinar estado y badge
    let estadoBadge = 'bg-success';
    let estadoTexto = 'En Construcción';
    
    if (proyecto.estado === 'planos') {
        estadoBadge = 'bg-info';
        estadoTexto = 'En Planos';
    } else if (proyecto.estado === 'entregado') {
        estadoBadge = 'bg-secondary';
        estadoTexto = 'Entregado';
    }
    
    // Calcular porcentaje de disponibilidad
    const porcentajeDisponible = proyecto.unidades > 0 
        ? Math.round((proyecto.disponibles / proyecto.unidades) * 100) 
        : 0;
    
    // Determinar color de badge según disponibilidad
    let disponibleBadge = 'bg-danger';
    if (porcentajeDisponible > 50) {
        disponibleBadge = 'bg-success';
    } else if (porcentajeDisponible > 20) {
        disponibleBadge = 'bg-warning';
    }
    
    return `
        <div class="col-lg-6 col-xl-4">
            <div class="card proyecto-card h-100 border-0 shadow-sm" 
                 style="transition: all 0.3s ease; border-radius: 12px; overflow: hidden; cursor: pointer;"
                 onmouseover="this.style.transform='translateY(-10px)'; this.style.boxShadow='0 10px 30px rgba(0,0,0,0.15)'"
                 onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 10px rgba(0,0,0,0.1)'"
                 onclick="window.location.href='/proyecto/${proyecto.id}'">
                
                <!-- Imagen del proyecto con overlay -->
                <div class="proyecto-image-wrapper position-relative" style="height: 250px; overflow: hidden;">
                    <img src="${proyecto.image_url || '/theme_bohio_real_estate/static/src/img/banner1.jpg'}" 
                         alt="${proyecto.name}" 
                         class="w-100 h-100" 
                         style="object-fit: cover; transition: transform 0.5s ease;"
                         onmouseover="this.style.transform='scale(1.1)'"
                         onmouseout="this.style.transform='scale(1)'"/>
                    
                    <!-- Overlay gradient -->
                    <div class="position-absolute bottom-0 start-0 w-100 h-50" 
                         style="background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);"></div>
                    
                    <!-- Badge de estado - Top Left -->
                    <div class="position-absolute top-0 start-0 m-3">
                        <span class="badge ${estadoBadge} px-3 py-2" 
                              style="font-size: 0.85rem; border-radius: 20px; font-weight: 600;">
                            <i class="bi bi-building me-1"></i>
                            ${estadoTexto}
                        </span>
                    </div>
                    
                    <!-- Badge de disponibilidad - Top Right -->
                    <div class="position-absolute top-0 end-0 m-3">
                        <span class="badge ${disponibleBadge} px-3 py-2" 
                              style="font-size: 0.85rem; border-radius: 20px; font-weight: 600;">
                            <i class="bi bi-house-fill me-1"></i>
                            ${proyecto.disponibles} disponibles
                        </span>
                    </div>
                    
                    <!-- Nombre del proyecto - Bottom (sobre la imagen) -->
                    <div class="position-absolute bottom-0 start-0 w-100 p-3 text-white" style="z-index: 1;">
                        <h5 class="mb-1 fw-bold" style="font-size: 1.3rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
                            ${proyecto.name}
                        </h5>
                        <p class="mb-0 small" style="text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
                            <i class="bi bi-geo-alt-fill me-1"></i>
                            ${proyecto.ubicacion || 'Sin ubicación'}
                        </p>
                    </div>
                </div>
                
                <!-- Contenido del card -->
                <div class="card-body p-4">
                    
                    <!-- Descripción -->
                    <p class="card-text text-muted small mb-3" style="min-height: 60px; line-height: 1.6;">
                        ${proyecto.descripcion || 'Proyecto inmobiliario de alta calidad con excelentes acabados y ubicación estratégica.'}
                    </p>
                    
                    <!-- Estadísticas del proyecto -->
                    <div class="proyecto-stats mb-3 pb-3 border-bottom">
                        <div class="row g-2 text-center">
                            <div class="col-4">
                                <div class="stat-item p-2 rounded" style="background: rgba(227, 30, 36, 0.05);">
                                    <i class="bi bi-building text-danger d-block mb-1" style="font-size: 1.5rem;"></i>
                                    <span class="d-block fw-bold text-dark" style="font-size: 1.2rem;">${proyecto.unidades || 0}</span>
                                    <span class="small text-muted">Unidades</span>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="stat-item p-2 rounded" style="background: rgba(40, 167, 69, 0.05);">
                                    <i class="bi bi-house-check-fill text-success d-block mb-1" style="font-size: 1.5rem;"></i>
                                    <span class="d-block fw-bold text-dark" style="font-size: 1.2rem;">${proyecto.disponibles || 0}</span>
                                    <span class="small text-muted">Disponibles</span>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="stat-item p-2 rounded" style="background: rgba(255, 193, 7, 0.05);">
                                    <i class="bi bi-percent text-warning d-block mb-1" style="font-size: 1.5rem;"></i>
                                    <span class="d-block fw-bold text-dark" style="font-size: 1.2rem;">${porcentajeDisponible}%</span>
                                    <span class="small text-muted">Disponible</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Barra de progreso de disponibilidad -->
                    <div class="availability-progress mb-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <small class="text-muted">Disponibilidad</small>
                            <small class="fw-bold text-danger">${porcentajeDisponible}%</small>
                        </div>
                        <div class="progress" style="height: 8px; border-radius: 10px;">
                            <div class="progress-bar bg-danger" 
                                 role="progressbar" 
                                 style="width: ${porcentajeDisponible}%; border-radius: 10px;"
                                 aria-valuenow="${porcentajeDisponible}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Botones de acción -->
                    <div class="d-flex flex-column gap-2">
                        <!-- Botón principal -->
                        <a href="/proyecto/${proyecto.id}" 
                           class="btn btn-danger w-100 d-flex align-items-center justify-content-center gap-2" 
                           style="border-radius: 8px; padding: 12px; font-weight: 600; transition: all 0.3s;"
                           onclick="event.stopPropagation()"
                           onmouseover="this.style.background='linear-gradient(135deg, #E31E24 0%, #B81820 100%)'; this.style.transform='translateY(-2px)'"
                           onmouseout="this.style.background=''; this.style.transform='translateY(0)'">
                            <i class="bi bi-building"></i>
                            Ver Proyecto Completo
                        </a>
                        
                        <!-- Botones secundarios -->
                        <div class="row g-2">
                            <div class="col-6">
                                <a href="/properties?project_id=${proyecto.id}" 
                                   class="btn btn-outline-danger w-100 btn-sm" 
                                   style="border-radius: 8px; padding: 10px; font-weight: 500; transition: all 0.3s;"
                                   onclick="event.stopPropagation()"
                                   onmouseover="this.style.background='#E31E24'; this.style.color='white'"
                                   onmouseout="this.style.background=''; this.style.color=''">
                                    <i class="bi bi-grid me-1"></i>
                                    Unidades
                                </a>
                            </div>
                            <div class="col-6">
                                <a href="/contacto?proyecto=${proyecto.id}" 
                                   class="btn btn-outline-danger w-100 btn-sm" 
                                   style="border-radius: 8px; padding: 10px; font-weight: 500; transition: all 0.3s;"
                                   onclick="event.stopPropagation()"
                                   onmouseover="this.style.background='#E31E24'; this.style.color='white'"
                                   onmouseout="this.style.background=''; this.style.color=''">
                                    <i class="bi bi-envelope me-1"></i>
                                    Contactar
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Función auxiliar para formatear números
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

/**
 * Cargar proyectos con animación de entrada
 */
async function cargarProyectosConAnimacion() {
    const container = document.getElementById('proyectosContainer');
    const loading = document.getElementById('proyectosLoading');
    const empty = document.getElementById('proyectosEmpty');

    try {
        loading.style.display = 'block';
        container.innerHTML = '';
        empty.style.display = 'none';

        const response = await fetch('/bohio/api/proyectos', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {}
            })
        });

        const data = await response.json();
        allProyectos = data.result.proyectos || [];

        loading.style.display = 'none';

        if (allProyectos.length === 0) {
            empty.style.display = 'block';
            return;
        }

        // Renderizar proyectos con animación escalonada
        allProyectos.forEach((proyecto, index) => {
            container.insertAdjacentHTML('beforeend', renderProyectoCard(proyecto));
            
            // Animar entrada
            setTimeout(() => {
                const card = container.children[index];
                if (card) {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(30px)';
                    card.style.transition = 'all 0.5s ease';
                    
                    setTimeout(() => {
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, 50);
                }
            }, index * 100);
        });

        // Actualizar mapa si existe
        if (typeof actualizarMapaProyectos === 'function') {
            actualizarMapaProyectos(allProyectos);
        }

    } catch (error) {
        console.error('Error cargando proyectos:', error);
        loading.style.display = 'none';
        empty.style.display = 'block';
    }
}

// Reemplazar la función original al cargar
document.addEventListener('DOMContentLoaded', function() {
    // Reemplazar cargarProyectos original con la versión mejorada
    if (typeof cargarProyectos !== 'undefined') {
        cargarProyectos = cargarProyectosConAnimacion;
    }
    
    // Ejecutar carga inicial
    cargarProyectosConAnimacion();
});
