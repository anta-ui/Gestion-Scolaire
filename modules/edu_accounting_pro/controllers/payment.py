# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class PaymentController(http.Controller):

    @http.route('/api/accounting/payments', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payments(self, **kwargs):
        payments = request.env['student.payment'].sudo().search([])
        return {
            'status': 'success',
            'data': [{
                'id': p.id,
                'name': p.name,
                'student_id': p.student_id.id if p.student_id else None,
                'student_name': p.student_id.name if p.student_id else None,
                'amount': p.amount,
                'payment_date': str(p.payment_date) if p.payment_date else None,
                'payment_method': p.payment_method,
                'state': p.state,
                'reference': p.reference,
                'description': p.description,
            } for p in payments]
        }

    @http.route('/api/accounting/payments/<int:payment_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_payment(self, payment_id):
        payment = request.env['student.payment'].sudo().browse(payment_id)
        if not payment.exists():
            return {'error': 'Payment not found'}
        return {
            'id': payment.id,
            'name': payment.name,
            'student_id': payment.student_id.id if payment.student_id else None,
            'student_name': payment.student_id.name if payment.student_id else None,
            'amount': payment.amount,
            'payment_date': str(payment.payment_date) if payment.payment_date else None,
            'payment_method': payment.payment_method,
            'state': payment.state,
            'reference': payment.reference,
            'description': payment.description,
        }

    @http.route('/api/accounting/payments/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_payment(self, **data):
        try:
            payment = request.env['student.payment'].sudo().create(data)
            return {'id': payment.id, 'message': 'Payment created successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/accounting/payments/<int:payment_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_payment(self, payment_id, **data):
        payment = request.env['student.payment'].sudo().browse(payment_id)
        if not payment.exists():
            return {'error': 'Payment not found'}
        try:
            payment.write(data)
            return {'message': 'Payment updated successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/accounting/payments/<int:payment_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_payment(self, payment_id):
        payment = request.env['student.payment'].sudo().browse(payment_id)
        if not payment.exists():
            return {'error': 'Payment not found'}
        payment.unlink()
        return {'message': 'Payment deleted successfully'}
