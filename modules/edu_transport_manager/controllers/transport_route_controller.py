# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class TransportRouteController(http.Controller):

    @http.route('/api/transport/routes', type='json', auth='user', methods=['POST'], csrf=False)
    def get_routes(self, **kwargs):
        routes = request.env['transport.route'].sudo().search([])
        return {
            'status': 'success',
            'data': [{
                'id': r.id,
                'name': r.name,
                'code': r.code,
                'start_location': r.start_location,
                'end_location': r.end_location,
                'total_distance': r.total_distance,
                'estimated_duration': r.estimated_duration,
                'state': r.state,
                'base_fare': r.base_fare,
                'trip_count': r.trip_count,
                'student_count': r.student_count
            } for r in routes]
        }

    @http.route('/api/transport/routes/<int:route_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_route(self, route_id):
        route = request.env['transport.route'].sudo().browse(route_id)
        if not route.exists():
            return {'error': 'Route not found'}
        return {
            'id': route.id,
            'name': route.name,
            'code': route.code,
            'start_location': route.start_location,
            'end_location': route.end_location,
            'total_distance': route.total_distance,
            'estimated_duration': route.estimated_duration,
            'state': route.state,
            'base_fare': route.base_fare,
            'trip_count': route.trip_count,
            'student_count': route.student_count,
            'stops': [{
                'id': s.id,
                'name': s.name,
                'sequence': s.sequence,
                'arrival_time': s.arrival_time,
                'departure_time': s.departure_time,
                'latitude': s.latitude,
                'longitude': s.longitude,
                'address': s.address,
                'stop_duration': s.stop_duration,
                'student_count': s.student_count
            } for s in route.stop_ids]
        }

    @http.route('/api/transport/routes', type='json', auth='user', methods=['POST'], csrf=False)
    def create_route(self, **data):
        route = request.env['transport.route'].sudo().create(data)
        return {'id': route.id, 'message': 'Route created successfully'}

    @http.route('/api/transport/routes/<int:route_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_route(self, route_id, **data):
        route = request.env['transport.route'].sudo().browse(route_id)
        if not route.exists():
            return {'error': 'Route not found'}
        route.write(data)
        return {'message': 'Route updated successfully'}

    @http.route('/api/transport/routes/<int:route_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_route(self, route_id):
        route = request.env['transport.route'].sudo().browse(route_id)
        if not route.exists():
            return {'error': 'Route not found'}
        route.unlink()
        return {'message': 'Route deleted successfully'}
