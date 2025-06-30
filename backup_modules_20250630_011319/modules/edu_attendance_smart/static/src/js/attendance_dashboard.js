/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class AttendanceDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            activeSessions: 0,
            presentCount: 0,
            absentCount: 0,
            lateCount: 0,
            loading: true
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });

        onMounted(() => {
            this.startAutoRefresh();
        });
    }

    async loadDashboardData() {
        try {
            const data = await this.orm.call(
                "edu.attendance.session",
                "get_dashboard_data",
                []
            );
            
            this.state.activeSessions = data.active_sessions || 0;
            this.state.presentCount = data.present_count || 0;
            this.state.absentCount = data.absent_count || 0;
            this.state.lateCount = data.late_count || 0;
            this.state.loading = false;
        } catch (error) {
            console.error("Erreur lors du chargement des données:", error);
            this.notification.add("Erreur lors du chargement des données", {
                type: "danger"
            });
            this.state.loading = false;
        }
    }

    startAutoRefresh() {
        // Actualiser les données toutes les 30 secondes
        setInterval(() => {
            this.loadDashboardData();
        }, 30000);
    }

    async refreshData() {
        this.state.loading = true;
        await this.loadDashboardData();
    }
}

AttendanceDashboard.template = "edu_attendance_smart.AttendanceDashboard";

registry.category("actions").add("edu_attendance_smart.dashboard", AttendanceDashboard);

console.log("Module Education Enhanced - JavaScript chargé");
