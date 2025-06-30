/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class TransportDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            fleetStats: {},
            liveTrips: [],
            alerts: [],
            loading: true,
        });
        
        this.loadDashboardData();
        
        // Mise à jour automatique toutes les 30 secondes
        setInterval(() => {
            this.loadLiveData();
        }, 30000);
    }
    
    async loadDashboardData() {
        try {
            // Statistiques de la flotte
            const fleetStats = await this.orm.call(
                "edu.transport.vehicle",
                "get_fleet_statistics",
                []
            );
            
            // Trajets en cours
            const liveTrips = await this.orm.searchRead(
                "edu.transport.trip",
                [["state", "=", "in_progress"]],
                ["name", "route_id", "vehicle_id", "driver_id", "student_count"]
            );
            
            // Alertes actives
            const alerts = await this.orm.call(
                "edu.transport.vehicle",
                "check_vehicle_alerts",
                []
            );
            
            this.state.fleetStats = fleetStats;
            this.state.liveTrips = liveTrips;
            this.state.alerts = alerts;
            this.state.loading = false;
            
        } catch (error) {
            console.error("Erreur lors du chargement du dashboard transport:", error);
            this.state.loading = false;
        }
    }
    
    async loadLiveData() {
        // Recharger seulement les données temps réel
        try {
            const liveTrips = await this.orm.searchRead(
                "edu.transport.trip",
                [["state", "=", "in_progress"]],
                ["name", "route_id", "vehicle_id", "driver_id", "student_count"]
            );
            
            this.state.liveTrips = liveTrips;
        } catch (error) {
            console.error("Erreur lors de la mise à jour temps réel:", error);
        }
    }
    
    async onEmergencyAlert() {
        // Déclencher une alerte d'urgence
        const action = await this.orm.call(
            "edu.transport.emergency",
            "create_emergency_alert",
            []
        );
        
        this.env.services.action.doAction(action);
    }
}

TransportDashboard.template = "edu_transport_manager.Dashboard";

registry.category("actions").add("transport_dashboard", TransportDashboard);
