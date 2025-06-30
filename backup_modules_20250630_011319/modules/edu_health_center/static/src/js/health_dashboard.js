/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class HealthDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            stats: {},
            alerts: [],
            emergencies: [],
            loading: true,
        });
        
        this.loadDashboardData();
    }
    
    async loadDashboardData() {
        try {
            // Charger les statistiques de santé
            const stats = await this.orm.call(
                "edu.health.record",
                "generate_health_statistics",
                []
            );
            
            // Charger les alertes actives
            const alerts = await this.orm.call(
                "edu.health.alert",
                "get_active_alerts",
                []
            );
            
            // Charger les urgences en cours
            const emergencies = await this.orm.searchRead(
                "edu.health.emergency",
                [["state", "=", "active"]],
                ["name", "emergency_type", "severity_level", "create_date"]
            );
            
            this.state.stats = stats;
            this.state.alerts = alerts;
            this.state.emergencies = emergencies;
            this.state.loading = false;
            
        } catch (error) {
            console.error("Erreur lors du chargement du dashboard santé:", error);
            this.state.loading = false;
        }
    }
    
    async triggerEmergencyAlert() {
        // Déclencher une alerte d'urgence
        const action = await this.orm.call(
            "edu.health.emergency",
            "create_emergency_alert",
            []
        );
        
        // Rediriger vers le formulaire d'urgence
        this.env.services.action.doAction(action);
    }
}

HealthDashboard.template = "edu_health_center.Dashboard";

registry.category("actions").add("health_dashboard", HealthDashboard);
