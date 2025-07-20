# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class TransportTrackingController(http.Controller):

    @http.route('/api/tracking/update_position', type='json', auth='user', methods=['POST'], csrf=False)
    def update_position(self, **kwargs):
        """
        Body attendu (JSON):
        {
            "tracking_id": 5,
            "latitude": 36.12345,
            "longitude": 10.12345,
            "speed": 45,
            "heading": 90
        }
        """
        tracking = request.env['transport.tracking'].sudo().browse(int(kwargs.get('tracking_id')))
        if not tracking.exists():
            return {'error': 'Suivi non trouvé'}

        tracking.update_position(
            latitude=kwargs.get('latitude'),
            longitude=kwargs.get('longitude'),
            speed=kwargs.get('speed', 0),
            heading=kwargs.get('heading', 0)
        )

        return {'success': True, 'message': 'Position mise à jour'}

    @http.route('/api/tracking/current_position/<int:tracking_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_current_position(self, tracking_id, **kwargs):
        tracking = request.env['transport.tracking'].sudo().browse(tracking_id)
        if not tracking.exists():
            return {'error': 'Suivi non trouvé'}

        return {
            'vehicle_id': tracking.vehicle_id.id,
            'trip_id': tracking.trip_id.id if tracking.trip_id else None,
            'latitude': tracking.current_latitude,
            'longitude': tracking.current_longitude,
            'speed': tracking.current_speed,
            'heading': tracking.current_heading,
            'last_update': tracking.last_update,
        }

    @http.route('/api/tracking/alerts/<int:tracking_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_alerts(self, tracking_id, **kwargs):
        alerts = request.env['transport.tracking.alert'].sudo().search([('tracking_id', '=', tracking_id)], limit=50)
        return [{
            'alert_type': alert.alert_type,
            'message': alert.message,
            'latitude': alert.latitude,
            'longitude': alert.longitude,
            'timestamp': alert.timestamp,
            'severity': alert.severity,
            'state': alert.state,
        } for alert in alerts]

    @http.route('/api/tracking/positions/<int:tracking_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_position_history(self, tracking_id, **kwargs):
        history = request.env['transport.position.history'].sudo().search(
            [('tracking_id', '=', tracking_id)], order='timestamp desc', limit=100
        )
        return [{
            'latitude': pos.latitude,
            'longitude': pos.longitude,
            'speed': pos.speed,
            'heading': pos.heading,
            'timestamp': pos.timestamp,
        } for pos in history]
