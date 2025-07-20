# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class TransportVehicleController(http.Controller):

    @http.route('/api/transport/vehicles', type='json', auth='user', methods=['POST'], csrf=False)
    def get_vehicles(self, **kwargs):
        vehicles = request.env['transport.vehicle'].sudo().search([])
        return {
            'status': 'success',
            'data': [{
                'id': v.id,
                'name': v.name,
                'license_plate': v.license_plate,
                'vehicle_type': v.vehicle_type,
                'capacity': v.capacity,
                'state': v.state,
                'driver_id': v.driver_id.id if v.driver_id else None,
                'driver_name': v.driver_id.name if v.driver_id else None,
                'route_id': v.route_id.id if v.route_id else None,
                'route_name': v.route_id.name if v.route_id else None,
                'last_maintenance': str(v.last_maintenance) if v.last_maintenance else None,
                'next_maintenance': str(v.next_maintenance) if v.next_maintenance else None,
                'fuel_level': v.fuel_level,
                'mileage': v.mileage,
            } for v in vehicles]
        }

    @http.route('/api/transport/vehicles/active', type='json', auth='user', methods=['POST'], csrf=False)
    def get_active_vehicles(self, **kwargs):
        vehicles = request.env['transport.vehicle'].sudo().search([('state', '=', 'active')])
        return {
            'status': 'success',
            'data': [{
                'id': v.id,
                'name': v.name,
                'license_plate': v.license_plate,
                'vehicle_type': v.vehicle_type,
                'capacity': v.capacity,
                'driver_id': v.driver_id.id if v.driver_id else None,
                'driver_name': v.driver_id.name if v.driver_id else None,
                'route_id': v.route_id.id if v.route_id else None,
                'route_name': v.route_id.name if v.route_id else None,
            } for v in vehicles]
        }

    @http.route('/api/transport/vehicles/<int:vehicle_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_vehicle(self, vehicle_id):
        vehicle = request.env['transport.vehicle'].sudo().browse(vehicle_id)
        if not vehicle.exists():
            return {'error': 'Vehicle not found'}
        return {
            'id': vehicle.id,
            'name': vehicle.name,
            'license_plate': vehicle.license_plate,
            'vehicle_type': vehicle.vehicle_type,
            'capacity': vehicle.capacity,
            'state': vehicle.state,
            'driver_id': vehicle.driver_id.id if vehicle.driver_id else None,
            'driver_name': vehicle.driver_id.name if vehicle.driver_id else None,
            'route_id': vehicle.route_id.id if vehicle.route_id else None,
            'route_name': vehicle.route_id.name if vehicle.route_id else None,
            'last_maintenance': str(vehicle.last_maintenance) if vehicle.last_maintenance else None,
            'next_maintenance': str(vehicle.next_maintenance) if vehicle.next_maintenance else None,
            'fuel_level': vehicle.fuel_level,
            'mileage': vehicle.mileage,
            'description': vehicle.description,
        }

    @http.route('/api/transport/vehicles/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_vehicle(self, **data):
        try:
            vehicle = request.env['transport.vehicle'].sudo().create(data)
            return {'id': vehicle.id, 'message': 'Vehicle created successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/transport/vehicles/<int:vehicle_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_vehicle(self, vehicle_id, **data):
        vehicle = request.env['transport.vehicle'].sudo().browse(vehicle_id)
        if not vehicle.exists():
            return {'error': 'Vehicle not found'}
        try:
            vehicle.write(data)
            return {'message': 'Vehicle updated successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/transport/vehicles/<int:vehicle_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_vehicle(self, vehicle_id):
        vehicle = request.env['transport.vehicle'].sudo().browse(vehicle_id)
        if not vehicle.exists():
            return {'error': 'Vehicle not found'}
        vehicle.unlink()
        return {'message': 'Vehicle deleted successfully'}
