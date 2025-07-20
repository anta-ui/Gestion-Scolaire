# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduFinancialAidController(http.Controller):
    """Controller pour la gestion de l'aide financière"""

    @http.route('/api/financial-aids', type='json', auth='user', methods=['POST'], csrf=False)
    def get_financial_aids(self, **kwargs):
        """Récupère la liste des aides financières"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', kwargs['student_id']))
            if kwargs.get('aid_type'):
                domain.append(('aid_type', '=', kwargs['aid_type']))
            if kwargs.get('status'):
                domain.append(('status', '=', kwargs['status']))
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            
            # Recherche par nom/référence
            if kwargs.get('search'):
                domain.append('|', ('name', 'ilike', kwargs['search']), ('reference', 'ilike', kwargs['search']))
            
            # Filtres de date
            if kwargs.get('date_from'):
                domain.append(('application_date', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('application_date', '<=', kwargs['date_to']))
            
            # Pagination
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            aids = request.env['edu.financial.aid'].search(domain, limit=limit, offset=offset)
            
            result = []
            for aid in aids:
                result.append({
                    'id': aid.id,
                    'name': aid.name,
                    'reference': aid.reference if hasattr(aid, 'reference') else '',
                    'student_id': aid.student_id.id if hasattr(aid, 'student_id') and aid.student_id else None,
                    'student_name': aid.student_id.name if hasattr(aid, 'student_id') and aid.student_id else '',
                    'aid_type': aid.aid_type if hasattr(aid, 'aid_type') else '',
                    'aid_type_display': dict(aid._fields['aid_type'].selection).get(aid.aid_type, '') if hasattr(aid, 'aid_type') else '',
                    'amount': aid.amount if hasattr(aid, 'amount') else 0,
                    'percentage': aid.percentage if hasattr(aid, 'percentage') else 0,
                    'status': aid.status if hasattr(aid, 'status') else 'draft',
                    'status_display': dict(aid._fields['status'].selection).get(aid.status, '') if hasattr(aid, 'status') else '',
                    'application_date': aid.application_date.isoformat() if hasattr(aid, 'application_date') and aid.application_date else None,
                    'approved_date': aid.approved_date.isoformat() if hasattr(aid, 'approved_date') and aid.approved_date else None,
                    'disbursed_amount': aid.disbursed_amount if hasattr(aid, 'disbursed_amount') else 0,
                    'remaining_amount': aid.remaining_amount if hasattr(aid, 'remaining_amount') else 0,
                    'currency_symbol': aid.currency_id.symbol if hasattr(aid, 'currency_id') and aid.currency_id else '',
                    'active': aid.active if hasattr(aid, 'active') else True,
                })
            
            total_count = request.env['edu.financial.aid'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des aides financières: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/financial-aids/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_financial_aid(self, **kwargs):
        """Récupère une aide financière spécifique"""
        try:
            aid_id = kwargs.get('aid_id')
            if not aid_id:
                return {'success': False, 'error': 'ID d\'aide financière requis'}
            
            aid = request.env['edu.financial.aid'].browse(aid_id)
            
            if not aid.exists():
                return {'success': False, 'error': 'Aide financière non trouvée'}
            
            data = {
                'id': aid.id,
                'name': aid.name,
                'reference': aid.reference if hasattr(aid, 'reference') else '',
                'description': aid.description if hasattr(aid, 'description') else '',
                'student_id': aid.student_id.id if hasattr(aid, 'student_id') and aid.student_id else None,
                'student_name': aid.student_id.name if hasattr(aid, 'student_id') and aid.student_id else '',
                'aid_type': aid.aid_type if hasattr(aid, 'aid_type') else '',
                'amount': aid.amount if hasattr(aid, 'amount') else 0,
                'percentage': aid.percentage if hasattr(aid, 'percentage') else 0,
                'status': aid.status if hasattr(aid, 'status') else 'draft',
                'application_date': aid.application_date.isoformat() if hasattr(aid, 'application_date') and aid.application_date else None,
                'approved_date': aid.approved_date.isoformat() if hasattr(aid, 'approved_date') and aid.approved_date else None,
                'start_date': aid.start_date.isoformat() if hasattr(aid, 'start_date') and aid.start_date else None,
                'end_date': aid.end_date.isoformat() if hasattr(aid, 'end_date') and aid.end_date else None,
                'approved_by_id': aid.approved_by.id if hasattr(aid, 'approved_by') and aid.approved_by else None,
                'approved_by_name': aid.approved_by.name if hasattr(aid, 'approved_by') and aid.approved_by else '',
                'disbursed_amount': aid.disbursed_amount if hasattr(aid, 'disbursed_amount') else 0,
                'remaining_amount': aid.remaining_amount if hasattr(aid, 'remaining_amount') else 0,
                'disbursement_method': aid.disbursement_method if hasattr(aid, 'disbursement_method') else '',
                'requirements': aid.requirements if hasattr(aid, 'requirements') else '',
                'documents_required': aid.documents_required if hasattr(aid, 'documents_required') else False,
                'renewal_required': aid.renewal_required if hasattr(aid, 'renewal_required') else False,
                'academic_year_id': aid.academic_year_id.id if hasattr(aid, 'academic_year_id') and aid.academic_year_id else None,
                'academic_year_name': aid.academic_year_id.name if hasattr(aid, 'academic_year_id') and aid.academic_year_id else '',
                'course_id': aid.course_id.id if hasattr(aid, 'course_id') and aid.course_id else None,
                'course_name': aid.course_id.name if hasattr(aid, 'course_id') and aid.course_id else '',
                'notes': aid.notes if hasattr(aid, 'notes') else '',
                'active': aid.active if hasattr(aid, 'active') else True,
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de l'aide: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/financial-aids/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_financial_aid(self, **kwargs):
        """Crée une nouvelle aide financière"""
        try:
            # Validation des champs requis
            required_fields = ['name', 'student_id', 'aid_type']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Champ requis manquant: {field}'}
            
            # Validation du montant ou pourcentage
            amount = kwargs.get('amount', 0)
            percentage = kwargs.get('percentage', 0)
            
            if not amount and not percentage:
                return {'success': False, 'error': 'Montant ou pourcentage requis'}
            
            if amount and percentage:
                return {'success': False, 'error': 'Montant et pourcentage sont mutuellement exclusifs'}
            
            # Préparation des données
            vals = {
                'name': kwargs['name'],
                'student_id': kwargs['student_id'],
                'aid_type': kwargs['aid_type'],
                'amount': amount,
                'percentage': percentage,
            }
            
            # Champs optionnels
            optional_fields = [
                'reference', 'description', 'application_date', 'start_date', 'end_date',
                'disbursement_method', 'requirements', 'documents_required', 'renewal_required',
                'academic_year_id', 'course_id', 'notes', 'active'
            ]
            
            for field in optional_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Validation des dates
            if vals.get('start_date') and vals.get('end_date'):
                if vals['start_date'] > vals['end_date']:
                    return {'success': False, 'error': 'La date de début ne peut pas être après la date de fin'}
            
            # Vérification de l'existence de l'étudiant
            student = request.env['res.partner'].browse(kwargs['student_id'])
            if not student.exists():
                return {'success': False, 'error': 'Étudiant non trouvé'}
            
            # Création de l'aide financière
            aid = request.env['edu.financial.aid'].create(vals)
            
            return {
                'success': True,
                'data': {
                    'id': aid.id,
                    'name': aid.name,
                    'reference': aid.reference if hasattr(aid, 'reference') else ''
                },
                'message': 'Aide financière créée avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la création: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/financial-aids/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_financial_aid(self, **kwargs):
        """Met à jour une aide financière"""
        try:
            aid_id = kwargs.get('aid_id')
            if not aid_id:
                return {'success': False, 'error': 'ID d\'aide financière requis'}
            
            aid = request.env['edu.financial.aid'].browse(aid_id)
            
            if not aid.exists():
                return {'success': False, 'error': 'Aide financière non trouvée'}
            
            # Préparation des données à mettre à jour
            vals = {}
            updatable_fields = [
                'name', 'description', 'student_id', 'aid_type', 'amount', 'percentage',
                'application_date', 'start_date', 'end_date', 'disbursement_method',
                'requirements', 'documents_required', 'renewal_required',
                'academic_year_id', 'course_id', 'notes', 'active'
            ]
            
            for field in updatable_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Validation du montant ou pourcentage
            final_amount = vals.get('amount', aid.amount if hasattr(aid, 'amount') else 0)
            final_percentage = vals.get('percentage', aid.percentage if hasattr(aid, 'percentage') else 0)
            
            if final_amount and final_percentage:
                return {'success': False, 'error': 'Montant et pourcentage sont mutuellement exclusifs'}
            
            if not final_amount and not final_percentage:
                return {'success': False, 'error': 'Montant ou pourcentage requis'}
            
            # Validation des dates
            final_start = vals.get('start_date', aid.start_date if hasattr(aid, 'start_date') else None)
            final_end = vals.get('end_date', aid.end_date if hasattr(aid, 'end_date') else None)
            
            if final_start and final_end and final_start > final_end:
                return {'success': False, 'error': 'La date de début ne peut pas être après la date de fin'}
            
            # Mise à jour
            aid.write(vals)
            
            return {
                'success': True,
                'message': 'Aide financière mise à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/financial-aids/approve', type='json', auth='user', methods=['POST'], csrf=False)
    def approve_financial_aid(self, **kwargs):
        """Approuve une aide financière"""
        try:
            aid_id = kwargs.get('aid_id')
            if not aid_id:
                return {'success': False, 'error': 'ID d\'aide financière requis'}
            
            aid = request.env['edu.financial.aid'].browse(aid_id)
            
            if not aid.exists():
                return {'success': False, 'error': 'Aide financière non trouvée'}
            
            # Vérifier si l'aide peut être approuvée
            if hasattr(aid, 'status') and aid.status == 'approved':
                return {'success': False, 'error': 'Aide déjà approuvée'}
            
            # Effectuer l'approbation
            vals = {
                'status': 'approved',
                'approved_date': request.env.context.get('approval_date') or kwargs.get('approved_date'),
                'approved_by': request.env.user.id,
            }
            
            if hasattr(aid, 'action_approve'):
                aid.action_approve()
            else:
                aid.write(vals)
            
            return {
                'success': True,
                'message': f'Aide financière "{aid.name}" approuvée avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'approbation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/financial-aids/reject', type='json', auth='user', methods=['POST'], csrf=False)
    def reject_financial_aid(self, **kwargs):
        """Rejette une aide financière"""
        try:
            aid_id = kwargs.get('aid_id')
            rejection_reason = kwargs.get('reason', '')
            
            if not aid_id:
                return {'success': False, 'error': 'ID d\'aide financière requis'}
            
            aid = request.env['edu.financial.aid'].browse(aid_id)
            
            if not aid.exists():
                return {'success': False, 'error': 'Aide financière non trouvée'}
            
            # Vérifier si l'aide peut être rejetée
            if hasattr(aid, 'status') and aid.status == 'rejected':
                return {'success': False, 'error': 'Aide déjà rejetée'}
            
            # Effectuer le rejet
            vals = {
                'status': 'rejected',
                'rejection_reason': rejection_reason,
                'rejected_by': request.env.user.id,
                'rejected_date': request.env.context.get('rejection_date') or kwargs.get('rejected_date'),
            }
            
            if hasattr(aid, 'action_reject'):
                aid.action_reject()
            else:
                aid.write(vals)
            
            return {
                'success': True,
                'message': f'Aide financière "{aid.name}" rejetée'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors du rejet: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/financial-aids/disburse', type='json', auth='user', methods=['POST'], csrf=False)
    def disburse_financial_aid(self, **kwargs):
        """Effectue un décaissement d'aide financière"""
        try:
            aid_id = kwargs.get('aid_id')
            amount = kwargs.get('amount')
            
            if not aid_id:
                return {'success': False, 'error': 'ID d\'aide financière requis'}
            if not amount or amount <= 0:
                return {'success': False, 'error': 'Montant de décaissement requis et positif'}
            
            aid = request.env['edu.financial.aid'].browse(aid_id)
            
            if not aid.exists():
                return {'success': False, 'error': 'Aide financière non trouvée'}
            
            # Vérifier si l'aide est approuvée
            if hasattr(aid, 'status') and aid.status != 'approved':
                return {'success': False, 'error': 'L\'aide doit être approuvée avant décaissement'}
            
            # Vérifier le montant disponible
            remaining = aid.remaining_amount if hasattr(aid, 'remaining_amount') else aid.amount
            if amount > remaining:
                return {'success': False, 'error': f'Montant supérieur au solde disponible ({remaining})'}
            
            # Effectuer le décaissement
            if hasattr(aid, 'action_disburse'):
                aid.action_disburse(amount)
            else:
                disbursed = aid.disbursed_amount if hasattr(aid, 'disbursed_amount') else 0
                aid.write({
                    'disbursed_amount': disbursed + amount,
                    'last_disbursement_date': kwargs.get('disbursement_date'),
                })
            
            return {
                'success': True,
                'message': f'Décaissement de {amount} effectué avec succès',
                'data': {
                    'disbursed_amount': amount,
                    'total_disbursed': (aid.disbursed_amount if hasattr(aid, 'disbursed_amount') else 0) + amount,
                    'remaining_amount': remaining - amount
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors du décaissement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/financial-aids/statistics', type='json', auth='user', methods=['POST'], csrf=False)
    def get_aid_statistics(self, **kwargs):
        """Récupère les statistiques des aides financières"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            if kwargs.get('aid_type'):
                domain.append(('aid_type', '=', kwargs['aid_type']))
            if kwargs.get('date_from'):
                domain.append(('application_date', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('application_date', '<=', kwargs['date_to']))
            
            aids = request.env['edu.financial.aid'].search(domain)
            
            # Calculs des statistiques
            total_aids = len(aids)
            approved_aids = len(aids.filtered(lambda a: a.status == 'approved' if hasattr(a, 'status') else False))
            rejected_aids = len(aids.filtered(lambda a: a.status == 'rejected' if hasattr(a, 'status') else False))
            pending_aids = total_aids - approved_aids - rejected_aids
            
            total_amount = sum(aids.mapped('amount')) if hasattr(aids, 'amount') else 0
            disbursed_amount = sum(aids.mapped('disbursed_amount')) if hasattr(aids, 'disbursed_amount') else 0
            remaining_amount = total_amount - disbursed_amount
            
            # Statistiques par type
            by_type = {}
            for aid in aids:
                aid_type = aid.aid_type if hasattr(aid, 'aid_type') else 'other'
                if aid_type not in by_type:
                    by_type[aid_type] = {'count': 0, 'total_amount': 0, 'approved': 0}
                by_type[aid_type]['count'] += 1
                if hasattr(aid, 'amount'):
                    by_type[aid_type]['total_amount'] += aid.amount
                if hasattr(aid, 'status') and aid.status == 'approved':
                    by_type[aid_type]['approved'] += 1
            
            # Étudiants bénéficiaires uniques
            unique_students = len(set(aids.mapped('student_id.id'))) if aids else 0
            
            data = {
                'total_aids': total_aids,
                'approved_aids': approved_aids,
                'rejected_aids': rejected_aids,
                'pending_aids': pending_aids,
                'approval_rate': (approved_aids / total_aids * 100) if total_aids > 0 else 0,
                'total_amount': total_amount,
                'disbursed_amount': disbursed_amount,
                'remaining_amount': remaining_amount,
                'disbursement_rate': (disbursed_amount / total_amount * 100) if total_amount > 0 else 0,
                'unique_students': unique_students,
                'average_aid_per_student': (total_amount / unique_students) if unique_students > 0 else 0,
                'by_type': by_type,
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
