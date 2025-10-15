/** @odoo-module */

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, onMounted, useState } from "@odoo/owl";

/**
 * BOHIO CRM - Quick Create Inteligente
 *
 * Funcionalidades:
 * 1. Muestra/oculta campos según service_interested
 * 2. Sistema de sugerencias basado en uso frecuente
 * 3. Validaciones condicionales
 * 4. Autocompletado inteligente
 */

export class BohioCRMQuickCreateController extends FormController {
    setup() {
        super.setup();

        this.orm = useService("orm");
        this.notification = useService("notification");

        // Estado para sugerencias
        this.state = useState({
            suggestions: [],
            recentChoices: {},
            fieldVisibility: {},
        });

        onWillStart(async () => {
            await this.loadSuggestions();
        });

        onMounted(() => {
            this.setupFieldWatchers();
            this.loadRecentChoices();
        });
    }

    /**
     * Cargar sugerencias desde el backend
     */
    async loadSuggestions() {
        try {
            const suggestions = await this.orm.call(
                "crm.lead",
                "get_smart_suggestions",
                []
            );
            this.state.suggestions = suggestions;
        } catch (error) {
            console.error("Error cargando sugerencias:", error);
        }
    }

    /**
     * Cargar elecciones recientes del localStorage
     */
    loadRecentChoices() {
        const stored = localStorage.getItem('bohio_crm_recent_choices');
        if (stored) {
            try {
                this.state.recentChoices = JSON.parse(stored);
            } catch (e) {
                console.error("Error parseando choices:", e);
            }
        }
    }

    /**
     * Guardar elección en localStorage
     */
    saveChoice(fieldName, value) {
        if (!this.state.recentChoices[fieldName]) {
            this.state.recentChoices[fieldName] = [];
        }

        // Agregar al inicio
        this.state.recentChoices[fieldName].unshift({
            value: value,
            timestamp: Date.now(),
        });

        // Mantener solo las últimas 10
        this.state.recentChoices[fieldName] = this.state.recentChoices[fieldName].slice(0, 10);

        // Guardar en localStorage
        localStorage.setItem(
            'bohio_crm_recent_choices',
            JSON.stringify(this.state.recentChoices)
        );
    }

    /**
     * Configurar watchers para campos clave
     */
    setupFieldWatchers() {
        // Observar cambios en service_interested
        this.model.root.onFieldChange("service_interested", () => {
            this.onServiceInterestedChange();
        });

        // Observar cambios en client_type
        this.model.root.onFieldChange("client_type", () => {
            this.onClientTypeChange();
        });

        // Observar cambios en budget
        this.model.root.onFieldChange("budget_min", () => {
            this.suggestPropertiesByBudget();
        });

        this.model.root.onFieldChange("budget_max", () => {
            this.suggestPropertiesByBudget();
        });

        // Observar cambios en has_pets
        this.model.root.onFieldChange("has_pets", () => {
            this.onPetsChange();
        });

        // Observar cambios en requires_parking
        this.model.root.onFieldChange("requires_parking", () => {
            this.onParkingChange();
        });
    }

    /**
     * Cuando cambia el servicio de interés
     */
    async onServiceInterestedChange() {
        const serviceValue = this.model.root.data.service_interested;

        // Guardar elección
        this.saveChoice('service_interested', serviceValue);

        // Lógica condicional según el servicio
        switch(serviceValue) {
            case 'sale':
                this.setupForSale();
                break;
            case 'rent':
                this.setupForRent();
                break;
            case 'projects':
                this.setupForProjects();
                break;
            case 'consign':
                this.setupForConsign();
                break;
            case 'legal':
            case 'marketing':
            case 'corporate':
            case 'valuation':
                this.setupForServices();
                break;
        }

        // Sugerir client_type basado en service_interested
        this.suggestClientType(serviceValue);
    }

    /**
     * Configurar para VENTA
     */
    setupForSale() {
        console.log("📊 Configurando para Venta");

        // Sugerir etiquetas comunes para venta
        this.suggestTags(['Compra', 'Inversión', 'Primera Vivienda']);

        // Sugerir probabilidad inicial
        if (!this.model.root.data.probability) {
            this.model.root.update({ probability: 30 });
        }
    }

    /**
     * Configurar para ARRIENDO
     */
    setupForRent() {
        console.log("🏠 Configurando para Arriendo");

        // Sugerir etiquetas comunes para arriendo
        this.suggestTags(['Arriendo', 'Temporal', 'Largo Plazo']);

        // Sugerir probabilidad inicial
        if (!this.model.root.data.probability) {
            this.model.root.update({ probability: 40 });
        }
    }

    /**
     * Configurar para PROYECTOS
     */
    async setupForProjects() {
        console.log("🏗️ Configurando para Proyectos");

        // Cargar proyectos activos
        try {
            const projects = await this.orm.searchRead(
                "project.worksite",
                [["is_enabled", "=", true]],
                ["id", "name"],
                { limit: 5, order: "create_date desc" }
            );

            if (projects.length > 0) {
                this.notification.add(
                    `📋 Proyectos activos disponibles: ${projects.length}`,
                    { type: "info" }
                );
            }
        } catch (error) {
            console.error("Error cargando proyectos:", error);
        }

        this.suggestTags(['Proyecto Nuevo', 'Preventa', 'Inversión']);
    }

    /**
     * Configurar para CONSIGNACIÓN
     */
    setupForConsign() {
        console.log("📝 Configurando para Consignación");

        // Mostrar mensaje de ayuda
        this.notification.add(
            "💡 Recuerda crear la ficha del inmueble usando el botón 'Crear Ficha'",
            { type: "info", sticky: true }
        );

        this.suggestTags(['Captación', 'Exclusiva', 'Avalúo Pendiente']);
    }

    /**
     * Configurar para SERVICIOS
     */
    setupForServices() {
        console.log("🛠️ Configurando para Servicios");
        this.suggestTags(['Servicio', 'Consultoría']);
    }

    /**
     * Sugerir client_type basado en service_interested
     */
    suggestClientType(service) {
        const suggestions = {
            'sale': 'buyer',
            'rent': 'tenant',
            'projects': 'investor',
            'consign': 'owner',
        };

        const suggested = suggestions[service];
        if (suggested && !this.model.root.data.client_type) {
            this.model.root.update({ client_type: suggested });

            this.notification.add(
                `✨ Tipo de cliente sugerido: ${this.getClientTypeLabel(suggested)}`,
                { type: "success" }
            );
        }
    }

    /**
     * Cuando cambia el tipo de cliente
     */
    onClientTypeChange() {
        const clientType = this.model.root.data.client_type;
        this.saveChoice('client_type', clientType);
    }

    /**
     * Cuando cambia has_pets
     */
    onPetsChange() {
        const hasPets = this.model.root.data.has_pets;

        if (hasPets) {
            // Filtrar propiedades que acepten mascotas
            this.notification.add(
                "🐕 Filtrando propiedades que aceptan mascotas",
                { type: "info" }
            );

            // Agregar tag automáticamente
            this.addTagIfNotExists('Con Mascotas');
        }
    }

    /**
     * Cuando cambia requires_parking
     */
    onParkingChange() {
        const requiresParking = this.model.root.data.requires_parking;

        if (requiresParking && !this.model.root.data.parking_spots) {
            // Sugerir 1 parqueadero por defecto
            this.model.root.update({ parking_spots: 1 });
        }
    }

    /**
     * Sugerir propiedades según presupuesto
     */
    async suggestPropertiesByBudget() {
        const budgetMin = this.model.root.data.budget_min;
        const budgetMax = this.model.root.data.budget_max;
        const serviceType = this.model.root.data.service_interested;

        if (!budgetMin || !budgetMax) return;

        try {
            // Buscar propiedades en el rango
            const domain = [
                ["is_property", "=", true],
                ["state", "=", "free"],
            ];

            if (serviceType === 'sale') {
                domain.push(["net_price", ">=", budgetMin]);
                domain.push(["net_price", "<=", budgetMax]);
            } else if (serviceType === 'rent') {
                domain.push(["net_rental_price", ">=", budgetMin]);
                domain.push(["net_rental_price", "<=", budgetMax]);
            }

            const count = await this.orm.searchCount("product.template", domain);

            if (count > 0) {
                this.notification.add(
                    `🏘️ Encontradas ${count} propiedades en tu rango de presupuesto`,
                    { type: "success" }
                );
            } else {
                this.notification.add(
                    "⚠️ No hay propiedades disponibles en este rango. Ajusta el presupuesto.",
                    { type: "warning" }
                );
            }
        } catch (error) {
            console.error("Error buscando propiedades:", error);
        }
    }

    /**
     * Sugerir tags
     */
    async suggestTags(tagNames) {
        try {
            const existingTags = await this.orm.searchRead(
                "crm.tag",
                [["name", "in", tagNames]],
                ["id", "name"]
            );

            if (existingTags.length > 0) {
                const currentTagIds = this.model.root.data.tag_ids || [];
                const newTagIds = existingTags.map(t => t.id);

                // Agregar solo si no existen
                const merged = [...new Set([...currentTagIds, ...newTagIds])];

                this.model.root.update({ tag_ids: merged });
            }
        } catch (error) {
            console.error("Error sugiriendo tags:", error);
        }
    }

    /**
     * Agregar tag si no existe
     */
    async addTagIfNotExists(tagName) {
        try {
            const tag = await this.orm.searchRead(
                "crm.tag",
                [["name", "=", tagName]],
                ["id"],
                { limit: 1 }
            );

            if (tag.length > 0) {
                const currentTagIds = this.model.root.data.tag_ids || [];
                if (!currentTagIds.includes(tag[0].id)) {
                    this.model.root.update({
                        tag_ids: [...currentTagIds, tag[0].id]
                    });
                }
            }
        } catch (error) {
            console.error("Error agregando tag:", error);
        }
    }

    /**
     * Obtener label de client_type
     */
    getClientTypeLabel(value) {
        const labels = {
            'owner': 'Propietario',
            'tenant': 'Arrendatario',
            'buyer': 'Comprador',
            'seller': 'Vendedor',
            'investor': 'Inversionista',
            'other': 'Otro',
        };
        return labels[value] || value;
    }
}

// Registrar vista personalizada
export const bohioCRMQuickCreateFormView = {
    ...formView,
    Controller: BohioCRMQuickCreateController,
};

registry.category("views").add("bohio_crm_quick_create_form", bohioCRMQuickCreateFormView);
