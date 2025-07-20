# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
import json


class TransportBillingAPI(http.Controller):

    @http.route('/api/transport/billings', type='json', auth='user', methods=['GET'], csrf=False)
    def get_billings(self, **kwargs):
        billings = request.env['transport.billing'].sudo().search([])
        return [{
            'id': b.id,
            'name': b.name,
            'student_id': b.student_id.id,
            'student_name': b.student_id.name,
            'base_amount': b.base_amount,
            'discount_amount': b.discount_amount,
            'penalty_amount': b.penalty_amount,
            'total_amount': b.total_amount,
            'date': b.date.isoformat(),
            'state': b.state
        } for b in billings]

    @http.route('/api/transport/billings/<int:billing_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_billing(self, billing_id, **kwargs):
        billing = request.env['transport.billing'].sudo().browse(billing_id)
        if not billing.exists():
            return {'error': 'Billing record not found'}
        return {
            'id': billing.id,
            'name': billing.name,
            'student_id': billing.student_id.id,
            'student_name': billing.student_id.name,
            'base_amount': billing.base_amount,
            'discount_amount': billing.discount_amount,
            'penalty_amount': billing.penalty_amount,
            'total_amount': billing.total_amount,
            'date': billing.date.isoformat(),
            'state': billing.state
        }

    @http.route('/api/transport/billings', type='json', auth='user', methods=['POST'], csrf=False)
    def create_billing(self, **post):
        try:
            vals = {
                'student_id': post.get('student_id'),
                'base_amount': post.get('base_amount', 0.0),
                'discount_amount': post.get('discount_amount', 0.0),
                'penalty_amount': post.get('penalty_amount', 0.0),
                'period_start': post.get('period_start'),
                'period_end': post.get('period_end'),
                'date': post.get('date'),
                'description': post.get('description', ''),
                'notes': post.get('notes', ''),
            }
            billing = request.env['transport.billing'].sudo().create(vals)
            return {'id': billing.id, 'name': billing.name}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/transport/billings/<int:billing_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_billing(self, billing_id, **post):
        billing = request.env['transport.billing'].sudo().browse(billing_id)
        if not billing.exists():
            return {'error': 'Billing record not found'}

        try:
            billing.write(post)
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/transport/billings/<int:billing_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_billing(self, billing_id, **kwargs):
        billing = request.env['transport.billing'].sudo().browse(billing_id)
        if not billing.exists():
            return {'error': 'Billing record not found'}

        billing.unlink()
        return {'deleted': True}


class TransportDriverController(http.Controller):

    @http.route('/api/transport/drivers', type='json', auth='user', methods=['POST'], csrf=False)
    def get_drivers(self, **kwargs):
        drivers = request.env['transport.driver'].sudo().search([])
        return {
            'status': 'success',
            'data': [{
                'id': d.id,
                'name': d.name,
                'employee_id': d.employee_id.id if d.employee_id else None,
                'employee_name': d.employee_id.name if d.employee_id else None,
                'license_number': d.license_number,
                'license_type': d.license_type,
                'license_expiry': str(d.license_expiry) if d.license_expiry else None,
                'phone': d.phone,
                'email': d.email,
                'state': d.state,
                'vehicle_id': d.vehicle_id.id if d.vehicle_id else None,
                'vehicle_name': d.vehicle_id.name if d.vehicle_id else None,
                'route_id': d.route_id.id if d.route_id else None,
                'route_name': d.route_id.name if d.route_id else None,
                'experience_years': d.experience_years,
                'rating': d.rating,
            } for d in drivers]
        }

    @http.route('/api/transport/drivers/<int:driver_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_driver(self, driver_id):
        driver = request.env['transport.driver'].sudo().browse(driver_id)
        if not driver.exists():
            return {'error': 'Driver not found'}
        return {
            'id': driver.id,
            'name': driver.name,
            'employee_id': driver.employee_id.id if driver.employee_id else None,
            'employee_name': driver.employee_id.name if driver.employee_id else None,
            'license_number': driver.license_number,
            'license_type': driver.license_type,
            'license_expiry': str(driver.license_expiry) if driver.license_expiry else None,
            'phone': driver.phone,
            'email': driver.email,
            'state': driver.state,
            'vehicle_id': driver.vehicle_id.id if driver.vehicle_id else None,
            'vehicle_name': driver.vehicle_id.name if driver.vehicle_id else None,
            'route_id': driver.route_id.id if driver.route_id else None,
            'route_name': driver.route_id.name if driver.route_id else None,
            'experience_years': driver.experience_years,
            'rating': driver.rating,
            'address': driver.address,
            'emergency_contact': driver.emergency_contact,
            'medical_certificate': driver.medical_certificate,
            'background_check': driver.background_check,
        }

    @http.route('/api/transport/drivers/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_driver(self, **data):
        try:
            driver = request.env['transport.driver'].sudo().create(data)
            return {'id': driver.id, 'message': 'Driver created successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/transport/drivers/<int:driver_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_driver(self, driver_id, **data):
        driver = request.env['transport.driver'].sudo().browse(driver_id)
        if not driver.exists():
            return {'error': 'Driver not found'}
        try:
            driver.write(data)
            return {'message': 'Driver updated successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/transport/drivers/<int:driver_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_driver(self, driver_id):
        driver = request.env['transport.driver'].sudo().browse(driver_id)
        if not driver.exists():
            return {'error': 'Driver not found'}
        driver.unlink()
        return {'message': 'Driver deleted successfully'}
