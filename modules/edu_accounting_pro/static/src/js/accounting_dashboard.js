/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class AccountingDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            stats: {
                total_invoiced: 0,
                total_collected: 0,
                total_outstanding: 0,
                collection_rate: 0,
                overdue_count: 0,
                pending_payments: 0
            },
            recent_payments: [],
            overdue_invoices: [],
            monthly_data: [],
            loading: true
        });

        onWillStart(this.loadDashboardData);
    }

    async loadDashboardData() {
        try {
            // Charger les statistiques générales
            const stats = await this.orm.call(
                "edu.accounting.config",
                "get_dashboard_stats",
                []
            );
            
            // Charger les paiements récents
            const recent_payments = await this.orm.call(
                "edu.student.payment",
                "get_recent_payments",
                [10] // Limite de 10 paiements
            );
            
            // Charger les factures en retard
            const overdue_invoices = await this.orm.call(
                "edu.student.invoice",
                "get_overdue_invoices",
                []
            );
            
            // Charger les données mensuelles pour les graphiques
            const monthly_data = await this.orm.call(
                "edu.accounting.config",
                "get_monthly_collection_data",
                []
            );

            this.state.stats = stats;
            this.state.recent_payments = recent_payments;
            this.state.overdue_invoices = overdue_invoices;
            this.state.monthly_data = monthly_data;
            this.state.loading = false;

            // Initialiser les graphiques après le chargement des données
            this.$nextTick(() => {
                this.initializeCharts();
            });

        } catch (error) {
            console.error("Erreur lors du chargement du tableau de bord:", error);
            this.notification.add(
                "Erreur lors du chargement des données du tableau de bord",
                { type: "danger" }
            );
            this.state.loading = false;
        }
    }

    initializeCharts() {
        // Graphique de collecte mensuelle
        this.renderCollectionChart();
        
        // Graphique des statuts de paiement
        this.renderPaymentStatusChart();
    }

    renderCollectionChart() {
        const ctx = document.getElementById('collectionChart');
        if (!ctx) return;

        const monthlyData = this.state.monthly_data;
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: monthlyData.map(d => d.month),
                datasets: [{
                    label: 'Montant Collecté',
                    data: monthlyData.map(d => d.collected),
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Montant Facturé',
                    data: monthlyData.map(d => d.invoiced),
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return new Intl.NumberFormat('fr-FR', {
                                    style: 'currency',
                                    currency: 'EUR'
                                }).format(value);
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + 
                                       new Intl.NumberFormat('fr-FR', {
                                           style: 'currency',
                                           currency: 'EUR'
                                       }).format(context.parsed.y);
                            }
                        }
                    }
                }
            }
        });
    }

    renderPaymentStatusChart() {
        const ctx = document.getElementById('paymentStatusChart');
        if (!ctx) return;

        const stats = this.state.stats;
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Payé', 'Partiel', 'En Retard', 'Brouillon'],
                datasets: [{
                    data: [
                        stats.paid_count || 0,
                        stats.partial_count || 0,
                        stats.overdue_count || 0,
                        stats.draft_count || 0
                    ],
                    backgroundColor: [
                        '#28a745',
                        '#ffc107',
                        '#dc3545',
                        '#6c757d'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Actions rapides
    async onCreateInvoice() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Nouvelle Facture',
            res_model: 'edu.student.invoice',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current'
        });
    }

    async onRegisterPayment() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Nouveau Paiement',
            res_model: 'edu.student.payment',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current'
        });
    }

    async onViewOverdueInvoices() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Factures en Retard',
            res_model: 'edu.student.invoice',
            view_mode: 'tree,form',
            domain: [['state', '=', 'overdue']],
            target: 'current'
        });
    }

    async onViewRecentPayments() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Paiements Récents',
            res_model: 'edu.student.payment',
            view_mode: 'tree,form',
            domain: [['state', '=', 'posted']],
            context: {
                'search_default_recent': 1
            },
            target: 'current'
        });
    }

    // Formatage des montants
    formatCurrency(amount) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR'
        }).format(amount);
    }

    // Formatage des dates
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR');
    }

    // Actualiser les données
    async refreshDashboard() {
        this.state.loading = true;
        await this.loadDashboardData();
        this.notification.add("Tableau de bord actualisé", { type: "success" });
    }
}

AccountingDashboard.template = "edu_accounting_pro.AccountingDashboard";

// Enregistrer le composant
registry.category("actions").add("edu_accounting_dashboard", AccountingDashboard);
