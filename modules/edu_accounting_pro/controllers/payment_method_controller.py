# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduPaymentMethodController(http.Controller):
    """Controller pour la gestion des méthodes de paiement"""

    @http.route('/api/payment-methods', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payment_methods(self, **kwargs):
        """Récupère la liste des méthodes de paiement"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
            if kwargs.get('method_type'):
                domain.append(('method_type', '=', kwargs['method_type']))
            if kwargs.get('is_default') is not None:
                domain.append(('is_default', '=', kwargs['is_default']))
            
            # Recherche par nom
            if kwargs.get('search'):
                domain.append('|', ('name', 'ilike', kwargs['search']), ('code', 'ilike', kwargs['search']))
            
            # Pagination
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            payment_methods = request.env['edu.payment.method'].search(domain, limit=limit, offset=offset)
            
            result = []
            for method in payment_methods:
                result.append({
                    'id': method.id,
                    'name': method.name,
                    'code': method.code if hasattr(method, 'code') else '',
                    'description': method.description if hasattr(method, 'description') else '',
                    'method_type': method.method_type if hasattr(method, 'method_type') else '',
                    'method_type_display': dict(method._fields['method_type'].selection).get(method.method_type, '') if hasattr(method, 'method_type') else '',
                    'is_default': method.is_default if hasattr(method, 'is_default') else False,
                    'requires_reference': method.requires_reference if hasattr(method, 'requires_reference') else False,
                    'processing_fee': method.processing_fee if hasattr(method, 'processing_fee') else 0,
                    'fee_percentage': method.fee_percentage if hasattr(method, 'fee_percentage') else 0,
                    'sequence': method.sequence if hasattr(method, 'sequence') else 0,
                    'active': method.active if hasattr(method, 'active') else True,
                    'usage_count': method.usage_count if hasattr(method, 'usage_count') else 0,
                })
            
            total_count = request.env['edu.payment.method'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des méthodes de paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-methods/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payment_method(self, **kwargs):
        """Récupère une méthode de paiement spécifique"""
        try:
            method_id = kwargs.get('method_id')
            if not method_id:
                return {'success': False, 'error': 'ID de méthode de paiement requis'}
            
            method = request.env['edu.payment.method'].browse(method_id)
            
            if not method.exists():
                return {'success': False, 'error': 'Méthode de paiement non trouvée'}
            
            data = {
                'id': method.id,
                'name': method.name,
                'code': method.code if hasattr(method, 'code') else '',
                'description': method.description if hasattr(method, 'description') else '',
                'method_type': method.method_type if hasattr(method, 'method_type') else '',
                'is_default': method.is_default if hasattr(method, 'is_default') else False,
                'requires_reference': method.requires_reference if hasattr(method, 'requires_reference') else False,
                'requires_approval': method.requires_approval if hasattr(method, 'requires_approval') else False,
                'processing_fee': method.processing_fee if hasattr(method, 'processing_fee') else 0,
                'fee_percentage': method.fee_percentage if hasattr(method, 'fee_percentage') else 0,
                'min_amount': method.min_amount if hasattr(method, 'min_amount') else 0,
                'max_amount': method.max_amount if hasattr(method, 'max_amount') else 0,
                'instructions': method.instructions if hasattr(method, 'instructions') else '',
                'sequence': method.sequence if hasattr(method, 'sequence') else 0,
                'active': method.active if hasattr(method, 'active') else True,
                'usage_count': method.usage_count if hasattr(method, 'usage_count') else 0,
                'last_used': method.last_used.isoformat() if hasattr(method, 'last_used') and method.last_used else None,
                'account_id': method.account_id.id if hasattr(method, 'account_id') and method.account_id else None,
                'account_name': method.account_id.name if hasattr(method, 'account_id') and method.account_id else '',
                'journal_id': method.journal_id.id if hasattr(method, 'journal_id') and method.journal_id else None,
                'journal_name': method.journal_id.name if hasattr(method, 'journal_id') and method.journal_id else '',
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la méthode: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-methods/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_payment_method(self, **kwargs):
        """Crée une nouvelle méthode de paiement"""
        try:
            # Validation des champs requis
            required_fields = ['name', 'method_type']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Champ requis manquant: {field}'}
            
            # Préparation des données
            vals = {
                'name': kwargs['name'],
                'method_type': kwargs['method_type'],
            }
            
            # Champs optionnels
            optional_fields = [
                'code', 'description', 'is_default', 'requires_reference', 'requires_approval',
                'processing_fee', 'fee_percentage', 'min_amount', 'max_amount',
                'instructions', 'sequence', 'account_id', 'journal_id', 'active'
            ]
            
            for field in optional_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Validation des montants
            if vals.get('min_amount') and vals.get('max_amount'):
                if vals['min_amount'] > vals['max_amount']:
                    return {'success': False, 'error': 'Le montant minimum ne peut pas être supérieur au maximum'}
            
            if vals.get('fee_percentage') and (vals['fee_percentage'] < 0 or vals['fee_percentage'] > 100):
                return {'success': False, 'error': 'Le pourcentage de frais doit être entre 0 et 100'}
            
            # Si cette méthode est définie par défaut, désactiver les autres
            if vals.get('is_default'):
                request.env['edu.payment.method'].search([('is_default', '=', True)]).write({'is_default': False})
            
            # Création de la méthode de paiement
            method = request.env['edu.payment.method'].create(vals)
            
            return {
                'success': True,
                'data': {
                    'id': method.id,
                    'name': method.name,
                    'code': method.code if hasattr(method, 'code') else ''
                },
                'message': 'Méthode de paiement créée avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la création: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-methods/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_payment_method(self, **kwargs):
        """Met à jour une méthode de paiement"""
        try:
            method_id = kwargs.get('method_id')
            if not method_id:
                return {'success': False, 'error': 'ID de méthode de paiement requis'}
            
            method = request.env['edu.payment.method'].browse(method_id)
            
            if not method.exists():
                return {'success': False, 'error': 'Méthode de paiement non trouvée'}
            
            # Préparation des données à mettre à jour
            vals = {}
            updatable_fields = [
                'name', 'code', 'description', 'method_type', 'is_default',
                'requires_reference', 'requires_approval', 'processing_fee',
                'fee_percentage', 'min_amount', 'max_amount', 'instructions',
                'sequence', 'account_id', 'journal_id', 'active'
            ]
            
            for field in updatable_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Validation des montants
            final_min = vals.get('min_amount', method.min_amount if hasattr(method, 'min_amount') else 0)
            final_max = vals.get('max_amount', method.max_amount if hasattr(method, 'max_amount') else 0)
            
            if final_min and final_max and final_min > final_max:
                return {'success': False, 'error': 'Le montant minimum ne peut pas être supérieur au maximum'}
            
            if vals.get('fee_percentage') and (vals['fee_percentage'] < 0 or vals['fee_percentage'] > 100):
                return {'success': False, 'error': 'Le pourcentage de frais doit être entre 0 et 100'}
            
            # Si cette méthode est définie par défaut, désactiver les autres
            if vals.get('is_default'):
                request.env['edu.payment.method'].search([
                    ('is_default', '=', True), 
                    ('id', '!=', method.id)
                ]).write({'is_default': False})
            
            # Mise à jour
            method.write(vals)
            
            return {
                'success': True,
                'message': 'Méthode de paiement mise à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-methods/set-default', type='json', auth='user', methods=['POST'], csrf=False)
    def set_default_method(self, **kwargs):
        """Définit une méthode comme méthode par défaut"""
        try:
            method_id = kwargs.get('method_id')
            if not method_id:
                return {'success': False, 'error': 'ID de méthode de paiement requis'}
            
            method = request.env['edu.payment.method'].browse(method_id)
            
            if not method.exists():
                return {'success': False, 'error': 'Méthode de paiement non trouvée'}
            
            # Désactiver toutes les autres méthodes par défaut
            request.env['edu.payment.method'].search([
                ('is_default', '=', True)
            ]).write({'is_default': False})
            
            # Activer cette méthode comme défaut
            method.write({'is_default': True})
            
            return {
                'success': True,
                'message': f'"{method.name}" définie comme méthode par défaut'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la définition par défaut: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-methods/calculate-fees', type='json', auth='user', methods=['POST'], csrf=False)
    def calculate_fees(self, **kwargs):
        """Calcule les frais pour une méthode de paiement et un montant donnés"""
        try:
            method_id = kwargs.get('method_id')
            amount = kwargs.get('amount')
            
            if not method_id:
                return {'success': False, 'error': 'ID de méthode de paiement requis'}
            if not amount or amount <= 0:
                return {'success': False, 'error': 'Montant requis et positif'}
            
            method = request.env['edu.payment.method'].browse(method_id)
            
            if not method.exists():
                return {'success': False, 'error': 'Méthode de paiement non trouvée'}
            
            # Vérification des limites de montant
            if hasattr(method, 'min_amount') and method.min_amount and amount < method.min_amount:
                return {
                    'success': False, 
                    'error': f'Le montant minimum pour cette méthode est {method.min_amount}'
                }
            
            if hasattr(method, 'max_amount') and method.max_amount and amount > method.max_amount:
                return {
                    'success': False, 
                    'error': f'Le montant maximum pour cette méthode est {method.max_amount}'
                }
            
            # Calcul des frais
            processing_fee = method.processing_fee if hasattr(method, 'processing_fee') else 0
            fee_percentage = method.fee_percentage if hasattr(method, 'fee_percentage') else 0
            
            percentage_fee = amount * (fee_percentage / 100)
            total_fees = processing_fee + percentage_fee
            final_amount = amount + total_fees
            
            data = {
                'method_name': method.name,
                'original_amount': amount,
                'processing_fee': processing_fee,
                'percentage_fee': percentage_fee,
                'fee_percentage': fee_percentage,
                'total_fees': total_fees,
                'final_amount': final_amount,
                'currency_symbol': method.currency_id.symbol if hasattr(method, 'currency_id') and method.currency_id else '',
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors du calcul des frais: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/payment-methods/statistics', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payment_method_statistics(self, **kwargs):
        """Récupère les statistiques des méthodes de paiement"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('date_from'):
                domain.append(('create_date', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('create_date', '<=', kwargs['date_to']))
            
            methods = request.env['edu.payment.method'].search(domain)
            
            # Calculs des statistiques
            total_methods = len(methods)
            active_methods = len(methods.filtered(lambda m: m.active if hasattr(m, 'active') else True))
            default_method = methods.filtered(lambda m: m.is_default if hasattr(m, 'is_default') else False)
            
            # Statistiques par type
            by_type = {}
            for method in methods:
                method_type = method.method_type if hasattr(method, 'method_type') else 'other'
                if method_type not in by_type:
                    by_type[method_type] = {'count': 0, 'total_usage': 0}
                by_type[method_type]['count'] += 1
                if hasattr(method, 'usage_count'):
                    by_type[method_type]['total_usage'] += method.usage_count
            
            # Méthode la plus utilisée
            most_used_method = max(methods, key=lambda m: m.usage_count if hasattr(m, 'usage_count') else 0) if methods else None
            
            data = {
                'total_methods': total_methods,
                'active_methods': active_methods,
                'inactive_methods': total_methods - active_methods,
                'default_method_name': default_method.name if default_method else 'Aucune',
                'by_type': by_type,
                'most_used_method': {
                    'name': most_used_method.name if most_used_method else '',
                    'usage_count': most_used_method.usage_count if most_used_method and hasattr(most_used_method, 'usage_count') else 0
                },
                'total_usage': sum(methods.mapped('usage_count')) if hasattr(methods, 'usage_count') else 0,
                'average_usage': sum(methods.mapped('usage_count')) / total_methods if total_methods > 0 and hasattr(methods, 'usage_count') else 0,
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
