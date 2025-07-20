# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json

class HealthDashboardAPI(http.Controller):

    @http.route('/api/health_dashboard', type='json', auth='user', methods=['GET'], csrf=False)
    def get_dashboards(self):
        records = request.env['health.dashboard'].sudo().search([], limit=10, order="dashboard_date desc")
        return {
            "count": len(records),
            "items": [
                {
                    "id": r.id,
                    "name": r.name,
                    "date": r.dashboard_date,
                    "total_students": r.total_students,
                    "active_cases": r.active_cases,
                    "consultations_today": r.consultations_today,
                    "vaccinations_today": r.vaccinations_today,
                    "alert_level": r.alert_level,
                }
                for r in records
            ]
        }

    @http.route('/api/health_dashboard/<int:dashboard_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_dashboard(self, dashboard_id):
        record = request.env['health.dashboard'].sudo().browse(dashboard_id)
        if not record.exists():
            return {'error': 'Tableau de bord introuvable'}, 404
        
        return {
            "id": record.id,
            "name": record.name,
            "dashboard_date": record.dashboard_date,
            "total_students": record.total_students,
            "active_cases": record.active_cases,
            "consultations_today": record.consultations_today,
            "emergencies_today": record.emergencies_today,
            "vaccinations_today": record.vaccinations_today,
            "medications_dispensed": record.medications_dispensed,
            "alert_level": record.alert_level,
            "ai_recommendations": record.ai_recommendations,
            "active_alerts": record.active_alerts,
        }

    @http.route('/api/health_dashboard', type='json', auth='user', methods=['POST'], csrf=False)
    def create_dashboard(self, **kwargs):
        values = kwargs.get('params', {})
        dashboard = request.env['health.dashboard'].sudo().create({
            'name': values.get('name', 'Tableau de Bord Santé'),
            'dashboard_date': values.get('dashboard_date'),
        })
        dashboard.action_refresh_data()
        return {
            'id': dashboard.id,
            'message': 'Tableau de bord créé avec succès',
        }

    @http.route('/api/health_dashboard/<int:dashboard_id>/refresh', type='json', auth='user', methods=['POST'], csrf=False)
    def refresh_dashboard(self, dashboard_id):
        record = request.env['health.dashboard'].sudo().browse(dashboard_id)
        if not record.exists():
            return {'error': 'Tableau de bord non trouvé'}, 404
        record.action_refresh_data()
        return {'message': 'Données mises à jour'}
