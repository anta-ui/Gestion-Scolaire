# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class TransportTripController(http.Controller):

    @http.route('/api/transport/trips', type='json', auth='user', methods=['POST'], csrf=False)
    def get_trips(self, **kwargs):
        trips = request.env['transport.trip'].sudo().search([])
        return {
            'status': 'success',
            'data': [{
                'id': t.id,
                'name': t.name,
                'route_id': t.route_id.id if t.route_id else None,
                'route_name': t.route_id.name if t.route_id else None,
                'vehicle_id': t.vehicle_id.id if t.vehicle_id else None,
                'vehicle_name': t.vehicle_id.name if t.vehicle_id else None,
                'driver_id': t.driver_id.id if t.driver_id else None,
                'driver_name': t.driver_id.name if t.driver_id else None,
                'scheduled_departure': str(t.scheduled_departure) if t.scheduled_departure else None,
                'scheduled_arrival': str(t.scheduled_arrival) if t.scheduled_arrival else None,
                'actual_departure': str(t.actual_departure) if t.actual_departure else None,
                'actual_arrival': str(t.actual_arrival) if t.actual_arrival else None,
                'state': t.state,
                'student_count': t.student_count,
                'passenger_count': t.passenger_count,
            } for t in trips]
        }

    @http.route('/api/transport/trips/<int:trip_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_trip(self, trip_id):
        trip = request.env['transport.trip'].sudo().browse(trip_id)
        if not trip.exists():
            return {'error': 'Trip not found'}
        return {
            'id': trip.id,
            'name': trip.name,
            'route_id': trip.route_id.id if trip.route_id else None,
            'route_name': trip.route_id.name if trip.route_id else None,
            'vehicle_id': trip.vehicle_id.id if trip.vehicle_id else None,
            'vehicle_name': trip.vehicle_id.name if trip.vehicle_id else None,
            'driver_id': trip.driver_id.id if trip.driver_id else None,
            'driver_name': trip.driver_id.name if trip.driver_id else None,
            'scheduled_departure': str(trip.scheduled_departure) if trip.scheduled_departure else None,
            'scheduled_arrival': str(trip.scheduled_arrival) if trip.scheduled_arrival else None,
            'actual_departure': str(trip.actual_departure) if trip.actual_departure else None,
            'actual_arrival': str(trip.actual_arrival) if trip.actual_arrival else None,
            'state': trip.state,
            'student_count': trip.student_count,
            'passenger_count': trip.passenger_count,
            'notes': trip.notes,
        }

    @http.route('/api/transport/trips/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_trip(self, **data):
        try:
            trip = request.env['transport.trip'].sudo().create(data)
            return {'id': trip.id, 'message': 'Trip created successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/transport/trips/<int:trip_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_trip(self, trip_id, **data):
        trip = request.env['transport.trip'].sudo().browse(trip_id)
        if not trip.exists():
            return {'error': 'Trip not found'}
        try:
            trip.write(data)
            return {'message': 'Trip updated successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/transport/trips/<int:trip_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_trip(self, trip_id):
        trip = request.env['transport.trip'].sudo().browse(trip_id)
        if not trip.exists():
            return {'error': 'Trip not found'}
        trip.unlink()
        return {'message': 'Trip deleted successfully'}
