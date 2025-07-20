# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class TransportBillingAPI(http.Controller):

    @http.route('/api/transport/billings', type='json', auth='user', methods=['GET'], csrf=False)
    def get_all_billings(self, **kwargs):
        billings = request.env['transport.billing'].sudo().search([])
        return [{
            'id': b.id,
            'name': b.name,
            'student': b.student_id.name,
            'base_amount': b.base_amount,
            'discount_amount': b.discount_amount,
            'penalty_amount': b.penalty_amount,
            'total_amount': b.total_amount,
            'state': b.state,
            'invoice_id': b.invoice_id.id if b.invoice_id else None
        } for b in billings]

    @http.route('/api/transport/billing/<int:billing_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_one_billing(self, billing_id, **kwargs):
        billing = request.env['transport.billing'].sudo().browse(billing_id)
        if not billing.exists():
            return {'error': 'Billing not found'}
        return {
            'id': billing.id,
            'name': billing.name,
            'student': billing.student_id.name,
            'base_amount': billing.base_amount,
            'discount_amount': billing.discount_amount,
            'penalty_amount': billing.penalty_amount,
            'total_amount': billing.total_amount,
            'state': billing.state,
            'invoice_id': billing.invoice_id.id if billing.invoice_id else None
        }

    @http.route('/api/transport/billing/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_billing(self, **data):
        required_fields = ['student_id', 'base_amount', 'period_start', 'period_end']
        for field in required_fields:
            if field not in data:
                return {'error': f'Missing field: {field}'}
        
        billing = request.env['transport.billing'].sudo().create({
            'student_id': data['student_id'],
            'subscription_id': data.get('subscription_id'),
            'date': data.get('date'),
            'period_start': data['period_start'],
            'period_end': data['period_end'],
            'base_amount': data['base_amount'],
            'discount_amount': data.get('discount_amount', 0.0),
            'penalty_amount': data.get('penalty_amount', 0.0),
            'description': data.get('description'),
            'notes': data.get('notes'),
        })
        return {'id': billing.id, 'message': 'Billing created'}

    @http.route('/api/transport/billing/<int:billing_id>/update', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_billing(self, billing_id, **data):
        billing = request.env['transport.billing'].sudo().browse(billing_id)
        if not billing.exists():
            return {'error': 'Billing not found'}
        billing.write(data)
        return {'id': billing.id, 'message': 'Billing updated'}

    @http.route('/api/transport/billing/<int:billing_id>/delete', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_billing(self, billing_id, **kwargs):
        billing = request.env['transport.billing'].sudo().browse(billing_id)
        if not billing.exists():
            return {'error': 'Billing not found'}
        billing.unlink()
        return {'message': f'Billing {billing_id} deleted'}
