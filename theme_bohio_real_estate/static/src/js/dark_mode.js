/** @odoo-module **/

/**
 * BOHIO Real Estate - Dark Mode Manager
 * Gestiona el modo oscuro del sitio con persistencia y auto-detección
 */

export class DarkModeManager {
    constructor() {
        this.storageKey = 'bohio-theme';
        this.toggleButton = null;
        this.init();
    }

    init() {
        this.applySavedTheme();
        this.setupDarkModeToggle();
        this.listenToSystemPreferences();
    }

    /**
     * Crea el botón de toggle de modo oscuro
     */
    setupDarkModeToggle() {
        // Evitar duplicados
        if (document.getElementById('darkModeToggle')) {
            this.toggleButton = document.getElementById('darkModeToggle');
            return;
        }

        const toggle = document.createElement('button');
        toggle.id = 'darkModeToggle';
        toggle.className = 'btn btn-sm position-fixed';
        toggle.style.cssText = `
            bottom: 20px;
            right: 20px;
            z-index: 1050;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-lg);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition-fast);
        `;
        toggle.innerHTML = '<i class="fa fa-moon"></i>';
        toggle.setAttribute('aria-label', 'Cambiar modo oscuro');
        toggle.setAttribute('title', 'Cambiar tema');

        toggle.addEventListener('click', () => this.toggleDarkMode());

        // Hover effect
        toggle.addEventListener('mouseenter', () => {
            toggle.style.transform = 'scale(1.1)';
        });
        toggle.addEventListener('mouseleave', () => {
            toggle.style.transform = 'scale(1)';
        });

        document.body.appendChild(toggle);
        this.toggleButton = toggle;
    }

    /**
     * Alterna entre modo claro y oscuro
     */
    toggleDarkMode() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        this.setTheme(newTheme);
        this.saveTheme(newTheme);
        this.updateToggleIcon(newTheme);
        this.announceThemeChange(newTheme);
    }

    /**
     * Aplica el tema guardado o el preferido del sistema
     */
    applySavedTheme() {
        const savedTheme = this.getSavedTheme();
        const prefersDark = this.systemPrefersDark();
        const theme = savedTheme || (prefersDark ? 'dark' : 'light');

        this.setTheme(theme);
        this.updateToggleIcon(theme);
    }

    /**
     * Obtiene el tema actual
     */
    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }

    /**
     * Establece el tema
     */
    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);

        // Actualizar meta theme-color para PWA
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        metaThemeColor.content = theme === 'dark' ? '#1a1a1a' : '#ffffff';
    }

    /**
     * Guarda el tema en localStorage
     */
    saveTheme(theme) {
        try {
            localStorage.setItem(this.storageKey, theme);
        } catch (e) {
            console.warn('No se pudo guardar la preferencia de tema:', e);
        }
    }

    /**
     * Obtiene el tema guardado
     */
    getSavedTheme() {
        try {
            return localStorage.getItem(this.storageKey);
        } catch (e) {
            return null;
        }
    }

    /**
     * Verifica si el sistema prefiere modo oscuro
     */
    systemPrefersDark() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    /**
     * Actualiza el icono del botón toggle
     */
    updateToggleIcon(theme) {
        if (!this.toggleButton) return;

        const icon = this.toggleButton.querySelector('i');
        if (!icon) return;

        if (theme === 'dark') {
            icon.className = 'fa fa-sun';
            this.toggleButton.setAttribute('aria-label', 'Cambiar a modo claro');
            this.toggleButton.setAttribute('title', 'Modo claro');
        } else {
            icon.className = 'fa fa-moon';
            this.toggleButton.setAttribute('aria-label', 'Cambiar a modo oscuro');
            this.toggleButton.setAttribute('title', 'Modo oscuro');
        }
    }

    /**
     * Escucha cambios en las preferencias del sistema
     */
    listenToSystemPreferences() {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

        // Modern API
        if (mediaQuery.addEventListener) {
            mediaQuery.addEventListener('change', (e) => {
                // Solo aplicar si no hay preferencia guardada
                if (!this.getSavedTheme()) {
                    const theme = e.matches ? 'dark' : 'light';
                    this.setTheme(theme);
                    this.updateToggleIcon(theme);
                }
            });
        }
        // Fallback para navegadores antiguos
        else if (mediaQuery.addListener) {
            mediaQuery.addListener((e) => {
                if (!this.getSavedTheme()) {
                    const theme = e.matches ? 'dark' : 'light';
                    this.setTheme(theme);
                    this.updateToggleIcon(theme);
                }
            });
        }
    }

    /**
     * Anuncia el cambio de tema para lectores de pantalla
     */
    announceThemeChange(theme) {
        const announcement = document.createElement('div');
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', 'polite');
        announcement.className = 'visually-hidden';
        announcement.textContent = `Tema cambiado a modo ${theme === 'dark' ? 'oscuro' : 'claro'}`;

        document.body.appendChild(announcement);
        setTimeout(() => announcement.remove(), 1000);
    }

    /**
     * Limpia recursos (útil para SPA)
     */
    destroy() {
        if (this.toggleButton && this.toggleButton.parentNode) {
            this.toggleButton.remove();
        }
        this.toggleButton = null;
    }
}

// Auto-inicialización cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.bohioDarkMode = new DarkModeManager();
    });
} else {
    window.bohioDarkMode = new DarkModeManager();
}

export default DarkModeManager;
