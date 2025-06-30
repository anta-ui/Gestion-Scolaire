/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class LibraryDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            stats: {},
            loading: true,
        });
        
        this.loadDashboardData();
    }
    
    async loadDashboardData() {
        try {
            const stats = await this.orm.call(
                "edu.library.book",
                "get_library_statistics",
                []
            );
            this.state.stats = stats;
            this.state.loading = false;
        } catch (error) {
            console.error("Erreur lors du chargement du dashboard:", error);
            this.state.loading = false;
        }
    }
}

LibraryDashboard.template = "edu_library_plus.Dashboard";

registry.category("actions").add("library_dashboard", LibraryDashboard);
