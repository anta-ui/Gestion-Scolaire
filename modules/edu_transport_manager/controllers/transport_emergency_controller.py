# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class TransportEmergencyAPI(http.Controller):

    @http.route('/api/transport/emergencies', type='json', auth='user', methods=['GET'], csrf=False)
    def get_emergencies(self, **kwargs):
        emergencies = request.env['transport.emergency'].sudo().search([])
        return [{
            'id': e.id,
            'name': e.name,
            'type': e.emergency_type,
            'severity': e.severity,
            'description': e.description,
            'location': e.location,
            'date_reported': e.reported_date,
            'state': e.state,
            'vehicle': e.vehicle_id.name if e.vehicle_id else None,
            'driver': e.driver_id.name if e.driver_id else None,
            'students': [s.name for s in e.student_ids],
        } for e in emergencies]

    @http.route('/api/transport/emergency/<int:emergency_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_emergency_by_id(self, emergency_id, **kwargs):
        emergency = request.env['transport.emergency'].sudo().browse(emergency_id)
        if not emergency.exists():
            return {'error': 'Emergency not found'}
        return {
            'id': emergency.id,
            'name': emergency.name,
            'type': emergency.emergency_type,
            'severity': emergency.severity,
            'description': emergency.description,
            'location': emergency.location,
            'latitude': emergency.latitude,
            'longitude': emergency.longitude,
            'state': emergency.state,
            'vehicle': emergency.vehicle_id.name if emergency.vehicle_id else None,
            'driver': emergency.driver_id.name if emergency.driver_id else None,
            'students': [s.name for s in emergency.student_ids],
        }

    @http.route('/api/transport/emergency', type='json', auth='user', methods=['POST'], csrf=False)
    def create_emergency(self, **kwargs):
        required_fields = ['emergency_type', 'severity', 'description']
        missing = [f for f in required_fields if f not in kwargs]
        if missing:
            return {'error': f'Missing fields: {", ".join(missing)}'}

        emergency = request.env['transport.emergency'].sudo().create({
            'emergency_type': kwargs['emergency_type'],
            'severity': kwargs['severity'],
            'description': kwargs['description'],
            'location': kwargs.get('location'),
            'vehicle_id': kwargs.get('vehicle_id'),
            'driver_id': kwargs.get('driver_id'),
            'trip_id': kwargs.get('trip_id'),
            'student_ids': [(6, 0, kwargs.get('student_ids', []))],
        })
        return {'success': True, 'emergency_id': emergency.id}

    @http.route('/api/transport/emergency/<int:emergency_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_emergency(self, emergency_id, **kwargs):
        emergency = request.env['transport.emergency'].sudo().browse(emergency_id)
        if not emergency.exists():
            return {'error': 'Emergency not found'}

        emergency.write(kwargs)
        return {'success': True}

    @http.route('/api/transport/emergency/<int:emergency_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_emergency(self, emergency_id, **kwargs):
        emergency = request.env['transport.emergency'].sudo().browse(emergency_id)
        if not emergency.exists():
            return {'error': 'Emergency not found'}
        emergency.unlink()
        return {'success': True}
