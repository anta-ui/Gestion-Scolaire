# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduStudentInvoiceController(http.Controller):
    """Controller pour la gestion des factures étudiants"""

    @http.route('/api/student-invoices', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_invoices(self, **kwargs):
        """Récupère la liste des factures étudiants"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', kwargs['student_id']))
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            if kwargs.get('course_id'):
                domain.append(('course_id', '=', kwargs['course_id']))
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            if kwargs.get('payment_state'):
                domain.append(('payment_state', '=', kwargs['payment_state']))
            
            # Filtres par date
            if kwargs.get('date_from'):
                domain.append(('invoice_date', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('invoice_date', '<=', kwargs['date_to']))
            
            # Pagination
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            invoices = request.env['edu.student.invoice'].search(domain, limit=limit, offset=offset)
            
            result = []
            for invoice in invoices:
                result.append({
                    'id': invoice.id,
                    'number': invoice.number,
                    'reference': invoice.reference or '',
                    'student_id': invoice.student_id.id if invoice.student_id else None,
                    'student_name': invoice.student_id.name if invoice.student_id else '',
                    'student_registration_number': invoice.student_id.registration_number if invoice.student_id else '',
                    'partner_id': invoice.partner_id.id if invoice.partner_id else None,
                    'partner_name': invoice.partner_id.name if invoice.partner_id else '',
                    'academic_year_id': invoice.academic_year_id.id if invoice.academic_year_id else None,
                    'academic_year_name': invoice.academic_year_id.name if invoice.academic_year_id else '',
                    'course_id': invoice.course_id.id if invoice.course_id else None,
                    'course_name': invoice.course_id.name if invoice.course_id else '',
                    'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                    'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                    'amount_total': invoice.amount_total,
                    'amount_paid': invoice.amount_paid,
                    'amount_residual': invoice.amount_residual,
                    'state': invoice.state,
                    'payment_state': invoice.payment_state,
                    'currency_symbol': invoice.currency_id.symbol if invoice.currency_id else '',
                    'is_overdue': invoice.is_overdue,
                })
            
            total_count = request.env['edu.student.invoice'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des factures: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-invoices/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_invoice(self, **kwargs):
        """Récupère une facture étudiant spécifique"""
        try:
            invoice_id = kwargs.get('invoice_id')
            if not invoice_id:
                return {'success': False, 'error': 'ID de facture requis'}
            
            invoice = request.env['edu.student.invoice'].browse(invoice_id)
            
            if not invoice.exists():
                return {'success': False, 'error': 'Facture non trouvée'}
            
            # Récupération des lignes de facture
            invoice_lines = []
            for line in invoice.invoice_line_ids:
                invoice_lines.append({
                    'id': line.id,
                    'sequence': line.sequence,
                    'product_id': line.product_id.id if line.product_id else None,
                    'product_name': line.product_id.name if line.product_id else '',
                    'description': line.description or '',
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'price_subtotal': line.price_subtotal,
                    'price_tax': line.price_tax,
                    'price_total': line.price_total,
                    'fee_type_id': line.fee_type_id.id if line.fee_type_id else None,
                    'fee_type_name': line.fee_type_id.name if line.fee_type_id else '',
                    'academic_period': line.academic_period or '',
                    'tax_ids': line.tax_ids.ids,
                })
            
            # Récupération des paiements
            payments = []
            for payment in invoice.payment_ids:
                payments.append({
                    'id': payment.id,
                    'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                    'amount': payment.amount,
                    'payment_method': payment.payment_method,
                    'reference': payment.reference or '',
                    'state': payment.state,
                })
            
            data = {
                'id': invoice.id,
                'number': invoice.number,
                'reference': invoice.reference or '',
                'student_id': invoice.student_id.id if invoice.student_id else None,
                'student_name': invoice.student_id.name if invoice.student_id else '',
                'student_email': invoice.student_id.email if invoice.student_id else '',
                'student_phone': invoice.student_id.phone if invoice.student_id else '',
                'partner_id': invoice.partner_id.id if invoice.partner_id else None,
                'partner_name': invoice.partner_id.name if invoice.partner_id else '',
                'academic_year_id': invoice.academic_year_id.id if invoice.academic_year_id else None,
                'academic_year_name': invoice.academic_year_id.name if invoice.academic_year_id else '',
                'course_id': invoice.course_id.id if invoice.course_id else None,
                'course_name': invoice.course_id.name if invoice.course_id else '',
                'batch_id': invoice.batch_id.id if invoice.batch_id else None,
                'batch_name': invoice.batch_id.name if invoice.batch_id else '',
                'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
                'period_start': invoice.period_start.isoformat() if invoice.period_start else None,
                'period_end': invoice.period_end.isoformat() if invoice.period_end else None,
                'amount_untaxed': invoice.amount_untaxed,
                'amount_tax': invoice.amount_tax,
                'amount_total': invoice.amount_total,
                'amount_paid': invoice.amount_paid,
                'amount_residual': invoice.amount_residual,
                'state': invoice.state,
                'payment_state': invoice.payment_state,
                'currency_id': invoice.currency_id.id if invoice.currency_id else None,
                'currency_symbol': invoice.currency_id.symbol if invoice.currency_id else '',
                'is_overdue': invoice.is_overdue,
                'invoice_type': invoice.invoice_type,
                'late_fee_applied': invoice.late_fee_applied,
                'notes': invoice.notes or '',
                'narration': invoice.narration or '',
                'invoice_lines': invoice_lines,
                'payments': payments,
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la facture: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-invoices/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_student_invoice(self, **kwargs):
        """Crée une nouvelle facture étudiant"""
        try:
            # Validation des champs requis
            required_fields = ['student_id', 'academic_year_id', 'invoice_date', 'due_date']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Champ requis manquant: {field}'}
            
            # Préparation des données
            vals = {
                'student_id': kwargs['student_id'],
                'academic_year_id': kwargs['academic_year_id'],
                'invoice_date': kwargs['invoice_date'],
                'due_date': kwargs['due_date'],
            }
            
            # Champs optionnels
            optional_fields = [
                'reference', 'course_id', 'batch_id', 'period_start', 'period_end',
                'currency_id', 'invoice_type', 'notes', 'narration'
            ]
            
            for field in optional_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Création de la facture
            invoice = request.env['edu.student.invoice'].create(vals)
            
            # Création des lignes de facture si fournies
            if kwargs.get('invoice_lines'):
                for line_data in kwargs['invoice_lines']:
                    line_vals = {
                        'invoice_id': invoice.id,
                        'description': line_data.get('description', ''),
                        'quantity': line_data.get('quantity', 1.0),
                        'price_unit': line_data.get('price_unit', 0.0),
                        'sequence': line_data.get('sequence', 10),
                    }
                    
                    # Champs optionnels des lignes
                    if line_data.get('product_id'):
                        line_vals['product_id'] = line_data['product_id']
                    if line_data.get('fee_type_id'):
                        line_vals['fee_type_id'] = line_data['fee_type_id']
                    if line_data.get('academic_period'):
                        line_vals['academic_period'] = line_data['academic_period']
                    if line_data.get('tax_ids'):
                        line_vals['tax_ids'] = [(6, 0, line_data['tax_ids'])]
                    
                    request.env['edu.student.invoice.line'].create(line_vals)
            
            return {
                'success': True,
                'data': {
                    'id': invoice.id,
                    'number': invoice.number,
                    'amount_total': invoice.amount_total
                },
                'message': 'Facture créée avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la facture: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-invoices/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_student_invoice(self, **kwargs):
        """Met à jour une facture étudiant"""
        try:
            invoice_id = kwargs.get('invoice_id')
            if not invoice_id:
                return {'success': False, 'error': 'ID de facture requis'}
            
            invoice = request.env['edu.student.invoice'].browse(invoice_id)
            
            if not invoice.exists():
                return {'success': False, 'error': 'Facture non trouvée'}
            
            # Vérification de l'état
            if invoice.state not in ['draft']:
                return {'success': False, 'error': 'Seules les factures en brouillon peuvent être modifiées'}
            
            # Préparation des données à mettre à jour
            vals = {}
            updatable_fields = [
                'reference', 'student_id', 'academic_year_id', 'course_id', 'batch_id',
                'invoice_date', 'due_date', 'period_start', 'period_end',
                'invoice_type', 'notes', 'narration'
            ]
            
            for field in updatable_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Mise à jour
            invoice.write(vals)
            
            return {
                'success': True,
                'message': 'Facture mise à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-invoices/confirm', type='json', auth='user', methods=['POST'], csrf=False)
    def confirm_invoice(self, **kwargs):
        """Confirme une facture"""
        try:
            invoice_id = kwargs.get('invoice_id')
            if not invoice_id:
                return {'success': False, 'error': 'ID de facture requis'}
            
            invoice = request.env['edu.student.invoice'].browse(invoice_id)
            
            if not invoice.exists():
                return {'success': False, 'error': 'Facture non trouvée'}
            
            if invoice.state != 'draft':
                return {'success': False, 'error': 'Seules les factures en brouillon peuvent être confirmées'}
            
            invoice.action_confirm()
            
            return {
                'success': True,
                'message': f'Facture {invoice.number} confirmée avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la confirmation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-invoices/cancel', type='json', auth='user', methods=['POST'], csrf=False)
    def cancel_invoice(self, **kwargs):
        """Annule une facture"""
        try:
            invoice_id = kwargs.get('invoice_id')
            if not invoice_id:
                return {'success': False, 'error': 'ID de facture requis'}
            
            invoice = request.env['edu.student.invoice'].browse(invoice_id)
            
            if not invoice.exists():
                return {'success': False, 'error': 'Facture non trouvée'}
            
            if invoice.state == 'paid':
                return {'success': False, 'error': 'Une facture payée ne peut pas être annulée'}
            
            invoice.action_cancel()
            
            return {
                'success': True,
                'message': f'Facture {invoice.number} annulée avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'annulation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-invoices/register-payment', type='json', auth='user', methods=['POST'], csrf=False)
    def register_payment(self, **kwargs):
        """Enregistre un paiement pour une facture"""
        try:
            invoice_id = kwargs.get('invoice_id')
            if not invoice_id:
                return {'success': False, 'error': 'ID de facture requis'}
            
            invoice = request.env['edu.student.invoice'].browse(invoice_id)
            
            if not invoice.exists():
                return {'success': False, 'error': 'Facture non trouvée'}
            
            # Appel de la méthode d'enregistrement de paiement
            result = invoice.action_register_payment()
            
            return {
                'success': True,
                'message': 'Action de paiement lancée',
                'action': result
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'enregistrement du paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-invoices/send', type='json', auth='user', methods=['POST'], csrf=False)
    def send_invoice(self, **kwargs):
        """Envoie une facture par email"""
        try:
            invoice_id = kwargs.get('invoice_id')
            if not invoice_id:
                return {'success': False, 'error': 'ID de facture requis'}
            
            invoice = request.env['edu.student.invoice'].browse(invoice_id)
            
            if not invoice.exists():
                return {'success': False, 'error': 'Facture non trouvée'}
            
            invoice.action_send_invoice()
            
            return {
                'success': True,
                'message': f'Facture {invoice.number} envoyée par email'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
