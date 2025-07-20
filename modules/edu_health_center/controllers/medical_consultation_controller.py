# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class HealthAPIController(http.Controller):
    
    @http.route('/api/health/records', type='json', auth='user', methods=['GET'])
    def get_health_records(self, **kwargs):
        records = request.env['edu.health.record'].sudo().search([])
        result = []
        for rec in records:
            result.append({
                'id': rec.id,
                'student_name': rec.student_id.name,
                'blood_type': rec.blood_type,
                'age': rec.age,
                'bmi': rec.bmi,
                'record_number': rec.record_number,
            })
        return {'records': result}
    
    @http.route('/api/health/record/<int:record_id>', type='json', auth='user', methods=['GET'])
    def get_health_record(self, record_id, **kwargs):
        record = request.env['edu.health.record'].sudo().browse(record_id)
        if not record.exists():
            return {'error': 'Record not found'}
        return {
            'id': record.id,
            'student_name': record.student_id.name,
            'allergies': record.allergies,
            'chronic_conditions': record.chronic_conditions,
            'blood_type': record.blood_type,
            'bmi': record.bmi,
            'age': record.age,
            'record_number': record.record_number,
        }
    
    @http.route('/api/health/record', type='json', auth='user', methods=['POST'])
    def create_health_record(self, **kwargs):
        try:
            data = kwargs.get('data', {})
            record = request.env['edu.health.record'].sudo().create(data)
            return {'id': record.id, 'message': 'Record created'}
        except Exception as e:
            return {'error': str(e)}
    
    @http.route('/api/health/alerts', type='json', auth='user', methods=['GET'])
    def get_health_alerts(self, **kwargs):
        alerts = request.env['health.alert'].sudo().search([])
        return [{
            'id': alert.id,
            'name': alert.name,
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'state': alert.state,
        } for alert in alerts]
    
    @http.route('/api/consultations', type='json', auth='user', methods=['GET'])
    def get_consultations(self, **kwargs):
        consultations = request.env['edu.medical.consultation'].sudo().search([])
        return [{
            'id': cons.id,
            'student_name': cons.student_id.name,
            'date': cons.consultation_date,
            'state': cons.state,
            'diagnosis': cons.diagnosis,
        } for cons in consultations]
