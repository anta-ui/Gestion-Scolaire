# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class HealthAlertController(http.Controller):

    @http.route('/api/health/alerts', type='json', auth='user')
    def list_health_alerts(self, **kwargs):
        alerts = request.env['health.alert'].search([])
        data = alerts.read([
            'id', 'name', 'description', 'alert_type', 'severity',
            'state', 'student_id', 'health_record_id', 'due_date',
            'resolved_date', 'is_archived'
        ])
        return {'status': 200, 'alerts': data}

    @http.route('/api/health/alerts/<int:alert_id>', type='json', auth='user')
    def get_health_alert(self, alert_id, **kwargs):
        alert = request.env['health.alert'].browse(alert_id)
        if not alert.exists():
            return {'status': 404, 'error': 'Alerte non trouvée'}
        return {'status': 200, 'alert': alert.read()[0]}

    @http.route('/api/health/alerts', type='json', auth='user', methods=['POST'])
    def create_health_alert(self, **kwargs):
        try:
            alert = request.env['health.alert'].create(kwargs)
            return {'status': 201, 'id': alert.id}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/health/alerts/<int:alert_id>', type='json', auth='user', methods=['PUT'])
    def update_health_alert(self, alert_id, **kwargs):
        alert = request.env['health.alert'].browse(alert_id)
        if not alert.exists():
            return {'status': 404, 'error': 'Alerte non trouvée'}
        try:
            alert.write(kwargs)
            return {'status': 200, 'message': 'Alerte mise à jour'}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/health/alerts/<int:alert_id>', type='json', auth='user', methods=['DELETE'])
    def delete_health_alert(self, alert_id):
        alert = request.env['health.alert'].browse(alert_id)
        if not alert.exists():
            return {'status': 404, 'error': 'Alerte non trouvée'}
        alert.unlink()
        return {'status': 200, 'message': 'Alerte supprimée'}
