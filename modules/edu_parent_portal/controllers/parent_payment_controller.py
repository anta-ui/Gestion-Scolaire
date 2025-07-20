# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class ParentPaymentController(http.Controller):

    @http.route('/api/payments', type='json', auth='user', methods=['POST'])
    def create_payment(self, **kw):
        """Créer une facture/paiement"""
        vals = kw.get('data', {})
        payment = request.env['edu.parent.payment'].sudo().create(vals)
        return {'success': True, 'payment_id': payment.id, 'state': payment.state}

    @http.route('/api/payments/<int:payment_id>/mark_paid', type='json', auth='user', methods=['POST'])
    def mark_payment_paid(self, payment_id):
        """Marquer manuellement un paiement comme payé"""
        payment = request.env['edu.parent.payment'].sudo().browse(payment_id)
        if not payment.exists():
            return {'success': False, 'error': 'Payment not found'}
        payment.action_mark_paid()
        return {'success': True, 'state': payment.state}

    @http.route('/api/payments/<int:payment_id>/reminder', type='json', auth='user', methods=['POST'])
    def send_payment_reminder(self, payment_id):
        """Envoyer un rappel pour un paiement"""
        payment = request.env['edu.parent.payment'].sudo().browse(payment_id)
        if not payment.exists():
            return {'success': False, 'error': 'Payment not found'}
        payment.action_send_reminder()
        return {'success': True, 'reminder_count': payment.reminder_count}

    @http.route('/api/payments/<int:payment_id>', type='json', auth='user', methods=['GET'])
    def get_payment_details(self, payment_id):
        """Détails d'un paiement"""
        payment = request.env['edu.parent.payment'].sudo().browse(payment_id)
        if not payment.exists():
            return {'success': False, 'error': 'Payment not found'}
        
        return {
            'success': True,
            'payment': {
                'id': payment.id,
                'reference': payment.name,
                'amount': payment.amount,
                'paid_amount': payment.paid_amount,
                'remaining_amount': payment.remaining_amount,
                'due_date': payment.due_date,
                'state': payment.state,
                'student': payment.student_id.name,
                'parent': payment.parent_id.name,
            }
        }

    @http.route('/api/payments/list', type='json', auth='user', methods=['POST'])
    def list_payments(self, **kw):
        """Lister les paiements pour l'utilisateur connecté"""
        parent_id = request.env.user.partner_id.id
        payments = request.env['edu.parent.payment'].sudo().search([
            ('parent_id', '=', parent_id)
        ], limit=kw.get('limit', 20))

        result = [{
            'id': payment.id,
            'reference': payment.name,
            'amount': payment.amount,
            'remaining_amount': payment.remaining_amount,
            'state': payment.state,
            'due_date': payment.due_date,
            'student': payment.student_id.name,
        } for payment in payments]

        return {'success': True, 'payments': result}

    @http.route('/api/payments/<int:payment_id>/transactions', type='json', auth='user', methods=['GET'])
    def payment_transactions(self, payment_id):
        """Lister les transactions d'un paiement"""
        payment = request.env['edu.parent.payment'].sudo().browse(payment_id)
        if not payment.exists():
            return {'success': False, 'error': 'Payment not found'}

        transactions = [{
            'id': t.id,
            'reference': t.reference,
            'amount': t.amount,
            'method': t.payment_method,
            'state': t.state,
            'transaction_date': t.transaction_date,
        } for t in payment.payment_ids]

        return {'success': True, 'transactions': transactions}

    @http.route('/api/payments/<int:payment_id>', type='json', auth='user', methods=['DELETE'])
    def delete_payment(self, payment_id):
        """Annuler/Supprimer un paiement"""
        payment = request.env['edu.parent.payment'].sudo().browse(payment_id)
        if not payment.exists():
            return {'success': False, 'error': 'Payment not found'}
        payment.action_cancel()
        return {'success': True, 'state': payment.state}
