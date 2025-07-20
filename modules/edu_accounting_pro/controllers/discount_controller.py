# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduDiscountController(http.Controller):
    """Controller pour la gestion des remises et réductions"""

    @http.route('/api/discounts', type='json', auth='user', methods=['POST'], csrf=False)
    def get_discounts(self, **kwargs):
        """Récupère la liste des remises"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
            if kwargs.get('discount_type'):
                domain.append(('discount_type', '=', kwargs['discount_type']))
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            if kwargs.get('applicable_to'):
                domain.append(('applicable_to', '=', kwargs['applicable_to']))
            
            # Recherche par nom
            if kwargs.get('search'):
                domain.append(('name', 'ilike', kwargs['search']))
            
            # Pagination
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            discounts = request.env['edu.discount'].search(domain, limit=limit, offset=offset)
            
            result = []
            for discount in discounts:
                result.append({
                    'id': discount.id,
                    'name': discount.name,
                    'code': discount.code if hasattr(discount, 'code') else '',
                    'description': discount.description if hasattr(discount, 'description') else '',
                    'discount_type': discount.discount_type if hasattr(discount, 'discount_type') else '',
                    'discount_type_display': dict(discount._fields['discount_type'].selection).get(discount.discount_type, '') if hasattr(discount, 'discount_type') else '',
                    'amount': discount.amount if hasattr(discount, 'amount') else 0,
                    'percentage': discount.percentage if hasattr(discount, 'percentage') else 0,
                    'academic_year_id': discount.academic_year_id.id if hasattr(discount, 'academic_year_id') and discount.academic_year_id else None,
                    'academic_year_name': discount.academic_year_id.name if hasattr(discount, 'academic_year_id') and discount.academic_year_id else '',
                    'applicable_to': discount.applicable_to if hasattr(discount, 'applicable_to') else '',
                    'max_usage': discount.max_usage if hasattr(discount, 'max_usage') else 0,
                    'current_usage': discount.current_usage if hasattr(discount, 'current_usage') else 0,
                    'start_date': discount.start_date.isoformat() if hasattr(discount, 'start_date') and discount.start_date else None,
                    'end_date': discount.end_date.isoformat() if hasattr(discount, 'end_date') and discount.end_date else None,
                    'is_cumulative': discount.is_cumulative if hasattr(discount, 'is_cumulative') else False,
                    'active': discount.active if hasattr(discount, 'active') else True,
                    'currency_symbol': discount.currency_id.symbol if hasattr(discount, 'currency_id') and discount.currency_id else '',
                })
            
            total_count = request.env['edu.discount'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des remises: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/discounts/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_discount(self, **kwargs):
        """Récupère une remise spécifique"""
        try:
            discount_id = kwargs.get('discount_id')
            if not discount_id:
                return {'success': False, 'error': 'ID de remise requis'}
            
            discount = request.env['edu.discount'].browse(discount_id)
            
            if not discount.exists():
                return {'success': False, 'error': 'Remise non trouvée'}
            
            # Récupération des critères d'éligibilité
            eligibility_criteria = []
            if hasattr(discount, 'eligibility_criteria_ids'):
                for criteria in discount.eligibility_criteria_ids:
                    eligibility_criteria.append({
                        'id': criteria.id,
                        'criteria_type': criteria.criteria_type if hasattr(criteria, 'criteria_type') else '',
                        'operator': criteria.operator if hasattr(criteria, 'operator') else '',
                        'value': criteria.value if hasattr(criteria, 'value') else '',
                        'description': criteria.description if hasattr(criteria, 'description') else '',
                    })
            
            # Récupération des utilisations
            usage_history = []
            if hasattr(discount, 'usage_ids'):
                for usage in discount.usage_ids:
                    usage_history.append({
                        'id': usage.id,
                        'student_id': usage.student_id.id if hasattr(usage, 'student_id') and usage.student_id else None,
                        'student_name': usage.student_id.name if hasattr(usage, 'student_id') and usage.student_id else '',
                        'invoice_id': usage.invoice_id.id if hasattr(usage, 'invoice_id') and usage.invoice_id else None,
                        'invoice_number': usage.invoice_id.number if hasattr(usage, 'invoice_id') and usage.invoice_id else '',
                        'amount_discounted': usage.amount_discounted if hasattr(usage, 'amount_discounted') else 0,
                        'date_applied': usage.date_applied.isoformat() if hasattr(usage, 'date_applied') and usage.date_applied else None,
                    })
            
            data = {
                'id': discount.id,
                'name': discount.name,
                'code': discount.code if hasattr(discount, 'code') else '',
                'description': discount.description if hasattr(discount, 'description') else '',
                'discount_type': discount.discount_type if hasattr(discount, 'discount_type') else '',
                'amount': discount.amount if hasattr(discount, 'amount') else 0,
                'percentage': discount.percentage if hasattr(discount, 'percentage') else 0,
                'academic_year_id': discount.academic_year_id.id if hasattr(discount, 'academic_year_id') and discount.academic_year_id else None,
                'academic_year_name': discount.academic_year_id.name if hasattr(discount, 'academic_year_id') and discount.academic_year_id else '',
                'applicable_to': discount.applicable_to if hasattr(discount, 'applicable_to') else '',
                'max_usage': discount.max_usage if hasattr(discount, 'max_usage') else 0,
                'current_usage': discount.current_usage if hasattr(discount, 'current_usage') else 0,
                'start_date': discount.start_date.isoformat() if hasattr(discount, 'start_date') and discount.start_date else None,
                'end_date': discount.end_date.isoformat() if hasattr(discount, 'end_date') and discount.end_date else None,
                'is_cumulative': discount.is_cumulative if hasattr(discount, 'is_cumulative') else False,
                'requires_approval': discount.requires_approval if hasattr(discount, 'requires_approval') else False,
                'auto_apply': discount.auto_apply if hasattr(discount, 'auto_apply') else False,
                'minimum_amount': discount.minimum_amount if hasattr(discount, 'minimum_amount') else 0,
                'maximum_discount': discount.maximum_discount if hasattr(discount, 'maximum_discount') else 0,
                'terms_conditions': discount.terms_conditions if hasattr(discount, 'terms_conditions') else '',
                'active': discount.active if hasattr(discount, 'active') else True,
                'currency_id': discount.currency_id.id if hasattr(discount, 'currency_id') and discount.currency_id else None,
                'currency_symbol': discount.currency_id.symbol if hasattr(discount, 'currency_id') and discount.currency_id else '',
                'eligibility_criteria': eligibility_criteria,
                'usage_history': usage_history,
                'remaining_usage': (discount.max_usage - discount.current_usage) if hasattr(discount, 'max_usage') and hasattr(discount, 'current_usage') else 0,
                'total_discounted': sum(u['amount_discounted'] for u in usage_history),
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la remise: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/discounts/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_discount(self, **kwargs):
        """Crée une nouvelle remise"""
        try:
            # Validation des champs requis
            required_fields = ['name', 'discount_type']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Champ requis manquant: {field}'}
            
            # Préparation des données
            vals = {
                'name': kwargs['name'],
                'discount_type': kwargs['discount_type'],
            }
            
            # Champs optionnels
            optional_fields = [
                'code', 'description', 'amount', 'percentage', 'academic_year_id',
                'applicable_to', 'max_usage', 'start_date', 'end_date',
                'is_cumulative', 'requires_approval', 'auto_apply',
                'minimum_amount', 'maximum_discount', 'terms_conditions',
                'currency_id', 'active'
            ]
            
            for field in optional_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Validation de cohérence
            if vals.get('amount') and vals.get('percentage'):
                return {'success': False, 'error': 'Spécifiez soit un montant fixe, soit un pourcentage, pas les deux'}
            
            if not vals.get('amount') and not vals.get('percentage'):
                return {'success': False, 'error': 'Spécifiez soit un montant fixe, soit un pourcentage'}
            
            if vals.get('percentage') and (vals['percentage'] < 0 or vals['percentage'] > 100):
                return {'success': False, 'error': 'Le pourcentage de remise doit être entre 0 et 100'}
            
            if vals.get('end_date') and vals.get('start_date'):
                if vals['end_date'] < vals['start_date']:
                    return {'success': False, 'error': 'La date de fin doit être postérieure à la date de début'}
            
            # Création de la remise
            discount = request.env['edu.discount'].create(vals)
            
            return {
                'success': True,
                'data': {
                    'id': discount.id,
                    'name': discount.name,
                    'code': discount.code if hasattr(discount, 'code') else ''
                },
                'message': 'Remise créée avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la remise: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/discounts/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_discount(self, **kwargs):
        """Met à jour une remise"""
        try:
            discount_id = kwargs.get('discount_id')
            if not discount_id:
                return {'success': False, 'error': 'ID de remise requis'}
            
            discount = request.env['edu.discount'].browse(discount_id)
            
            if not discount.exists():
                return {'success': False, 'error': 'Remise non trouvée'}
            
            # Préparation des données à mettre à jour
            vals = {}
            updatable_fields = [
                'name', 'code', 'description', 'discount_type', 'amount', 'percentage',
                'academic_year_id', 'applicable_to', 'max_usage', 'start_date', 'end_date',
                'is_cumulative', 'requires_approval', 'auto_apply', 'minimum_amount',
                'maximum_discount', 'terms_conditions', 'active'
            ]
            
            for field in updatable_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Validation de cohérence
            final_amount = vals.get('amount', discount.amount if hasattr(discount, 'amount') else None)
            final_percentage = vals.get('percentage', discount.percentage if hasattr(discount, 'percentage') else None)
            
            if final_amount and final_percentage:
                return {'success': False, 'error': 'Spécifiez soit un montant fixe, soit un pourcentage, pas les deux'}
            
            if vals.get('percentage') and (vals['percentage'] < 0 or vals['percentage'] > 100):
                return {'success': False, 'error': 'Le pourcentage de remise doit être entre 0 et 100'}
            
            # Mise à jour
            discount.write(vals)
            
            return {
                'success': True,
                'message': 'Remise mise à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/discounts/apply', type='json', auth='user', methods=['POST'], csrf=False)
    def apply_discount(self, **kwargs):
        """Applique une remise à une facture ou un étudiant"""
        try:
            discount_id = kwargs.get('discount_id')
            if not discount_id:
                return {'success': False, 'error': 'ID de remise requis'}
            
            discount = request.env['edu.discount'].browse(discount_id)
            
            if not discount.exists():
                return {'success': False, 'error': 'Remise non trouvée'}
            
            # Validation des paramètres
            student_id = kwargs.get('student_id')
            invoice_id = kwargs.get('invoice_id')
            
            if not student_id and not invoice_id:
                return {'success': False, 'error': 'ID étudiant ou ID facture requis'}
            
            # Application de la remise
            result = {}
            if hasattr(discount, 'apply_discount'):
                if invoice_id:
                    invoice = request.env['edu.student.invoice'].browse(invoice_id)
                    if not invoice.exists():
                        return {'success': False, 'error': 'Facture non trouvée'}
                    result = discount.apply_discount(invoice=invoice)
                elif student_id:
                    student = request.env['op.student'].browse(student_id)
                    if not student.exists():
                        return {'success': False, 'error': 'Étudiant non trouvé'}
                    result = discount.apply_discount(student=student)
            else:
                # Logique d'application par défaut
                return {'success': False, 'error': 'Méthode d\'application non disponible'}
            
            return {
                'success': True,
                'data': result,
                'message': f'Remise "{discount.name}" appliquée avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'application de la remise: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/discounts/validate-eligibility', type='json', auth='user', methods=['POST'], csrf=False)
    def validate_eligibility(self, **kwargs):
        """Valide l'éligibilité d'un étudiant pour une remise"""
        try:
            discount_id = kwargs.get('discount_id')
            student_id = kwargs.get('student_id')
            
            if not discount_id:
                return {'success': False, 'error': 'ID de remise requis'}
            if not student_id:
                return {'success': False, 'error': 'ID étudiant requis'}
            
            discount = request.env['edu.discount'].browse(discount_id)
            student = request.env['op.student'].browse(student_id)
            
            if not discount.exists():
                return {'success': False, 'error': 'Remise non trouvée'}
            if not student.exists():
                return {'success': False, 'error': 'Étudiant non trouvé'}
            
            # Validation de l'éligibilité
            is_eligible = True
            reasons = []
            
            # Vérifications de base
            if hasattr(discount, 'active') and not discount.active:
                is_eligible = False
                reasons.append('La remise n\'est pas active')
            
            if hasattr(discount, 'start_date') and discount.start_date:
                from datetime import date
                if discount.start_date > date.today():
                    is_eligible = False
                    reasons.append('La remise n\'est pas encore disponible')
            
            if hasattr(discount, 'end_date') and discount.end_date:
                from datetime import date
                if discount.end_date < date.today():
                    is_eligible = False
                    reasons.append('La remise a expiré')
            
            if hasattr(discount, 'max_usage') and hasattr(discount, 'current_usage'):
                if discount.max_usage > 0 and discount.current_usage >= discount.max_usage:
                    is_eligible = False
                    reasons.append('Le nombre maximum d\'utilisations a été atteint')
            
            # Vérification personnalisée si disponible
            if hasattr(discount, 'is_eligible_student'):
                custom_eligible, custom_reasons = discount.is_eligible_student(student)
                if not custom_eligible:
                    is_eligible = False
                    reasons.extend(custom_reasons)
            
            return {
                'success': True,
                'data': {
                    'is_eligible': is_eligible,
                    'reasons': reasons,
                    'discount_name': discount.name,
                    'student_name': student.name,
                    'discount_amount': discount.amount if hasattr(discount, 'amount') else 0,
                    'discount_percentage': discount.percentage if hasattr(discount, 'percentage') else 0,
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la validation de l'éligibilité: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/discounts/statistics', type='json', auth='user', methods=['POST'], csrf=False)
    def get_discount_statistics(self, **kwargs):
        """Récupère les statistiques des remises"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            if kwargs.get('date_from'):
                domain.append(('start_date', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('end_date', '<=', kwargs['date_to']))
            
            discounts = request.env['edu.discount'].search(domain)
            
            # Calculs des statistiques
            total_discounts = len(discounts)
            active_discounts = len(discounts.filtered(lambda d: d.active if hasattr(d, 'active') else True))
            
            # Statistiques par type
            by_type = {}
            for discount in discounts:
                discount_type = discount.discount_type if hasattr(discount, 'discount_type') else 'other'
                if discount_type not in by_type:
                    by_type[discount_type] = {'count': 0, 'total_amount': 0, 'total_usage': 0}
                by_type[discount_type]['count'] += 1
                if hasattr(discount, 'current_usage'):
                    by_type[discount_type]['total_usage'] += discount.current_usage
            
            # Calcul du montant total de remises accordées
            total_discounted = 0
            if request.env['edu.discount.usage'].search([]):  # Si le modèle existe
                usage_records = request.env['edu.discount.usage'].search([
                    ('discount_id', 'in', discounts.ids)
                ])
                total_discounted = sum(usage_records.mapped('amount_discounted'))
            
            data = {
                'total_discounts': total_discounts,
                'active_discounts': active_discounts,
                'inactive_discounts': total_discounts - active_discounts,
                'by_type': by_type,
                'total_discounted_amount': total_discounted,
                'average_discount_usage': sum(d.current_usage for d in discounts if hasattr(d, 'current_usage')) / total_discounts if total_discounts > 0 else 0,
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
