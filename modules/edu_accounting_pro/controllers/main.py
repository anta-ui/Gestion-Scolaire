# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class AccountingMainController(http.Controller):

    @http.route('/api/accounting/dashboard', type='json', auth='user', methods=['POST'], csrf=False)
    def get_dashboard_data(self, **kwargs):
        """Récupérer les données du tableau de bord comptable"""
        try:
            # Statistiques des paiements
            total_payments = request.env['student.payment'].sudo().search_count([])
            pending_payments = request.env['student.payment'].sudo().search_count([('state', '=', 'pending')])
            completed_payments = request.env['student.payment'].sudo().search_count([('state', '=', 'completed')])
            
            # Statistiques des factures
            total_invoices = request.env['student.invoice'].sudo().search_count([])
            unpaid_invoices = request.env['student.invoice'].sudo().search_count([('state', '=', 'draft')])
            paid_invoices = request.env['student.invoice'].sudo().search_count([('state', '=', 'paid')])
            
            return {
                'status': 'success',
                'data': {
                    'payments': {
                        'total': total_payments,
                        'pending': pending_payments,
                        'completed': completed_payments
                    },
                    'invoices': {
                        'total': total_invoices,
                        'unpaid': unpaid_invoices,
                        'paid': paid_invoices
                    }
                }
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/api/accounting/invoices', type='json', auth='user', methods=['POST'], csrf=False)
    def get_invoices(self, **kwargs):
        invoices = request.env['student.invoice'].sudo().search([])
        return {
            'status': 'success',
            'data': [{
                'id': i.id,
                'name': i.name,
                'student_id': i.student_id.id if i.student_id else None,
                'student_name': i.student_id.name if i.student_id else None,
                'amount_total': i.amount_total,
                'amount_paid': i.amount_paid,
                'amount_due': i.amount_due,
                'invoice_date': str(i.invoice_date) if i.invoice_date else None,
                'due_date': str(i.due_date) if i.due_date else None,
                'state': i.state,
                'reference': i.reference,
            } for i in invoices]
        }

    @http.route('/api/accounting/invoices/<int:invoice_id>', type='json', auth='user', methods=['GET'], csrf=False)
    def get_invoice(self, invoice_id):
        invoice = request.env['student.invoice'].sudo().browse(invoice_id)
        if not invoice.exists():
            return {'error': 'Invoice not found'}
        return {
            'id': invoice.id,
            'name': invoice.name,
            'student_id': invoice.student_id.id if invoice.student_id else None,
            'student_name': invoice.student_id.name if invoice.student_id else None,
            'amount_total': invoice.amount_total,
            'amount_paid': invoice.amount_paid,
            'amount_due': invoice.amount_due,
            'invoice_date': str(invoice.invoice_date) if invoice.invoice_date else None,
            'due_date': str(invoice.due_date) if invoice.due_date else None,
            'state': invoice.state,
            'reference': invoice.reference,
            'description': invoice.description,
        }

    @http.route('/api/accounting/invoices/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_invoice(self, **data):
        try:
            invoice = request.env['student.invoice'].sudo().create(data)
            return {'id': invoice.id, 'message': 'Invoice created successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/accounting/invoices/<int:invoice_id>', type='json', auth='user', methods=['PUT'], csrf=False)
    def update_invoice(self, invoice_id, **data):
        invoice = request.env['student.invoice'].sudo().browse(invoice_id)
        if not invoice.exists():
            return {'error': 'Invoice not found'}
        try:
            invoice.write(data)
            return {'message': 'Invoice updated successfully'}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/accounting/invoices/<int:invoice_id>', type='json', auth='user', methods=['DELETE'], csrf=False)
    def delete_invoice(self, invoice_id):
        invoice = request.env['student.invoice'].sudo().browse(invoice_id)
        if not invoice.exists():
            return {'error': 'Invoice not found'}
        invoice.unlink()
        return {'message': 'Invoice deleted successfully'}
