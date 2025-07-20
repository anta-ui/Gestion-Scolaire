# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json

class HealthAlertAPIController(http.Controller):
    
    @http.route('/api/health_alerts', auth='user', type='json', methods=['GET'], csrf=False)
    def get_health_alerts(self, **kwargs):
        alerts = request.env['health.alert'].sudo().search([], limit=50)
        result = []
        for alert in alerts:
            result.append({
                'id': alert.id,
                'name': alert.name,
                'description': alert.description,
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'state': alert.state,
                'student_id': alert.student_id.id if alert.student_id else None,
                'created_by': alert.created_by.name,
                'due_date': alert.due_date,
            })
        return {'status': 200, 'data': result}
    
    @http.route('/api/health_alerts/<int:alert_id>', auth='user', type='json', methods=['GET'], csrf=False)
    def get_single_alert(self, alert_id, **kwargs):
        alert = request.env['health.alert'].sudo().browse(alert_id)
        if not alert.exists():
            return {'status': 404, 'error': 'Health alert not found'}
        
        return {
            'status': 200,
            'data': {
                'id': alert.id,
                'name': alert.name,
                'description': alert.description,
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'state': alert.state,
                'student_id': alert.student_id.id if alert.student_id else None,
                'created_by': alert.created_by.name,
                'due_date': alert.due_date,
            }
        }

    @http.route('/api/health_alerts', auth='user', type='json', methods=['POST'], csrf=False)
    def create_health_alert(self, **post):
        try:
            required_fields = ['name', 'description', 'alert_type', 'severity']
            for field in required_fields:
                if field not in post:
                    return {'status': 400, 'error': f'Missing required field: {field}'}
            
            alert = request.env['health.alert'].sudo().create({
                'name': post.get('name'),
                'description': post.get('description'),
                'alert_type': post.get('alert_type'),
                'severity': post.get('severity'),
                'student_id': post.get('student_id'),
                'due_date': post.get('due_date'),
            })
            return {'status': 201, 'id': alert.id}
        
        except Exception as e:
            return {'status': 500, 'error': str(e)}

    @http.route('/api/health_alerts/<int:alert_id>/resolve', auth='user', type='json', methods=['POST'], csrf=False)
    def resolve_health_alert(self, alert_id, **post):
        alert = request.env['health.alert'].sudo().browse(alert_id)
        if not alert.exists():
            return {'status': 404, 'error': 'Health alert not found'}
        
        alert.action_resolve()
        return {'status': 200, 'message': f'Alert {alert.name} resolved'}

