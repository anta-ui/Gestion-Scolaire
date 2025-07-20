# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduStudentPaymentController(http.Controller):
    """Controller pour la gestion des paiements étudiants"""

    @http.route('/api/student-payments', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_payments(self, **kwargs):
        """Récupère la liste des paiements étudiants"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', kwargs['student_id']))
            if kwargs.get('invoice_id'):
                domain.append(('invoice_id', '=', kwargs['invoice_id']))
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            if kwargs.get('payment_method'):
                domain.append(('payment_method', '=', kwargs['payment_method']))
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            
            # Filtres par date
            if kwargs.get('date_from'):
                domain.append(('payment_date', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('payment_date', '<=', kwargs['date_to']))
            
            # Pagination
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            payments = request.env['edu.student.payment'].search(domain, limit=limit, offset=offset)
            
            result = []
            for payment in payments:
                result.append({
                    'id': payment.id,
                    'reference': payment.reference or '',
                    'student_id': payment.student_id.id if payment.student_id else None,
                    'student_name': payment.student_id.name if payment.student_id else '',
                    'student_registration_number': payment.student_id.registration_number if payment.student_id else '',
                    'invoice_id': payment.invoice_id.id if payment.invoice_id else None,
                    'invoice_number': payment.invoice_id.number if payment.invoice_id else '',
                    'academic_year_id': payment.academic_year_id.id if payment.academic_year_id else None,
                    'academic_year_name': payment.academic_year_id.name if payment.academic_year_id else '',
                    'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                    'amount': payment.amount,
                    'payment_method': payment.payment_method,
                    'payment_method_display': dict(payment._fields['payment_method'].selection).get(payment.payment_method, ''),
                    'state': payment.state,
                    'state_display': dict(payment._fields['state'].selection).get(payment.state, ''),
                    'currency_symbol': payment.currency_id.symbol if payment.currency_id else '',
                    'bank_reference': payment.bank_reference or '',
                    'receipt_number': payment.receipt_number or '',
                })
            
            total_count = request.env['edu.student.payment'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des paiements: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-payments/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_payment(self, **kwargs):
        """Récupère un paiement étudiant spécifique"""
        try:
            payment_id = kwargs.get('payment_id')
            if not payment_id:
                return {'success': False, 'error': 'ID de paiement requis'}
            
            payment = request.env['edu.student.payment'].browse(payment_id)
            
            if not payment.exists():
                return {'success': False, 'error': 'Paiement non trouvé'}
            
            data = {
                'id': payment.id,
                'reference': payment.reference or '',
                'student_id': payment.student_id.id if payment.student_id else None,
                'student_name': payment.student_id.name if payment.student_id else '',
                'student_email': payment.student_id.email if payment.student_id else '',
                'student_phone': payment.student_id.phone if payment.student_id else '',
                'student_registration_number': payment.student_id.registration_number if payment.student_id else '',
                'invoice_id': payment.invoice_id.id if payment.invoice_id else None,
                'invoice_number': payment.invoice_id.number if payment.invoice_id else '',
                'invoice_amount': payment.invoice_id.amount_total if payment.invoice_id else 0,
                'academic_year_id': payment.academic_year_id.id if payment.academic_year_id else None,
                'academic_year_name': payment.academic_year_id.name if payment.academic_year_id else '',
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'amount': payment.amount,
                'payment_method': payment.payment_method,
                'payment_method_display': dict(payment._fields['payment_method'].selection).get(payment.payment_method, ''),
                'state': payment.state,
                'state_display': dict(payment._fields['state'].selection).get(payment.state, ''),
                'currency_id': payment.currency_id.id if payment.currency_id else None,
                'currency_symbol': payment.currency_id.symbol if payment.currency_id else '',
                'bank_reference': payment.bank_reference or '',
                'receipt_number': payment.receipt_number or '',
                'transaction_id': payment.transaction_id or '',
                'payment_gateway': payment.payment_gateway or '',
                'notes': payment.notes or '',
                'is_partial_payment': payment.is_partial_payment,
                'remaining_amount': payment.remaining_amount,
                'fee_structure_id': payment.fee_structure_id.id if hasattr(payment, 'fee_structure_id') and payment.fee_structure_id else None,
                'late_fee_amount': payment.late_fee_amount if hasattr(payment, 'late_fee_amount') else 0,
                'discount_amount': payment.discount_amount if hasattr(payment, 'discount_amount') else 0,
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-payments/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_student_payment(self, **kwargs):
        """Crée un nouveau paiement étudiant"""
        try:
            # Validation des champs requis
            required_fields = ['student_id', 'amount', 'payment_method', 'payment_date']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Champ requis manquant: {field}'}
            
            # Validation du montant
            if kwargs['amount'] <= 0:
                return {'success': False, 'error': 'Le montant doit être positif'}
            
            # Préparation des données
            vals = {
                'student_id': kwargs['student_id'],
                'amount': kwargs['amount'],
                'payment_method': kwargs['payment_method'],
                'payment_date': kwargs['payment_date'],
            }
            
            # Champs optionnels
            optional_fields = [
                'reference', 'invoice_id', 'academic_year_id', 'currency_id',
                'bank_reference', 'receipt_number', 'transaction_id', 'payment_gateway',
                'notes', 'is_partial_payment', 'late_fee_amount', 'discount_amount'
            ]
            
            for field in optional_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Si aucune référence n'est fournie, en générer une
            if not vals.get('reference'):
                vals['reference'] = request.env['ir.sequence'].next_by_code('edu.student.payment') or 'PAY/'
            
            # Création du paiement
            payment = request.env['edu.student.payment'].create(vals)
            
            return {
                'success': True,
                'data': {
                    'id': payment.id,
                    'reference': payment.reference,
                    'amount': payment.amount
                },
                'message': 'Paiement créé avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la création du paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-payments/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_student_payment(self, **kwargs):
        """Met à jour un paiement étudiant"""
        try:
            payment_id = kwargs.get('payment_id')
            if not payment_id:
                return {'success': False, 'error': 'ID de paiement requis'}
            
            payment = request.env['edu.student.payment'].browse(payment_id)
            
            if not payment.exists():
                return {'success': False, 'error': 'Paiement non trouvé'}
            
            # Vérification de l'état
            if payment.state not in ['draft', 'pending']:
                return {'success': False, 'error': 'Seuls les paiements en brouillon ou en attente peuvent être modifiés'}
            
            # Préparation des données à mettre à jour
            vals = {}
            updatable_fields = [
                'reference', 'student_id', 'invoice_id', 'academic_year_id',
                'payment_date', 'amount', 'payment_method', 'bank_reference',
                'receipt_number', 'transaction_id', 'payment_gateway', 'notes',
                'is_partial_payment', 'late_fee_amount', 'discount_amount'
            ]
            
            for field in updatable_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Validation du montant si modifié
            if 'amount' in vals and vals['amount'] <= 0:
                return {'success': False, 'error': 'Le montant doit être positif'}
            
            # Mise à jour
            payment.write(vals)
            
            return {
                'success': True,
                'message': 'Paiement mis à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-payments/validate', type='json', auth='user', methods=['POST'], csrf=False)
    def validate_payment(self, **kwargs):
        """Valide un paiement"""
        try:
            payment_id = kwargs.get('payment_id')
            if not payment_id:
                return {'success': False, 'error': 'ID de paiement requis'}
            
            payment = request.env['edu.student.payment'].browse(payment_id)
            
            if not payment.exists():
                return {'success': False, 'error': 'Paiement non trouvé'}
            
            if payment.state not in ['draft', 'pending']:
                return {'success': False, 'error': 'Seuls les paiements en brouillon ou en attente peuvent être validés'}
            
            # Validation du paiement (méthode dépendante du modèle)
            if hasattr(payment, 'action_validate'):
                payment.action_validate()
            else:
                payment.write({'state': 'validated'})
            
            return {
                'success': True,
                'message': f'Paiement {payment.reference} validé avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la validation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-payments/cancel', type='json', auth='user', methods=['POST'], csrf=False)
    def cancel_payment(self, **kwargs):
        """Annule un paiement"""
        try:
            payment_id = kwargs.get('payment_id')
            if not payment_id:
                return {'success': False, 'error': 'ID de paiement requis'}
            
            payment = request.env['edu.student.payment'].browse(payment_id)
            
            if not payment.exists():
                return {'success': False, 'error': 'Paiement non trouvé'}
            
            if payment.state == 'validated':
                return {'success': False, 'error': 'Un paiement validé ne peut pas être annulé'}
            
            # Annulation du paiement
            if hasattr(payment, 'action_cancel'):
                payment.action_cancel()
            else:
                payment.write({'state': 'cancelled'})
            
            return {
                'success': True,
                'message': f'Paiement {payment.reference} annulé avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'annulation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-payments/methods', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payment_methods(self, **kwargs):
        """Récupère les méthodes de paiement disponibles"""
        try:
            # Récupération des méthodes depuis le modèle
            payment_model = request.env['edu.student.payment']
            
            if hasattr(payment_model, '_fields') and 'payment_method' in payment_model._fields:
                methods = payment_model._fields['payment_method'].selection
                
                result = []
                for method in methods:
                    result.append({
                        'code': method[0],
                        'name': method[1]
                    })
                
                return {
                    'success': True,
                    'data': result
                }
            else:
                # Méthodes par défaut si pas définies dans le modèle
                default_methods = [
                    {'code': 'cash', 'name': 'Espèces'},
                    {'code': 'bank_transfer', 'name': 'Virement bancaire'},
                    {'code': 'credit_card', 'name': 'Carte de crédit'},
                    {'code': 'debit_card', 'name': 'Carte de débit'},
                    {'code': 'cheque', 'name': 'Chèque'},
                    {'code': 'mobile_money', 'name': 'Mobile Money'},
                    {'code': 'online', 'name': 'Paiement en ligne'},
                ]
                
                return {
                    'success': True,
                    'data': default_methods
                }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des méthodes: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/student-payments/statistics', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payment_statistics(self, **kwargs):
        """Récupère les statistiques des paiements"""
        try:
            domain = []
            
            # Filtres optionnels pour les statistiques
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', kwargs['student_id']))
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            if kwargs.get('date_from'):
                domain.append(('payment_date', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('payment_date', '<=', kwargs['date_to']))
            
            payments = request.env['edu.student.payment'].search(domain)
            
            # Calculs des statistiques
            total_payments = len(payments)
            total_amount = sum(payments.mapped('amount'))
            
            # Statistiques par état
            by_state = {}
            for state in ['draft', 'pending', 'validated', 'cancelled']:
                state_payments = payments.filtered(lambda p: p.state == state)
                by_state[state] = {
                    'count': len(state_payments),
                    'amount': sum(state_payments.mapped('amount'))
                }
            
            # Statistiques par méthode de paiement
            by_method = {}
            for payment in payments:
                method = payment.payment_method
                if method not in by_method:
                    by_method[method] = {'count': 0, 'amount': 0}
                by_method[method]['count'] += 1
                by_method[method]['amount'] += payment.amount
            
            # Moyenne des paiements
            average_amount = total_amount / total_payments if total_payments > 0 else 0
            
            data = {
                'total_payments': total_payments,
                'total_amount': total_amount,
                'average_amount': average_amount,
                'by_state': by_state,
                'by_method': by_method,
                'currency_symbol': payments[0].currency_id.symbol if payments else '',
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
