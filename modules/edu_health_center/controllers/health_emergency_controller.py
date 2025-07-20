# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class HealthAPIController(http.Controller):

    # ======= Alerte Santé =======
    @http.route('/api/health/alerts', type='json', auth='user', methods=['GET'], csrf=False)
    def get_health_alerts(self):
        alerts = request.env['health.alert'].sudo().search([])
        return [{
            'id': a.id,
            'name': a.name,
            'description': a.description,
            'alert_type': a.alert_type,
            'severity': a.severity,
            'state': a.state,
            'student_id': a.student_id.id if a.student_id else None,
            'created_by': a.created_by.name,
        } for a in alerts]

    @http.route('/api/health/alerts', type='json', auth='user', methods=['POST'], csrf=False)
    def create_health_alert(self, **kwargs):
        values = kwargs.get('params', {})
        alert = request.env['health.alert'].sudo().create({
            'name': values.get('name'),
            'description': values.get('description'),
            'alert_type': values.get('alert_type', 'medical'),
            'severity': values.get('severity', 'medium'),
            'state': values.get('state', 'draft'),
            'student_id': values.get('student_id'),
        })
        return {'id': alert.id, 'message': 'Alerte créée avec succès'}

    # ======= Urgence Médicale =======
    @http.route('/api/health/emergencies', type='json', auth='user', methods=['GET'], csrf=False)
    def get_emergencies(self):
        emergencies = request.env['health.emergency'].sudo().search([])
        return [{
            'id': e.id,
            'name': e.name,
            'student': e.student_id.name,
            'type': e.emergency_type,
            'severity': e.severity_level,
            'state': e.state,
            'date': e.emergency_date,
        } for e in emergencies]

    @http.route('/api/health/emergencies', type='json', auth='user', methods=['POST'], csrf=False)
    def create_emergency(self, **kwargs):
        vals = kwargs.get('params', {})
        emergency = request.env['health.emergency'].sudo().create({
            'health_record_id': vals.get('health_record_id'),
            'emergency_type': vals.get('emergency_type', 'medical'),
            'severity_level': vals.get('severity_level', 'medium'),
            'description': vals.get('description'),
            'location': vals.get('location'),
        })
        return {'id': emergency.id, 'message': 'Urgence créée avec succès'}

    # ======= Dashboard Rapide (Stats) =======
    @http.route('/api/health/dashboard/summary', type='json', auth='user', methods=['GET'], csrf=False)
    def get_dashboard_summary(self):
        dashboard = request.env['health.dashboard'].sudo().search([], limit=1, order='dashboard_date desc')
        if not dashboard:
            return {'error': 'Aucun tableau de bord trouvé'}

        return {
            'date': str(dashboard.dashboard_date),
            'total_students': dashboard.total_students,
            'active_cases': dashboard.active_cases,
            'vaccinations_today': dashboard.vaccinations_today,
            'consultations_today': dashboard.consultations_today,
            'emergencies_today': dashboard.emergencies_today,
            'alert_level': dashboard.alert_level,
        }
