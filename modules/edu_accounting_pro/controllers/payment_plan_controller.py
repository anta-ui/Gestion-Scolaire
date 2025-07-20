# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduPaymentPlanController(http.Controller):
    """Controller pour la gestion des plans de paiement"""

    @http.route('/api/payment-plans', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payment_plans(self, **kwargs):
        """Récupère la liste des plans de paiement"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', kwargs['student_id']))
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            if kwargs.get('plan_type'):
                domain.append(('plan_type', '=', kwargs['plan_type']))
            
            # Recherche par nom
            if kwargs.get('search'):
                domain.append('|', ('name', 'ilike', kwargs['search']), ('reference', 'ilike', kwargs['search']))
            
            # Pagination
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            payment_plans = request.env['edu.payment.plan'].search(domain, limit=limit, offset=offset)
            
            result = []
            for plan in payment_plans:
                result.append({
                    'id': plan.id,
                    'name': plan.name,
                    'reference': plan.reference if hasattr(plan, 'reference') else '',
                    'student_id': plan.student_id.id if hasattr(plan, 'student_id') and plan.student_id else None,
                    'student_name': plan.student_id.name if hasattr(plan, 'student_id') and plan.student_id else '',
                    'academic_year_id': plan.academic_year_id.id if hasattr(plan, 'academic_year_id') and plan.academic_year_id else None,
                    'academic_year_name': plan.academic_year_id.name if hasattr(plan, 'academic_year_id') and plan.academic_year_id else '',
                    'plan_type': plan.plan_type if hasattr(plan, 'plan_type') else '',
                    'plan_type_display': dict(plan._fields['plan_type'].selection).get(plan.plan_type, '') if hasattr(plan, 'plan_type') else '',
                    'total_amount': plan.total_amount if hasattr(plan, 'total_amount') else 0,
                    'paid_amount': plan.paid_amount if hasattr(plan, 'paid_amount') else 0,
                    'remaining_amount': plan.remaining_amount if hasattr(plan, 'remaining_amount') else 0,
                    'start_date': plan.start_date.isoformat() if hasattr(plan, 'start_date') and plan.start_date else None,
                    'end_date': plan.end_date.isoformat() if hasattr(plan, 'end_date') and plan.end_date else None,
                    'installments_count': plan.installments_count if hasattr(plan, 'installments_count') else 0,
                    'paid_installments': plan.paid_installments if hasattr(plan, 'paid_installments') else 0,
                    'next_due_date': plan.next_due_date.isoformat() if hasattr(plan, 'next_due_date') and plan.next_due_date else None,
                    'state': plan.state if hasattr(plan, 'state') else 'draft',
                    'state_display': dict(plan._fields['state'].selection).get(plan.state, '') if hasattr(plan, 'state') else '',
                    'active': plan.active if hasattr(plan, 'active') else True,
                    'currency_symbol': plan.currency_id.symbol if hasattr(plan, 'currency_id') and plan.currency_id else '',
                    'progress_percentage': (plan.paid_amount / plan.total_amount * 100) if hasattr(plan, 'paid_amount') and hasattr(plan, 'total_amount') and plan.total_amount > 0 else 0,
                })
            
            total_count = request.env['edu.payment.plan'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des plans de paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-plans/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payment_plan(self, **kwargs):
        """Récupère un plan de paiement spécifique"""
        try:
            plan_id = kwargs.get('plan_id')
            if not plan_id:
                return {'success': False, 'error': 'ID de plan de paiement requis'}
            
            plan = request.env['edu.payment.plan'].browse(plan_id)
            
            if not plan.exists():
                return {'success': False, 'error': 'Plan de paiement non trouvé'}
            
            # Récupération des échéances
            installments = []
            if hasattr(plan, 'installment_ids'):
                for installment in plan.installment_ids:
                    installments.append({
                        'id': installment.id,
                        'sequence': installment.sequence if hasattr(installment, 'sequence') else 0,
                        'name': installment.name if hasattr(installment, 'name') else '',
                        'due_date': installment.due_date.isoformat() if hasattr(installment, 'due_date') and installment.due_date else None,
                        'amount': installment.amount if hasattr(installment, 'amount') else 0,
                        'paid_amount': installment.paid_amount if hasattr(installment, 'paid_amount') else 0,
                        'remaining_amount': installment.remaining_amount if hasattr(installment, 'remaining_amount') else 0,
                        'state': installment.state if hasattr(installment, 'state') else 'pending',
                        'state_display': dict(installment._fields['state'].selection).get(installment.state, '') if hasattr(installment, 'state') else '',
                        'payment_date': installment.payment_date.isoformat() if hasattr(installment, 'payment_date') and installment.payment_date else None,
                        'late_fee': installment.late_fee if hasattr(installment, 'late_fee') else 0,
                        'is_overdue': installment.is_overdue if hasattr(installment, 'is_overdue') else False,
                        'days_overdue': installment.days_overdue if hasattr(installment, 'days_overdue') else 0,
                    })
            
            # Récupération des paiements associés
            payments = []
            if hasattr(plan, 'payment_ids'):
                for payment in plan.payment_ids:
                    payments.append({
                        'id': payment.id,
                        'reference': payment.reference if hasattr(payment, 'reference') else '',
                        'amount': payment.amount if hasattr(payment, 'amount') else 0,
                        'payment_date': payment.payment_date.isoformat() if hasattr(payment, 'payment_date') and payment.payment_date else None,
                        'payment_method': payment.payment_method if hasattr(payment, 'payment_method') else '',
                        'installment_id': payment.installment_id.id if hasattr(payment, 'installment_id') and payment.installment_id else None,
                        'state': payment.state if hasattr(payment, 'state') else 'draft',
                    })
            
            data = {
                'id': plan.id,
                'name': plan.name,
                'reference': plan.reference if hasattr(plan, 'reference') else '',
                'description': plan.description if hasattr(plan, 'description') else '',
                'student_id': plan.student_id.id if hasattr(plan, 'student_id') and plan.student_id else None,
                'student_name': plan.student_id.name if hasattr(plan, 'student_id') and plan.student_id else '',
                'student_email': plan.student_id.email if hasattr(plan, 'student_id') and plan.student_id and hasattr(plan.student_id, 'email') else '',
                'academic_year_id': plan.academic_year_id.id if hasattr(plan, 'academic_year_id') and plan.academic_year_id else None,
                'academic_year_name': plan.academic_year_id.name if hasattr(plan, 'academic_year_id') and plan.academic_year_id else '',
                'plan_type': plan.plan_type if hasattr(plan, 'plan_type') else '',
                'total_amount': plan.total_amount if hasattr(plan, 'total_amount') else 0,
                'paid_amount': plan.paid_amount if hasattr(plan, 'paid_amount') else 0,
                'remaining_amount': plan.remaining_amount if hasattr(plan, 'remaining_amount') else 0,
                'start_date': plan.start_date.isoformat() if hasattr(plan, 'start_date') and plan.start_date else None,
                'end_date': plan.end_date.isoformat() if hasattr(plan, 'end_date') and plan.end_date else None,
                'installments_count': plan.installments_count if hasattr(plan, 'installments_count') else 0,
                'paid_installments': plan.paid_installments if hasattr(plan, 'paid_installments') else 0,
                'next_due_date': plan.next_due_date.isoformat() if hasattr(plan, 'next_due_date') and plan.next_due_date else None,
                'late_fee_rate': plan.late_fee_rate if hasattr(plan, 'late_fee_rate') else 0,
                'grace_period_days': plan.grace_period_days if hasattr(plan, 'grace_period_days') else 0,
                'auto_generate_invoices': plan.auto_generate_invoices if hasattr(plan, 'auto_generate_invoices') else False,
                'send_reminders': plan.send_reminders if hasattr(plan, 'send_reminders') else False,
                'reminder_days_before': plan.reminder_days_before if hasattr(plan, 'reminder_days_before') else 7,
                'notes': plan.notes if hasattr(plan, 'notes') else '',
                'state': plan.state if hasattr(plan, 'state') else 'draft',
                'active': plan.active if hasattr(plan, 'active') else True,
                'currency_id': plan.currency_id.id if hasattr(plan, 'currency_id') and plan.currency_id else None,
                'currency_symbol': plan.currency_id.symbol if hasattr(plan, 'currency_id') and plan.currency_id else '',
                'installments': installments,
                'payments': payments,
                'progress_percentage': (plan.paid_amount / plan.total_amount * 100) if hasattr(plan, 'paid_amount') and hasattr(plan, 'total_amount') and plan.total_amount > 0 else 0,
                'overdue_amount': sum(i['remaining_amount'] for i in installments if i['is_overdue']),
                'next_installment': next((i for i in installments if i['state'] == 'pending'), None),
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du plan de paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-plans/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_payment_plan(self, **kwargs):
        """Crée un nouveau plan de paiement"""
        try:
            # Validation des champs requis
            required_fields = ['name', 'student_id', 'total_amount']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Champ requis manquant: {field}'}
            
            # Validation de la cohérence des données
            if kwargs['total_amount'] <= 0:
                return {'success': False, 'error': 'Le montant total doit être positif'}
            
            # Préparation des données
            vals = {
                'name': kwargs['name'],
                'student_id': kwargs['student_id'],
                'total_amount': kwargs['total_amount'],
            }
            
            # Champs optionnels
            optional_fields = [
                'reference', 'description', 'academic_year_id', 'plan_type',
                'start_date', 'end_date', 'installments_count', 'late_fee_rate',
                'grace_period_days', 'auto_generate_invoices', 'send_reminders',
                'reminder_days_before', 'notes', 'currency_id', 'active'
            ]
            
            for field in optional_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Validation supplémentaire
            if vals.get('end_date') and vals.get('start_date'):
                if vals['end_date'] <= vals['start_date']:
                    return {'success': False, 'error': 'La date de fin doit être postérieure à la date de début'}
            
            if vals.get('installments_count') and vals['installments_count'] <= 0:
                return {'success': False, 'error': 'Le nombre d\'échéances doit être positif'}
            
            # Création du plan de paiement
            plan = request.env['edu.payment.plan'].create(vals)
            
            # Génération automatique des échéances si demandé
            installments_data = kwargs.get('installments', [])
            if installments_data:
                self._create_installments(plan, installments_data)
            elif vals.get('installments_count') and vals.get('start_date'):
                self._auto_generate_installments(plan)
            
            return {
                'success': True,
                'data': {
                    'id': plan.id,
                    'name': plan.name,
                    'reference': plan.reference if hasattr(plan, 'reference') else ''
                },
                'message': 'Plan de paiement créé avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la création du plan de paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_installments(self, plan, installments_data):
        """Crée les échéances pour un plan de paiement"""
        try:
            for installment_data in installments_data:
                vals = {
                    'plan_id': plan.id,
                    'name': installment_data.get('name', f'Échéance {installment_data.get("sequence", 1)}'),
                    'sequence': installment_data.get('sequence', 1),
                    'due_date': installment_data['due_date'],
                    'amount': installment_data['amount'],
                }
                request.env['edu.payment.plan.installment'].create(vals)
        except Exception as e:
            _logger.error(f"Erreur lors de la création des échéances: {str(e)}")

    def _auto_generate_installments(self, plan):
        """Génère automatiquement les échéances pour un plan de paiement"""
        try:
            if not hasattr(plan, 'action_generate_installments'):
                return
            
            plan.action_generate_installments()
        except Exception as e:
            _logger.error(f"Erreur lors de la génération automatique des échéances: {str(e)}")

    @http.route('/api/payment-plans/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_payment_plan(self, **kwargs):
        """Met à jour un plan de paiement"""
        try:
            plan_id = kwargs.get('plan_id')
            if not plan_id:
                return {'success': False, 'error': 'ID de plan de paiement requis'}
            
            plan = request.env['edu.payment.plan'].browse(plan_id)
            
            if not plan.exists():
                return {'success': False, 'error': 'Plan de paiement non trouvé'}
            
            # Vérifier si le plan peut être modifié
            if hasattr(plan, 'state') and plan.state not in ['draft', 'active']:
                return {'success': False, 'error': 'Ce plan de paiement ne peut plus être modifié'}
            
            # Préparation des données à mettre à jour
            vals = {}
            updatable_fields = [
                'name', 'description', 'academic_year_id', 'plan_type',
                'total_amount', 'start_date', 'end_date', 'late_fee_rate',
                'grace_period_days', 'auto_generate_invoices', 'send_reminders',
                'reminder_days_before', 'notes', 'active'
            ]
            
            for field in updatable_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Validation
            if vals.get('total_amount') and vals['total_amount'] <= 0:
                return {'success': False, 'error': 'Le montant total doit être positif'}
            
            # Mise à jour
            plan.write(vals)
            
            return {
                'success': True,
                'message': 'Plan de paiement mis à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-plans/activate', type='json', auth='user', methods=['POST'], csrf=False)
    def activate_payment_plan(self, **kwargs):
        """Active un plan de paiement"""
        try:
            plan_id = kwargs.get('plan_id')
            if not plan_id:
                return {'success': False, 'error': 'ID de plan de paiement requis'}
            
            plan = request.env['edu.payment.plan'].browse(plan_id)
            
            if not plan.exists():
                return {'success': False, 'error': 'Plan de paiement non trouvé'}
            
            # Activation du plan
            if hasattr(plan, 'action_activate'):
                plan.action_activate()
            else:
                plan.write({'state': 'active'})
            
            return {
                'success': True,
                'message': f'Plan de paiement "{plan.name}" activé avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'activation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-plans/record-payment', type='json', auth='user', methods=['POST'], csrf=False)
    def record_payment(self, **kwargs):
        """Enregistre un paiement pour un plan"""
        try:
            plan_id = kwargs.get('plan_id')
            installment_id = kwargs.get('installment_id')
            amount = kwargs.get('amount')
            payment_date = kwargs.get('payment_date')
            payment_method = kwargs.get('payment_method')
            
            if not plan_id:
                return {'success': False, 'error': 'ID de plan de paiement requis'}
            if not amount or amount <= 0:
                return {'success': False, 'error': 'Montant de paiement requis et positif'}
            
            plan = request.env['edu.payment.plan'].browse(plan_id)
            
            if not plan.exists():
                return {'success': False, 'error': 'Plan de paiement non trouvé'}
            
            # Enregistrement du paiement
            payment_vals = {
                'plan_id': plan.id,
                'amount': amount,
                'payment_date': payment_date,
                'payment_method': payment_method or 'cash',
                'reference': kwargs.get('reference', ''),
                'notes': kwargs.get('notes', ''),
            }
            
            if installment_id:
                installment = request.env['edu.payment.plan.installment'].browse(installment_id)
                if installment.exists():
                    payment_vals['installment_id'] = installment.id
            
            # Création du paiement
            if hasattr(plan, 'record_payment'):
                result = plan.record_payment(**payment_vals)
            else:
                payment = request.env['edu.student.payment'].create(payment_vals)
                result = {'payment_id': payment.id}
            
            return {
                'success': True,
                'data': result,
                'message': 'Paiement enregistré avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'enregistrement du paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-plans/send-reminder', type='json', auth='user', methods=['POST'], csrf=False)
    def send_reminder(self, **kwargs):
        """Envoie un rappel de paiement"""
        try:
            plan_id = kwargs.get('plan_id')
            if not plan_id:
                return {'success': False, 'error': 'ID de plan de paiement requis'}
            
            plan = request.env['edu.payment.plan'].browse(plan_id)
            
            if not plan.exists():
                return {'success': False, 'error': 'Plan de paiement non trouvé'}
            
            # Envoi du rappel
            if hasattr(plan, 'send_payment_reminder'):
                result = plan.send_payment_reminder()
                message = 'Rappel de paiement envoyé avec succès'
            else:
                message = 'Fonction de rappel non disponible'
                result = {}
            
            return {
                'success': True,
                'data': result,
                'message': message
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi du rappel: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-plans/statistics', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payment_plan_statistics(self, **kwargs):
        """Récupère les statistiques des plans de paiement"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', kwargs['student_id']))
            if kwargs.get('date_from'):
                domain.append(('start_date', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('end_date', '<=', kwargs['date_to']))
            
            plans = request.env['edu.payment.plan'].search(domain)
            
            # Calculs des statistiques
            total_plans = len(plans)
            active_plans = len(plans.filtered(lambda p: p.state == 'active' if hasattr(p, 'state') else True))
            completed_plans = len(plans.filtered(lambda p: p.state == 'completed' if hasattr(p, 'state') else False))
            
            total_amount = sum(plans.mapped('total_amount')) if hasattr(plans, 'total_amount') else 0
            paid_amount = sum(plans.mapped('paid_amount')) if hasattr(plans, 'paid_amount') else 0
            remaining_amount = total_amount - paid_amount
            
            # Statistiques par état
            by_state = {}
            for plan in plans:
                state = plan.state if hasattr(plan, 'state') else 'unknown'
                if state not in by_state:
                    by_state[state] = {'count': 0, 'total_amount': 0, 'paid_amount': 0}
                by_state[state]['count'] += 1
                by_state[state]['total_amount'] += plan.total_amount if hasattr(plan, 'total_amount') else 0
                by_state[state]['paid_amount'] += plan.paid_amount if hasattr(plan, 'paid_amount') else 0
            
            # Plans en retard
            overdue_plans = 0
            overdue_amount = 0
            for plan in plans:
                if hasattr(plan, 'next_due_date') and plan.next_due_date:
                    from datetime import date
                    if plan.next_due_date < date.today() and hasattr(plan, 'remaining_amount'):
                        overdue_plans += 1
                        overdue_amount += plan.remaining_amount
            
            data = {
                'total_plans': total_plans,
                'active_plans': active_plans,
                'completed_plans': completed_plans,
                'overdue_plans': overdue_plans,
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'remaining_amount': remaining_amount,
                'overdue_amount': overdue_amount,
                'collection_rate': (paid_amount / total_amount * 100) if total_amount > 0 else 0,
                'completion_rate': (completed_plans / total_plans * 100) if total_plans > 0 else 0,
                'by_state': by_state,
                'average_plan_amount': total_amount / total_plans if total_plans > 0 else 0,
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
