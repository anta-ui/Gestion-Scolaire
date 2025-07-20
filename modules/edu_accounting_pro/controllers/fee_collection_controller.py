# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduFeeCollectionController(http.Controller):
    """Controller pour la gestion de la collecte des frais"""

    @http.route('/api/fee-collections', type='json', auth='user', methods=['POST'], csrf=False)
    def get_fee_collections(self, **kwargs):
        """Récupère la liste des collectes de frais"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            if kwargs.get('course_id'):
                domain.append(('course_id', '=', kwargs['course_id']))
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            
            # Recherche par nom
            if kwargs.get('search'):
                domain.append('|', ('name', 'ilike', kwargs['search']), ('reference', 'ilike', kwargs['search']))
            
            # Pagination
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            collections = request.env['edu.fee.collection'].search(domain, limit=limit, offset=offset)
            
            result = []
            for collection in collections:
                result.append({
                    'id': collection.id,
                    'name': collection.name,
                    'reference': collection.reference if hasattr(collection, 'reference') else '',
                    'academic_year_name': collection.academic_year_id.name if hasattr(collection, 'academic_year_id') and collection.academic_year_id else '',
                    'course_name': collection.course_id.name if hasattr(collection, 'course_id') and collection.course_id else '',
                    'total_amount': collection.total_amount if hasattr(collection, 'total_amount') else 0,
                    'collected_amount': collection.collected_amount if hasattr(collection, 'collected_amount') else 0,
                    'state': collection.state if hasattr(collection, 'state') else 'draft',
                    'collection_date': collection.collection_date.isoformat() if hasattr(collection, 'collection_date') and collection.collection_date else None,
                    'currency_symbol': collection.currency_id.symbol if hasattr(collection, 'currency_id') and collection.currency_id else '',
                })
            
            total_count = request.env['edu.fee.collection'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des collectes de frais: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-collections/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_fee_collection(self, **kwargs):
        """Récupère une collecte de frais spécifique"""
        try:
            collection_id = kwargs.get('collection_id')
            if not collection_id:
                return {'success': False, 'error': 'ID de collecte requis'}
            
            collection = request.env['edu.fee.collection'].browse(collection_id)
            
            if not collection.exists():
                return {'success': False, 'error': 'Collecte non trouvée'}
            
            data = {
                'id': collection.id,
                'name': collection.name,
                'reference': collection.reference if hasattr(collection, 'reference') else '',
                'description': collection.description if hasattr(collection, 'description') else '',
                'academic_year_id': collection.academic_year_id.id if hasattr(collection, 'academic_year_id') and collection.academic_year_id else None,
                'academic_year_name': collection.academic_year_id.name if hasattr(collection, 'academic_year_id') and collection.academic_year_id else '',
                'course_id': collection.course_id.id if hasattr(collection, 'course_id') and collection.course_id else None,
                'course_name': collection.course_id.name if hasattr(collection, 'course_id') and collection.course_id else '',
                'total_amount': collection.total_amount if hasattr(collection, 'total_amount') else 0,
                'collected_amount': collection.collected_amount if hasattr(collection, 'collected_amount') else 0,
                'collection_date': collection.collection_date.isoformat() if hasattr(collection, 'collection_date') and collection.collection_date else None,
                'due_date': collection.due_date.isoformat() if hasattr(collection, 'due_date') and collection.due_date else None,
                'state': collection.state if hasattr(collection, 'state') else 'draft',
                'active': collection.active if hasattr(collection, 'active') else True,
                'currency_symbol': collection.currency_id.symbol if hasattr(collection, 'currency_id') and collection.currency_id else '',
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la collecte: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/fee-collections/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_fee_collection(self, **kwargs):
        """Crée une nouvelle collecte de frais"""
        try:
            required_fields = ['name']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Champ requis: {field}'}
            
            vals = {
                'name': kwargs['name'],
            }
            
            optional_fields = ['reference', 'description', 'academic_year_id', 'course_id', 'collection_date', 'due_date', 'active']
            for field in optional_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            collection = request.env['edu.fee.collection'].create(vals)
            
            return {
                'success': True,
                'data': {'id': collection.id, 'name': collection.name},
                'message': 'Collecte créée avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la création: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/fee-collections/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_fee_collection(self, **kwargs):
        """Met à jour une collecte de frais"""
        try:
            collection_id = kwargs.get('collection_id')
            if not collection_id:
                return {'success': False, 'error': 'ID de collecte requis'}
            
            collection = request.env['edu.fee.collection'].browse(collection_id)
            if not collection.exists():
                return {'success': False, 'error': 'Collecte non trouvée'}
            
            vals = {}
            updatable_fields = ['name', 'description', 'academic_year_id', 'course_id', 'collection_date', 'due_date', 'active']
            for field in updatable_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            collection.write(vals)
            
            return {'success': True, 'message': 'Collecte mise à jour'}
            
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/fee-collections/start', type='json', auth='user', methods=['POST'], csrf=False)
    def start_collection(self, **kwargs):
        """Démarre une collecte de frais"""
        try:
            collection_id = kwargs.get('collection_id')
            if not collection_id:
                return {'success': False, 'error': 'ID de collecte requis'}
            
            collection = request.env['edu.fee.collection'].browse(collection_id)
            if not collection.exists():
                return {'success': False, 'error': 'Collecte non trouvée'}
            
            if hasattr(collection, 'action_start'):
                collection.action_start()
            else:
                collection.write({'state': 'active'})
            
            return {'success': True, 'message': 'Collecte démarrée avec succès'}
            
        except Exception as e:
            _logger.error(f"Erreur lors du démarrage: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/fee-collections/statistics', type='json', auth='user', methods=['POST'], csrf=False)
    def get_collection_statistics(self, **kwargs):
        """Récupère les statistiques des collectes"""
        try:
            domain = []
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            
            collections = request.env['edu.fee.collection'].search(domain)
            
            total_collections = len(collections)
            active_collections = len(collections.filtered(lambda c: c.state == 'active' if hasattr(c, 'state') else True))
            total_expected = sum(collections.mapped('total_amount')) if hasattr(collections, 'total_amount') else 0
            total_collected = sum(collections.mapped('collected_amount')) if hasattr(collections, 'collected_amount') else 0
            
            data = {
                'total_collections': total_collections,
                'active_collections': active_collections,
                'total_expected': total_expected,
                'total_collected': total_collected,
                'collection_rate': (total_collected / total_expected * 100) if total_expected > 0 else 0,
            }
            
            return {'success': True, 'data': data}
            
        except Exception as e:
            _logger.error(f"Erreur lors des statistiques: {str(e)}")
            return {'success': False, 'error': str(e)}
