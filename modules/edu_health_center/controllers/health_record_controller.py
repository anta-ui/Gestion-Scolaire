# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class HealthRecordController(http.Controller):

    @http.route('/api/health/records', type='json', auth='user', methods=['POST'], csrf=False)
    def get_health_records(self, **kwargs):
        records = request.env['health.record'].sudo().search([])
        return {
            'status': 'success',
            'data': [{
                'id': r.id,
                'name': r.name,
                'student_id': r.student_id.id if r.student_id else None,
                'student_name': r.student_id.name if r.student_id else None,
                'record_type': r.record_type,
                'date': str(r.date) if r.date else None,
                'doctor_id': r.doctor_id.id if r.doctor_id else None,
                'doctor_name': r.doctor_id.name if r.doctor_id else None,
                'diagnosis': r.diagnosis,
                'treatment': r.treatment,
                'prescription': r.prescription,
                'state': r.state,
                'priority': r.priority,
                'is_emergency': r.is_emergency,
            } for r in records]
        }

    @http.route('/api/health/records/<int:record_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_health_record(self, record_id):
        record = request.env['health.record'].sudo().browse(record_id)
        if not record.exists():
            return {'error': 'Health record not found'}
        return {
            'id': record.id,
            'name': record.name,
            'student_id': record.student_id.id if record.student_id else None,
            'student_name': record.student_id.name if record.student_id else None,
            'record_type': record.record_type,
            'date': str(record.date) if record.date else None,
            'doctor_id': record.doctor_id.id if record.doctor_id else None,
            'doctor_name': record.doctor_id.name if record.doctor_id else None,
            'diagnosis': record.diagnosis,
            'treatment': record.treatment,
            'prescription': record.prescription,
            'state': record.state,
            'priority': record.priority,
            'is_emergency': record.is_emergency,
            'symptoms': record.symptoms,
            'allergies': record.allergies,
            'medications': record.medications,
            'notes': record.notes,
        }

    @http.route('/api/health/records/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_health_record(self, **data):
        try:
            record = request.env['health.record'].sudo().create(data)
            return {'id': record.id, 'message': 'Health record created successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/health/records/<int:record_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_health_record(self, record_id, **data):
        record = request.env['health.record'].sudo().browse(record_id)
        if not record.exists():
            return {'error': 'Health record not found'}
        try:
            record.write(data)
            return {'message': 'Health record updated successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/health/records/<int:record_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_health_record(self, record_id):
        record = request.env['health.record'].sudo().browse(record_id)
        if not record.exists():
            return {'error': 'Health record not found'}
        record.unlink()
        return {'message': 'Health record deleted successfully'}
