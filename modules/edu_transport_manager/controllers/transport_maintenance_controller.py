# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class TransportMaintenanceAPI(http.Controller):

    @http.route('/api/transport/maintenance', auth='user', type='json', methods=['GET'], csrf=False)
    def list_maintenances(self, **kwargs):
        maints = request.env['transport.maintenance'].sudo().search([])
        return [
            {
                'id': m.id,
                'reference': m.name,
                'vehicle': m.vehicle_id.name,
                'type': m.maintenance_type,
                'state': m.state,
                'date': m.date,
                'total_cost': m.total_cost,
            } for m in maints
        ]

    @http.route('/api/transport/maintenance/<int:maintenance_id>', auth='user', type='json', methods=['GET'], csrf=False)
    def get_maintenance(self, maintenance_id):
        m = request.env['transport.maintenance'].sudo().browse(maintenance_id)
        if not m.exists():
            return {'error': 'Maintenance non trouvée'}
        return {
            'id': m.id,
            'reference': m.name,
            'vehicle_id': m.vehicle_id.id,
            'type': m.maintenance_type,
            'state': m.state,
            'description': m.description,
            'date': m.date,
            'duration': m.duration,
            'actual_date': m.actual_date,
            'actual_duration': m.actual_duration,
            'total_cost': m.total_cost
        }

    @http.route('/api/transport/maintenance', auth='user', type='json', methods=['POST'], csrf=False)
    def create_maintenance(self, **params):
        try:
            values = {
                'vehicle_id': params.get('vehicle_id'),
                'maintenance_type': params.get('maintenance_type', 'preventive'),
                'date': params.get('date'),
                'description': params.get('description', 'Maintenance auto via API'),
            }
            m = request.env['transport.maintenance'].sudo().create(values)
            return {'id': m.id, 'reference': m.name}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/transport/maintenance/<int:maintenance_id>', auth='user', type='json', methods=['PUT'], csrf=False)
    def update_maintenance(self, maintenance_id, **params):
        m = request.env['transport.maintenance'].sudo().browse(maintenance_id)
        if not m.exists():
            return {'error': 'Maintenance introuvable'}

        try:
            m.write(params)
            return {'success': True, 'id': m.id}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/transport/maintenance/<int:maintenance_id>', auth='user', type='json', methods=['DELETE'], csrf=False)
    def delete_maintenance(self, maintenance_id):
        m = request.env['transport.maintenance'].sudo().browse(maintenance_id)
        if not m.exists():
            return {'error': 'Maintenance introuvable'}
        m.unlink()
        return {'success': True}
