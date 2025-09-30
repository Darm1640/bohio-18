/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CrmBohioFormController extends FormController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
    }

    /**
     * Agrupa las propiedades comparadas por tipo de propiedad
     */
    async action_group_properties_by_type() {
        const record = this.model.root;
        const comparedPropertyIds = record.data.compared_properties_ids;

        if (!comparedPropertyIds || comparedPropertyIds.length === 0) {
            this.notification.add("No hay propiedades para agrupar", { type: "warning" });
            return;
        }

        try {
            // Obtener las propiedades con su tipo
            const properties = await this.orm.searchRead(
                "product.template",
                [["id", "in", comparedPropertyIds]],
                ["default_code", "name", "property_type_id", "list_price", "property_area", "num_bedrooms", "num_bathrooms"]
            );

            // Agrupar por tipo
            const groupedByType = {};
            properties.forEach(prop => {
                const type = (prop.property_type_id && prop.property_type_id[1]) || "Sin Tipo";
                if (!groupedByType[type]) {
                    groupedByType[type] = [];
                }
                groupedByType[type].push(prop);
            });

            // Crear mensaje con las propiedades agrupadas
            let message = "<h4>Propiedades Agrupadas por Tipo:</h4>";
            for (const [type, props] of Object.entries(groupedByType)) {
                message += `<h5>${type} (${props.length})</h5><ul>`;
                props.forEach(prop => {
                    message += `<li><strong>${prop.default_code || 'Sin código'}</strong> - ${prop.name} |
                                $${prop.list_price} | ${prop.property_area || 0}m² |
                                ${prop.num_bedrooms || 0} hab | ${prop.num_bathrooms || 0} baños</li>`;
                });
                message += "</ul>";
            }

            this.notification.add(message, {
                type: "info",
                sticky: true,
                className: "o_notification_grouped_properties"
            });

        } catch (error) {
            this.notification.add("Error al agrupar propiedades: " + error.message, { type: "danger" });
        }
    }

    /**
     * Remueve una propiedad de la comparación
     */
    async action_remove_from_comparison(propertyId) {
        const record = this.model.root;
        try {
            await this.orm.call(
                "crm.lead",
                "write",
                [[record.resId], {
                    compared_properties_ids: [[3, propertyId]]  // comando (3, id) para unlink
                }]
            );
            await record.load();
            this.notification.add("Propiedad removida de la comparación", { type: "success" });
        } catch (error) {
            this.notification.add("Error al remover propiedad: " + error.message, { type: "danger" });
        }
    }

    /**
     * Vista de propiedades recomendadas basada en preferencias
     */
    async action_view_recommended_properties() {
        const record = this.model.root;
        const data = record.data;

        // Construir dominio basado en preferencias del cliente
        const domain = [["is_property", "=", true], ["state", "=", "free"]];

        if (data.desired_property_type_id) {
            domain.push(["property_type_id", "=", data.desired_property_type_id[0]]);
        }
        if (data.desired_city) {
            domain.push(["city_id.name", "ilike", data.desired_city]);
        }
        if (data.desired_neighborhood) {
            domain.push(["neighborhood_id.name", "ilike", data.desired_neighborhood]);
        }
        if (data.budget_min) {
            domain.push(["list_price", ">=", data.budget_min]);
        }
        if (data.budget_max) {
            domain.push(["list_price", "<=", data.budget_max]);
        }
        if (data.min_bedrooms) {
            domain.push(["num_bedrooms", ">=", data.min_bedrooms]);
        }
        if (data.min_bathrooms) {
            domain.push(["num_bathrooms", ">=", data.min_bathrooms]);
        }
        if (data.min_area) {
            domain.push(["property_area", ">=", data.min_area]);
        }
        if (data.max_area) {
            domain.push(["property_area", "<=", data.max_area]);
        }

        // Abrir vista de propiedades con el dominio filtrado
        this.action.doAction({
            name: "Propiedades Recomendadas",
            type: "ir.actions.act_window",
            res_model: "product.template",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: domain,
            context: {
                default_is_property: true,
                search_default_group_by_type: 1,
            },
        });
    }

    /**
     * Vista del comparador de propiedades
     */
    async action_view_compared_properties() {
        const record = this.model.root;
        const comparedIds = record.data.compared_properties_ids || [];

        if (comparedIds.length === 0) {
            this.notification.add("No hay propiedades para comparar", { type: "warning" });
            return;
        }

        this.action.doAction({
            name: "Comparador de Propiedades",
            type: "ir.actions.act_window",
            res_model: "product.template",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain: [["id", "in", comparedIds]],
            context: {
                default_is_property: true,
                create: false,
                edit: false,
            },
        });
    }
}

CrmBohioFormController.template = "web.FormView";

registry.category("views").add("crm_bohio_form", {
    ...registry.category("views").get("form"),
    Controller: CrmBohioFormController,
});