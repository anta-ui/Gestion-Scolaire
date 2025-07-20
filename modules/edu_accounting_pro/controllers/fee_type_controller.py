# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduFeeTypeController(http.Controller):
    """Controller pour la gestion des types de frais"""

    @http.route('/api/fee-types', type='json', auth='user', methods=['POST'], csrf=False)
    def get_fee_types(self, **kwargs):
        """Récupère la liste des types de frais"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
            if kwargs.get('category_id'):
                domain.append(('category_id', '=', kwargs['category_id']))
            if kwargs.get('fee_nature'):
                domain.append(('fee_nature', '=', kwargs['fee_nature']))
            
            # Recherche par nom
            if kwargs.get('search'):
                domain.append(('name', 'ilike', kwargs['search']))
            
            # Pagination
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            fee_types = request.env['edu.fee.type'].search(domain, limit=limit, offset=offset)
            
            result = []
            for fee_type in fee_types:
                result.append({
                    'id': fee_type.id,
                    'name': fee_type.name,
                    'code': fee_type.code,
                    'description': fee_type.description or '',
                    'category_id': fee_type.category_id.id if fee_type.category_id else None,
                    'category_name': fee_type.category_id.name if fee_type.category_id else '',
                    'fee_nature': fee_type.fee_nature,
                    'fee_type': fee_type.fee_type,
                    'default_amount': fee_type.default_amount,
                    'is_mandatory': fee_type.is_mandatory,
                    'is_refundable': fee_type.is_refundable,
                    'allow_discount': fee_type.allow_discount,
                    'account_id': fee_type.account_id.id if fee_type.account_id else None,
                    'account_name': fee_type.account_id.name if fee_type.account_id else '',
                    'tax_ids': fee_type.tax_ids.ids,
                    'active': fee_type.active,
                    'currency_symbol': fee_type.currency_id.symbol if fee_type.currency_id else '',
                })
            
            total_count = request.env['edu.fee.type'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des types de frais: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-types/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_fee_type(self, **kwargs):
        """Récupère un type de frais spécifique"""
        try:
            fee_type_id = kwargs.get('fee_type_id')
            if not fee_type_id:
                return {'success': False, 'error': 'ID de type de frais requis'}
            
            fee_type = request.env['edu.fee.type'].browse(fee_type_id)
            
            if not fee_type.exists():
                return {'success': False, 'error': 'Type de frais non trouvé'}
            
            data = {
                'id': fee_type.id,
                'name': fee_type.name,
                'code': fee_type.code,
                'description': fee_type.description or '',
                'category_id': fee_type.category_id.id if fee_type.category_id else None,
                'category_name': fee_type.category_id.name if fee_type.category_id else '',
                'fee_nature': fee_type.fee_nature,
                'fee_type': fee_type.fee_type,
                'default_amount': fee_type.default_amount,
                'is_mandatory': fee_type.is_mandatory,
                'is_refundable': fee_type.is_refundable,
                'allow_discount': fee_type.allow_discount,
                'allow_installment': fee_type.allow_installment,
                'maximum_installments': fee_type.maximum_installments,
                'late_fee_applicable': fee_type.late_fee_applicable,
                'late_fee_amount': fee_type.late_fee_amount,
                'late_fee_type': fee_type.late_fee_type,
                'grace_period_days': fee_type.grace_period_days,
                'account_id': fee_type.account_id.id if fee_type.account_id else None,
                'account_name': fee_type.account_id.name if fee_type.account_id else '',
                'account_code': fee_type.account_id.code if fee_type.account_id else '',
                'tax_ids': fee_type.tax_ids.ids,
                'currency_id': fee_type.currency_id.id if fee_type.currency_id else None,
                'currency_symbol': fee_type.currency_id.symbol if fee_type.currency_id else '',
                'active': fee_type.active,
                'academic_year_ids': fee_type.academic_year_ids.ids,
                'course_ids': fee_type.course_ids.ids,
                'sequence': fee_type.sequence,
                'notes': fee_type.notes or '',
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du type de frais: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-types/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_fee_type(self, **kwargs):
        """Crée un nouveau type de frais"""
        try:
            # Validation des champs requis
            required_fields = ['name', 'code', 'fee_nature']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Champ requis manquant: {field}'}
            
            # Préparation des données
            vals = {
                'name': kwargs['name'],
                'code': kwargs['code'],
                'fee_nature': kwargs['fee_nature'],
            }
            
            # Champs optionnels
            optional_fields = [
                'description', 'category_id', 'fee_type', 'default_amount',
                'is_mandatory', 'is_refundable', 'allow_discount', 'allow_installment',
                'maximum_installments', 'late_fee_applicable', 'late_fee_amount',
                'late_fee_type', 'grace_period_days', 'account_id', 'currency_id',
                'active', 'sequence', 'notes'
            ]
            
            for field in optional_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Relations Many2many
            if kwargs.get('tax_ids'):
                vals['tax_ids'] = [(6, 0, kwargs['tax_ids'])]
            if kwargs.get('academic_year_ids'):
                vals['academic_year_ids'] = [(6, 0, kwargs['academic_year_ids'])]
            if kwargs.get('course_ids'):
                vals['course_ids'] = [(6, 0, kwargs['course_ids'])]
            
            # Création du type de frais
            fee_type = request.env['edu.fee.type'].create(vals)
            
            return {
                'success': True,
                'data': {
                    'id': fee_type.id,
                    'name': fee_type.name,
                    'code': fee_type.code
                },
                'message': 'Type de frais créé avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la création du type de frais: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-types/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_fee_type(self, **kwargs):
        """Met à jour un type de frais"""
        try:
            fee_type_id = kwargs.get('fee_type_id')
            if not fee_type_id:
                return {'success': False, 'error': 'ID de type de frais requis'}
            
            fee_type = request.env['edu.fee.type'].browse(fee_type_id)
            
            if not fee_type.exists():
                return {'success': False, 'error': 'Type de frais non trouvé'}
            
            # Préparation des données à mettre à jour
            vals = {}
            updatable_fields = [
                'name', 'code', 'description', 'category_id', 'fee_nature', 'fee_type',
                'default_amount', 'is_mandatory', 'is_refundable', 'allow_discount',
                'allow_installment', 'maximum_installments', 'late_fee_applicable',
                'late_fee_amount', 'late_fee_type', 'grace_period_days', 'account_id',
                'active', 'sequence', 'notes'
            ]
            
            for field in updatable_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Relations Many2many
            if kwargs.get('tax_ids') is not None:
                vals['tax_ids'] = [(6, 0, kwargs['tax_ids'])]
            if kwargs.get('academic_year_ids') is not None:
                vals['academic_year_ids'] = [(6, 0, kwargs['academic_year_ids'])]
            if kwargs.get('course_ids') is not None:
                vals['course_ids'] = [(6, 0, kwargs['course_ids'])]
            
            # Mise à jour
            fee_type.write(vals)
            
            return {
                'success': True,
                'message': 'Type de frais mis à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-types/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_fee_type(self, **kwargs):
        """Supprime un type de frais"""
        try:
            fee_type_id = kwargs.get('fee_type_id')
            if not fee_type_id:
                return {'success': False, 'error': 'ID de type de frais requis'}
            
            fee_type = request.env['edu.fee.type'].browse(fee_type_id)
            
            if not fee_type.exists():
                return {'success': False, 'error': 'Type de frais non trouvé'}
            
            # Vérification si le type peut être supprimé
            # Vérifier s'il est utilisé dans des structures de frais
            structure_lines = request.env['edu.fee.structure.line'].search([('fee_type_id', '=', fee_type.id)])
            if structure_lines:
                return {
                    'success': False,
                    'error': 'Impossible de supprimer un type de frais utilisé dans des structures'
                }
            
            # Vérifier s'il est utilisé dans des factures
            invoice_lines = request.env['edu.student.invoice.line'].search([('fee_type_id', '=', fee_type.id)])
            if invoice_lines:
                return {
                    'success': False,
                    'error': 'Impossible de supprimer un type de frais utilisé dans des factures'
                }
            
            fee_type_name = fee_type.name
            fee_type.unlink()
            
            return {
                'success': True,
                'message': f'Type de frais "{fee_type_name}" supprimé avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-types/categories', type='json', auth='user', methods=['POST'], csrf=False)
    def get_fee_categories(self, **kwargs):
        """Récupère les catégories de frais disponibles"""
        try:
            domain = []
            
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
            
            categories = request.env['edu.fee.category'].search(domain)
            
            result = []
            for category in categories:
                result.append({
                    'id': category.id,
                    'name': category.name,
                    'code': category.code if hasattr(category, 'code') else '',
                    'description': category.description if hasattr(category, 'description') else '',
                    'color': category.color if hasattr(category, 'color') else 0,
                    'sequence': category.sequence if hasattr(category, 'sequence') else 10,
                    'active': category.active if hasattr(category, 'active') else True,
                })
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des catégories: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-types/statistics', type='json', auth='user', methods=['POST'], csrf=False)
    def get_fee_type_statistics(self, **kwargs):
        """Récupère les statistiques des types de frais"""
        try:
            fee_type_id = kwargs.get('fee_type_id')
            
            if fee_type_id:
                # Statistiques pour un type spécifique
                fee_type = request.env['edu.fee.type'].browse(fee_type_id)
                if not fee_type.exists():
                    return {'success': False, 'error': 'Type de frais non trouvé'}
                
                # Compter les utilisations
                structure_count = request.env['edu.fee.structure.line'].search_count([('fee_type_id', '=', fee_type.id)])
                invoice_count = request.env['edu.student.invoice.line'].search_count([('fee_type_id', '=', fee_type.id)])
                
                # Calculer le montant total facturé
                invoice_lines = request.env['edu.student.invoice.line'].search([('fee_type_id', '=', fee_type.id)])
                total_amount = sum(line.price_total for line in invoice_lines)
                
                data = {
                    'fee_type_id': fee_type.id,
                    'fee_type_name': fee_type.name,
                    'structure_usage_count': structure_count,
                    'invoice_usage_count': invoice_count,
                    'total_invoiced_amount': total_amount,
                    'currency_symbol': fee_type.currency_id.symbol if fee_type.currency_id else '',
                }
            else:
                # Statistiques globales
                total_fee_types = request.env['edu.fee.type'].search_count([])
                active_fee_types = request.env['edu.fee.type'].search_count([('active', '=', True)])
                mandatory_fee_types = request.env['edu.fee.type'].search_count([('is_mandatory', '=', True)])
                
                data = {
                    'total_fee_types': total_fee_types,
                    'active_fee_types': active_fee_types,
                    'inactive_fee_types': total_fee_types - active_fee_types,
                    'mandatory_fee_types': mandatory_fee_types,
                    'optional_fee_types': total_fee_types - mandatory_fee_types,
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
