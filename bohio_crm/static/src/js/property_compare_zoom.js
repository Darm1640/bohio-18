/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, useRef, onMounted } from "@odoo/owl";

/**
 * Widget de Zoom para Kanban de Comparación de Propiedades
 *
 * Características:
 * - Zoom in/out con botones
 * - Modo fullscreen
 * - Scroll horizontal suave
 * - Control con teclado (+ / - / F)
 */
export class PropertyCompareZoom extends Component {
    setup() {
        this.state = useState({
            zoomLevel: 100,
            isFullscreen: false,
        });

        this.kanbanRef = useRef("propertyKanban");
        this.containerRef = useRef("zoomContainer");

        onMounted(() => {
            this.setupKeyboardShortcuts();
            this.observeKanbanChanges();
        });
    }

    /**
     * Aumentar zoom en 10%
     */
    zoomIn() {
        if (this.state.zoomLevel < 200) {
            this.state.zoomLevel += 10;
            this.applyZoom();
        }
    }

    /**
     * Disminuir zoom en 10%
     */
    zoomOut() {
        if (this.state.zoomLevel > 50) {
            this.state.zoomLevel -= 10;
            this.applyZoom();
        }
    }

    /**
     * Resetear zoom a 100%
     */
    resetZoom() {
        this.state.zoomLevel = 100;
        this.applyZoom();
    }

    /**
     * Aplicar el nivel de zoom al kanban
     */
    applyZoom() {
        const kanbanEl = this.kanbanRef.el;
        if (kanbanEl) {
            kanbanEl.style.transform = `scale(${this.state.zoomLevel / 100})`;
            kanbanEl.style.transformOrigin = "top left";

            // Ajustar el tamaño del contenedor para compensar el escalado
            const container = this.containerRef.el;
            if (container) {
                const scaleFactor = this.state.zoomLevel / 100;
                container.style.height = `${kanbanEl.scrollHeight * scaleFactor}px`;
            }
        }
    }

    /**
     * Toggle modo fullscreen
     */
    toggleFullscreen() {
        const container = this.containerRef.el;

        if (!this.state.isFullscreen) {
            if (container.requestFullscreen) {
                container.requestFullscreen();
            } else if (container.webkitRequestFullscreen) {
                container.webkitRequestFullscreen();
            } else if (container.msRequestFullscreen) {
                container.msRequestFullscreen();
            }
            this.state.isFullscreen = true;
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            this.state.isFullscreen = false;
        }
    }

    /**
     * Configurar atajos de teclado
     */
    setupKeyboardShortcuts() {
        const container = this.containerRef.el;
        if (container) {
            container.addEventListener('keydown', (e) => {
                // Ctrl/Cmd + Plus
                if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '=')) {
                    e.preventDefault();
                    this.zoomIn();
                }
                // Ctrl/Cmd + Minus
                else if ((e.ctrlKey || e.metaKey) && e.key === '-') {
                    e.preventDefault();
                    this.zoomOut();
                }
                // Ctrl/Cmd + 0
                else if ((e.ctrlKey || e.metaKey) && e.key === '0') {
                    e.preventDefault();
                    this.resetZoom();
                }
                // F para fullscreen
                else if (e.key === 'f' || e.key === 'F') {
                    e.preventDefault();
                    this.toggleFullscreen();
                }
            });

            // Listener para salir de fullscreen
            document.addEventListener('fullscreenchange', () => {
                if (!document.fullscreenElement) {
                    this.state.isFullscreen = false;
                }
            });
        }
    }

    /**
     * Observar cambios en el kanban (nuevas propiedades añadidas)
     */
    observeKanbanChanges() {
        const kanbanEl = this.kanbanRef.el;
        if (kanbanEl && window.MutationObserver) {
            const observer = new MutationObserver(() => {
                // Re-aplicar zoom cuando cambia el contenido
                if (this.state.zoomLevel !== 100) {
                    this.applyZoom();
                }
            });

            observer.observe(kanbanEl, {
                childList: true,
                subtree: true,
            });
        }
    }

    /**
     * Scroll suave hacia la izquierda
     */
    scrollLeft() {
        const container = this.containerRef.el;
        if (container) {
            container.scrollBy({
                left: -300,
                behavior: 'smooth'
            });
        }
    }

    /**
     * Scroll suave hacia la derecha
     */
    scrollRight() {
        const container = this.containerRef.el;
        if (container) {
            container.scrollBy({
                left: 300,
                behavior: 'smooth'
            });
        }
    }
}

PropertyCompareZoom.template = "bohio_crm.PropertyCompareZoomTemplate";

// Registrar el componente en el registro de vistas (Odoo 18 format)
registry.category("view_widgets").add("property_compare_zoom", {
    component: PropertyCompareZoom,
});
