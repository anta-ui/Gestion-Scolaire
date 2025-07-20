# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class TransportStudentAPI(http.Controller):

    # === Étudiants avec transport ===
    @http.route('/api/transport/students', type='json', auth='user', methods=['GET'], csrf=False)
    def get_transport_students(self):
        students = request.env['op.student'].sudo().search([('uses_transport', '=', True)])
        return [{
            'id': s.id,
            'name': s.name,
            'uses_transport': s.uses_transport,
            'transport_subscription_id': s.transport_subscription_id.id if s.transport_subscription_id else None,
            'pickup_stop_id': s.pickup_stop_id.name if s.pickup_stop_id else None,
            'dropoff_stop_id': s.dropoff_stop_id.name if s.dropoff_stop_id else None,
            'emergency_contact': s.emergency_contact_name,
            'total_trips': s.total_trips,
            'missed_trips': s.missed_trips
        } for s in students]

    # === Détails d'un étudiant transporté ===
    @http.route('/api/transport/students/<int:student_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_transport_student(self, student_id):
        student = request.env['op.student'].sudo().browse(student_id)
        if not student.exists() or not student.uses_transport:
            return {'error': 'Étudiant non trouvé ou n’utilise pas le transport'}
        
        return {
            'id': student.id,
            'name': student.name,
            'subscription': student.transport_subscription_id.name if student.transport_subscription_id else None,
            'pickup_stop': student.pickup_stop_id.name if student.pickup_stop_id else None,
            'dropoff_stop': student.dropoff_stop_id.name if student.dropoff_stop_id else None,
            'emergency_contact_name': student.emergency_contact_name,
            'emergency_contact_phone': student.emergency_contact_phone,
            'medical_conditions': student.medical_conditions,
            'total_trips': student.total_trips,
            'missed_trips': student.missed_trips
        }

    # === Présences transport ===
    @http.route('/api/transport/attendances', type='json', auth='user', methods=['GET'], csrf=False)
    def get_all_attendance(self):
        attendances = request.env['transport.student.attendance'].sudo().search([])
        return [{
            'id': a.id,
            'student_id': a.student_id.name,
            'trip_id': a.trip_id.name if a.trip_id else None,
            'stop_id': a.stop_id.name if a.stop_id else None,
            'status': a.status,
            'boarded': a.boarded,
            'alighted': a.alighted,
            'board_time': a.board_time,
            'alight_time': a.alight_time,
        } for a in attendances]
