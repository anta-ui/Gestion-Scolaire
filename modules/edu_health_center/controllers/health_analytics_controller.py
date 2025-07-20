# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class HealthAnalyticsController(http.Controller):

    @http.route('/api/health/analytics', type='json', auth='user')
    def list_analytics(self, **kwargs):
        records = request.env['health.analytics'].sudo().search([], limit=100)
        data = records.read([
            'id', 'name', 'description', 'analysis_type',
            'period_start', 'period_end', 'state', 'total_students',
            'total_consultations', 'total_vaccinations', 'total_emergencies',
            'vaccination_rate', 'emergency_rate', 'consultation_rate',
            'chart_data', 'analysis_report', 'recommendations', 'key_findings',
            'generation_date'
        ])
        return {'status': 200, 'analytics': data}

    @http.route('/api/health/analytics/<int:record_id>', type='json', auth='user')
    def get_analytics(self, record_id, **kwargs):
        record = request.env['health.analytics'].sudo().browse(record_id)
        if not record.exists():
            return {'status': 404, 'error': 'Analyse non trouvée'}
        return {'status': 200, 'analytics': record.read()[0]}

    @http.route('/api/health/analytics', type='json', auth='user', methods=['POST'])
    def create_analytics(self, **kwargs):
        try:
            record = request.env['health.analytics'].sudo().create(kwargs)
            return {'status': 201, 'id': record.id}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/health/analytics/<int:record_id>', type='json', auth='user', methods=['PUT'])
    def update_analytics(self, record_id, **kwargs):
        record = request.env['health.analytics'].sudo().browse(record_id)
        if not record.exists():
            return {'status': 404, 'error': 'Analyse non trouvée'}
        try:
            record.write(kwargs)
            return {'status': 200, 'message': 'Analyse mise à jour'}
        except Exception as e:
            return {'status': 400, 'error': str(e)}

    @http.route('/api/health/analytics/<int:record_id>', type='json', auth='user', methods=['DELETE'])
    def delete_analytics(self, record_id):
        record = request.env['health.analytics'].sudo().browse(record_id)
        if not record.exists():
            return {'status': 404, 'error': 'Analyse non trouvée'}
        record.unlink()
        return {'status': 200, 'message': 'Analyse supprimée'}
