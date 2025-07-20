# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class ParentAppointmentController(http.Controller):

    @http.route('/api/appointments', type='json', auth='user', methods=['POST'])
    def create_appointment(self, **kw):
        """Créer un rendez-vous parent-enseignant"""
        vals = kw.get('data', {})
        appointment = request.env['edu.parent.appointment'].sudo().create(vals)
        return {
            'success': True,
            'id': appointment.id,
            'name': appointment.name
        }

    @http.route('/api/appointments/<int:appointment_id>', type='json', auth='user', methods=['GET'])
    def get_appointment(self, appointment_id):
        """Récupérer les détails d'un rendez-vous spécifique"""
        appointment = request.env['edu.parent.appointment'].sudo().browse(appointment_id)
        if not appointment.exists():
            return {'success': False, 'error': 'Appointment not found'}

        return {
            'success': True,
            'appointment': {
                'id': appointment.id,
                'name': appointment.name,
                'parent': appointment.parent_id.name,
                'teacher': appointment.teacher_id.name,
                'student': appointment.student_id.name,
                'date': appointment.appointment_date,
                'duration': appointment.duration,
                'subject': appointment.subject,
                'location': appointment.location,
                'meeting_type': appointment.meeting_type,
                'state': appointment.state,
                'priority': appointment.priority
            }
        }

    @http.route('/api/appointments/<int:appointment_id>', type='json', auth='user', methods=['PUT'])
    def update_appointment(self, appointment_id, **kw):
        """Mettre à jour un rendez-vous existant"""
        vals = kw.get('data', {})
        appointment = request.env['edu.parent.appointment'].sudo().browse(appointment_id)
        if not appointment.exists():
            return {'success': False, 'error': 'Appointment not found'}

        appointment.write(vals)
        return {'success': True}

    @http.route('/api/appointments/<int:appointment_id>', type='json', auth='user', methods=['DELETE'])
    def delete_appointment(self, appointment_id):
        """Supprimer un rendez-vous"""
        appointment = request.env['edu.parent.appointment'].sudo().browse(appointment_id)
        if not appointment.exists():
            return {'success': False, 'error': 'Appointment not found'}

        appointment.unlink()
        return {'success': True}

    @http.route('/api/appointments/list', type='json', auth='user', methods=['POST'])
    def list_appointments(self, **kw):
        """Lister les rendez-vous avec filtres optionnels"""
        domain = kw.get('domain', [])
        appointments = request.env['edu.parent.appointment'].sudo().search(domain)
        result = [{
            'id': a.id,
            'name': a.name,
            'date': a.appointment_date,
            'state': a.state,
            'parent': a.parent_id.name,
            'teacher': a.teacher_id.name,
            'student': a.student_id.name,
        } for a in appointments]

        return {
            'success': True,
            'appointments': result
        }
