# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduFeeStructureController(http.Controller):
    """Controller pour la gestion des structures de frais"""

    @http.route('/api/fee-structures', type='json', auth='user', methods=['POST'], csrf=False)
    def get_fee_structures(self, **kwargs):
        """Récupère la liste des structures de frais"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            if kwargs.get('course_id'):
                domain.append(('course_id', '=', kwargs['course_id']))
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
            
            # Pagination
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            structures = request.env['edu.fee.structure'].search(domain, limit=limit, offset=offset)
            
            result = []
            for structure in structures:
                result.append({
                    'id': structure.id,
                    'name': structure.name,
                    'code': structure.code,
                    'academic_year_id': structure.academic_year_id.id if structure.academic_year_id else None,
                    'academic_year_name': structure.academic_year_id.name if structure.academic_year_id else '',
                    'course_id': structure.course_id.id if structure.course_id else None,
                    'course_name': structure.course_id.name if structure.course_id else '',
                    'batch_id': structure.batch_id.id if structure.batch_id else None,
                    'batch_name': structure.batch_id.name if structure.batch_id else '',
                    'total_amount': structure.total_amount,
                    'mandatory_amount': structure.mandatory_amount,
                    'optional_amount': structure.optional_amount,
                    'billing_type': structure.billing_type,
                    'date_start': structure.date_start.isoformat() if structure.date_start else None,
                    'date_end': structure.date_end.isoformat() if structure.date_end else None,
                    'active': structure.active,
                    'currency_symbol': structure.currency_id.symbol if structure.currency_id else '',
                })
            
            total_count = request.env['edu.fee.structure'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des structures de frais: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-structures/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_fee_structure(self, **kwargs):
        """Récupère une structure de frais spécifique"""
        try:
            structure_id = kwargs.get('structure_id')
            if not structure_id:
                return {'success': False, 'error': 'ID de structure requis'}
            
            structure = request.env['edu.fee.structure'].browse(structure_id)
            
            if not structure.exists():
                return {'success': False, 'error': 'Structure non trouvée'}
            
            # Récupération des lignes de frais
            fee_lines = []
            for line in structure.fee_line_ids:
                fee_lines.append({
                    'id': line.id,
                    'sequence': line.sequence,
                    'fee_type_id': line.fee_type_id.id if line.fee_type_id else None,
                    'fee_type_name': line.fee_type_id.name if line.fee_type_id else '',
                    'amount': line.amount,
                    'is_mandatory': line.is_mandatory,
                    'description': line.description or '',
                    'tax_ids': line.tax_ids.ids,
                })
            
            data = {
                'id': structure.id,
                'name': structure.name,
                'code': structure.code,
                'academic_year_id': structure.academic_year_id.id if structure.academic_year_id else None,
                'academic_year_name': structure.academic_year_id.name if structure.academic_year_id else '',
                'course_id': structure.course_id.id if structure.course_id else None,
                'course_name': structure.course_id.name if structure.course_id else '',
                'batch_id': structure.batch_id.id if structure.batch_id else None,
                'batch_name': structure.batch_id.name if structure.batch_id else '',
                'total_amount': structure.total_amount,
                'mandatory_amount': structure.mandatory_amount,
                'optional_amount': structure.optional_amount,
                'billing_type': structure.billing_type,
                'date_start': structure.date_start.isoformat() if structure.date_start else None,
                'date_end': structure.date_end.isoformat() if structure.date_end else None,
                'active': structure.active,
                'allow_partial_payment': structure.allow_partial_payment,
                'scholarship_applicable': structure.scholarship_applicable,
                'discount_applicable': structure.discount_applicable,
                'description': structure.description or '',
                'currency_id': structure.currency_id.id if structure.currency_id else None,
                'currency_symbol': structure.currency_id.symbol if structure.currency_id else '',
                'fee_lines': fee_lines,
                'invoice_count': structure.invoice_count,
                'student_count': structure.student_count,
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la structure: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-structures/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_fee_structure(self, **kwargs):
        """Crée une nouvelle structure de frais"""
        try:
            # Validation des champs requis
            required_fields = ['name', 'code', 'academic_year_id', 'course_id', 'billing_type']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Champ requis manquant: {field}'}
            
            # Préparation des données
            vals = {
                'name': kwargs['name'],
                'code': kwargs['code'],
                'academic_year_id': kwargs['academic_year_id'],
                'course_id': kwargs['course_id'],
                'billing_type': kwargs['billing_type'],
            }
            
            # Champs optionnels
            optional_fields = [
                'batch_id', 'date_start', 'date_end', 'active', 'currency_id',
                'allow_partial_payment', 'scholarship_applicable', 'discount_applicable',
                'description'
            ]
            
            for field in optional_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Création de la structure
            structure = request.env['edu.fee.structure'].create(vals)
            
            # Création des lignes de frais si fournies
            if kwargs.get('fee_lines'):
                for line_data in kwargs['fee_lines']:
                    line_vals = {
                        'fee_structure_id': structure.id,
                        'fee_type_id': line_data.get('fee_type_id'),
                        'amount': line_data.get('amount', 0.0),
                        'sequence': line_data.get('sequence', 10),
                        'is_mandatory': line_data.get('is_mandatory', True),
                        'description': line_data.get('description', ''),
                    }
                    if line_data.get('tax_ids'):
                        line_vals['tax_ids'] = [(6, 0, line_data['tax_ids'])]
                    
                    request.env['edu.fee.structure.line'].create(line_vals)
            
            return {
                'success': True,
                'data': {
                    'id': structure.id,
                    'name': structure.name,
                    'code': structure.code
                },
                'message': 'Structure de frais créée avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la structure: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-structures/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_fee_structure(self, **kwargs):
        """Met à jour une structure de frais"""
        try:
            structure_id = kwargs.get('structure_id')
            if not structure_id:
                return {'success': False, 'error': 'ID de structure requis'}
            
            structure = request.env['edu.fee.structure'].browse(structure_id)
            
            if not structure.exists():
                return {'success': False, 'error': 'Structure non trouvée'}
            
            # Préparation des données à mettre à jour
            vals = {}
            updatable_fields = [
                'name', 'code', 'academic_year_id', 'course_id', 'batch_id',
                'billing_type', 'date_start', 'date_end', 'active',
                'allow_partial_payment', 'scholarship_applicable', 'discount_applicable',
                'description'
            ]
            
            for field in updatable_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Mise à jour
            structure.write(vals)
            
            return {
                'success': True,
                'message': 'Structure mise à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-structures/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_fee_structure(self, **kwargs):
        """Supprime une structure de frais"""
        try:
            structure_id = kwargs.get('structure_id')
            if not structure_id:
                return {'success': False, 'error': 'ID de structure requis'}
            
            structure = request.env['edu.fee.structure'].browse(structure_id)
            
            if not structure.exists():
                return {'success': False, 'error': 'Structure non trouvée'}
            
            # Vérification si la structure peut être supprimée
            if structure.invoice_count > 0:
                return {
                    'success': False,
                    'error': 'Impossible de supprimer une structure ayant des factures associées'
                }
            
            structure_name = structure.name
            structure.unlink()
            
            return {
                'success': True,
                'message': f'Structure "{structure_name}" supprimée avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-structures/generate-invoices', type='json', auth='user', methods=['POST'], csrf=False)
    def generate_invoices(self, **kwargs):
        """Génère les factures pour une structure de frais"""
        try:
            structure_id = kwargs.get('structure_id')
            if not structure_id:
                return {'success': False, 'error': 'ID de structure requis'}
            
            structure = request.env['edu.fee.structure'].browse(structure_id)
            
            if not structure.exists():
                return {'success': False, 'error': 'Structure non trouvée'}
            
            # Génération des factures
            structure.action_generate_invoices()
            
            return {
                'success': True,
                'message': f'Factures générées pour la structure "{structure.name}"'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la génération des factures: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
