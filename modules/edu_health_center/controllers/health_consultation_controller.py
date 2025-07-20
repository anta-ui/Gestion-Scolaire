# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class HealthConsultationController(http.Controller):

    @http.route('/api/health/consultations', type='json', auth='user', methods=['POST'], csrf=False)
    def get_consultations(self, **kwargs):
        consultations = request.env['health.consultation'].sudo().search([])
        return {
            'status': 'success',
            'data': [{
                'id': c.id,
                'name': c.name,
                'student_id': c.student_id.id if c.student_id else None,
                'student_name': c.student_id.name if c.student_id else None,
                'doctor_id': c.doctor_id.id if c.doctor_id else None,
                'doctor_name': c.doctor_id.name if c.doctor_id else None,
                'consultation_date': str(c.consultation_date) if c.consultation_date else None,
                'consultation_time': str(c.consultation_time) if c.consultation_time else None,
                'consultation_type': c.consultation_type,
                'state': c.state,
                'symptoms': c.symptoms,
                'diagnosis': c.diagnosis,
                'treatment': c.treatment,
                'prescription': c.prescription,
                'follow_up_date': str(c.follow_up_date) if c.follow_up_date else None,
            } for c in consultations]
        }

    @http.route('/api/health/consultations/today', type='json', auth='user', methods=['POST'], csrf=False)
    def get_today_consultations(self, **kwargs):
        from datetime import date
        today = date.today()
        consultations = request.env['health.consultation'].sudo().search([
            ('consultation_date', '=', today)
        ])
        return {
            'status': 'success',
            'data': [{
                'id': c.id,
                'name': c.name,
                'student_id': c.student_id.id if c.student_id else None,
                'student_name': c.student_id.name if c.student_id else None,
                'doctor_id': c.doctor_id.id if c.doctor_id else None,
                'doctor_name': c.doctor_id.name if c.doctor_id else None,
                'consultation_time': str(c.consultation_time) if c.consultation_time else None,
                'consultation_type': c.consultation_type,
                'state': c.state,
            } for c in consultations]
        }

    @http.route('/api/health/consultations/<int:consultation_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_consultation(self, consultation_id):
        consultation = request.env['health.consultation'].sudo().browse(consultation_id)
        if not consultation.exists():
            return {'error': 'Consultation not found'}
        return {
            'id': consultation.id,
            'name': consultation.name,
            'student_id': consultation.student_id.id if consultation.student_id else None,
            'student_name': consultation.student_id.name if consultation.student_id else None,
            'doctor_id': consultation.doctor_id.id if consultation.doctor_id else None,
            'doctor_name': consultation.doctor_id.name if consultation.doctor_id else None,
            'consultation_date': str(consultation.consultation_date) if consultation.consultation_date else None,
            'consultation_time': str(consultation.consultation_time) if consultation.consultation_time else None,
            'consultation_type': consultation.consultation_type,
            'state': consultation.state,
            'symptoms': consultation.symptoms,
            'diagnosis': consultation.diagnosis,
            'treatment': consultation.treatment,
            'prescription': consultation.prescription,
            'follow_up_date': str(consultation.follow_up_date) if consultation.follow_up_date else None,
            'notes': consultation.notes,
        }

    @http.route('/api/health/consultations/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_consultation(self, **data):
        try:
            consultation = request.env['health.consultation'].sudo().create(data)
            return {'id': consultation.id, 'message': 'Consultation created successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/health/consultations/<int:consultation_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_consultation(self, consultation_id, **data):
        consultation = request.env['health.consultation'].sudo().browse(consultation_id)
        if not consultation.exists():
            return {'error': 'Consultation not found'}
        try:
            consultation.write(data)
            return {'message': 'Consultation updated successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/health/consultations/<int:consultation_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_consultation(self, consultation_id):
        consultation = request.env['health.consultation'].sudo().browse(consultation_id)
        if not consultation.exists():
            return {'error': 'Consultation not found'}
        consultation.unlink()
        return {'message': 'Consultation deleted successfully'} 