# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class VaccinationTrackingController(http.Controller):

    @http.route('/api/health/vaccinations', type='json', auth='user', methods=['POST'], csrf=False)
    def get_vaccinations(self, **kwargs):
        vaccinations = request.env['health.vaccination'].sudo().search([])
        return {
            'status': 'success',
            'data': [{
                'id': v.id,
                'name': v.name,
                'student_id': v.student_id.id if v.student_id else None,
                'student_name': v.student_id.name if v.student_id else None,
                'vaccine_type': v.vaccine_type,
                'vaccination_date': str(v.vaccination_date) if v.vaccination_date else None,
                'next_dose_date': str(v.next_dose_date) if v.next_dose_date else None,
                'dose_number': v.dose_number,
                'total_doses': v.total_doses,
                'state': v.state,
                'administered_by': v.administered_by.name if v.administered_by else None,
                'batch_number': v.batch_number,
                'expiry_date': str(v.expiry_date) if v.expiry_date else None,
            } for v in vaccinations]
        }

    @http.route('/api/health/vaccinations/due', type='json', auth='user', methods=['POST'], csrf=False)
    def get_due_vaccinations(self, **kwargs):
        from datetime import date, timedelta
        today = date.today()
        next_week = today + timedelta(days=7)
        
        due_vaccinations = request.env['health.vaccination'].sudo().search([
            ('next_dose_date', '>=', today),
            ('next_dose_date', '<=', next_week),
            ('state', '!=', 'completed')
        ])
        
        return {
            'status': 'success',
            'data': [{
                'id': v.id,
                'name': v.name,
                'student_id': v.student_id.id if v.student_id else None,
                'student_name': v.student_id.name if v.student_id else None,
                'vaccine_type': v.vaccine_type,
                'next_dose_date': str(v.next_dose_date) if v.next_dose_date else None,
                'dose_number': v.dose_number,
                'total_doses': v.total_doses,
                'days_until_due': (v.next_dose_date - today).days if v.next_dose_date else None,
            } for v in due_vaccinations]
        }

    @http.route('/api/health/vaccinations/<int:vaccination_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_vaccination(self, vaccination_id):
        vaccination = request.env['health.vaccination'].sudo().browse(vaccination_id)
        if not vaccination.exists():
            return {'error': 'Vaccination not found'}
        return {
            'id': vaccination.id,
            'name': vaccination.name,
            'student_id': vaccination.student_id.id if vaccination.student_id else None,
            'student_name': vaccination.student_id.name if vaccination.student_id else None,
            'vaccine_type': vaccination.vaccine_type,
            'vaccination_date': str(vaccination.vaccination_date) if vaccination.vaccination_date else None,
            'next_dose_date': str(vaccination.next_dose_date) if vaccination.next_dose_date else None,
            'dose_number': vaccination.dose_number,
            'total_doses': vaccination.total_doses,
            'state': vaccination.state,
            'administered_by': vaccination.administered_by.name if vaccination.administered_by else None,
            'batch_number': vaccination.batch_number,
            'expiry_date': str(vaccination.expiry_date) if vaccination.expiry_date else None,
            'notes': vaccination.notes,
        }

    @http.route('/api/health/vaccinations/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_vaccination(self, **data):
        try:
            vaccination = request.env['health.vaccination'].sudo().create(data)
            return {'id': vaccination.id, 'message': 'Vaccination created successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/health/vaccinations/<int:vaccination_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_vaccination(self, vaccination_id, **data):
        vaccination = request.env['health.vaccination'].sudo().browse(vaccination_id)
        if not vaccination.exists():
            return {'error': 'Vaccination not found'}
        try:
            vaccination.write(data)
            return {'message': 'Vaccination updated successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/health/vaccinations/<int:vaccination_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_vaccination(self, vaccination_id):
        vaccination = request.env['health.vaccination'].sudo().browse(vaccination_id)
        if not vaccination.exists():
            return {'error': 'Vaccination not found'}
        vaccination.unlink()
        return {'message': 'Vaccination deleted successfully'}
