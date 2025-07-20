# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)

class StudentBehaviorController(http.Controller):
    """API Controller pour StudentBehaviorRecord"""

    @http.route('/api/behavior-records', type='json', auth='user', methods=['POST'], csrf=False)
    def get_behavior_records(self, **kwargs):
        """Récupérer la liste des enregistrements comportementaux"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', int(kwargs['student_id'])))
            
            if kwargs.get('type'):
                domain.append(('type', '=', kwargs['type']))
            
            if kwargs.get('category_id'):
                domain.append(('category_id', '=', int(kwargs['category_id'])))
            
            if kwargs.get('date_from'):
                domain.append(('date', '>=', kwargs['date_from']))
            
            if kwargs.get('date_to'):
                domain.append(('date', '<=', kwargs['date_to']))
            
            # Pagination
            limit = int(kwargs.get('limit', 20))
            offset = int(kwargs.get('offset', 0))
            
            records = request.env['student.behavior.record'].search(domain, limit=limit, offset=offset)
            total_count = request.env['student.behavior.record'].search_count(domain)
            
            data = []
            for record in records:
                data.append({
                    'id': record.id,
                    'name': record.name,
                    'student_id': record.student_id.id,
                    'student_name': record.student_id.name,
                    'date': record.date.isoformat() if record.date else None,
                    'type': record.type,
                    'category_id': record.category_id.id if record.category_id else None,
                    'category_name': record.category_id.name if record.category_id else None,
                    'points': record.points,
                    'description': record.description,
                    'teacher_id': record.teacher_id.id if record.teacher_id else None,
                    'teacher_name': record.teacher_id.name if record.teacher_id else None,
                    'location': record.location,
                    'state': record.state
                })
            
            return {
                'success': True,
                'data': data,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des enregistrements: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/behavior-records/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_behavior_record(self, **kwargs):
        """Récupérer les détails d'un enregistrement comportemental"""
        try:
            record_id = kwargs.get('record_id')
            if not record_id:
                return {'success': False, 'error': 'Le paramètre record_id est requis'}
            record = request.env['student.behavior.record'].browse(record_id)
            if not record.exists():
                return {'success': False, 'error': 'Enregistrement non trouvé'}
            
            return {
                'success': True,
                'data': {
                    'id': record.id,
                    'name': record.name,
                    'student_id': record.student_id.id,
                    'student_name': record.student_id.name,
                    'date': record.date.isoformat() if record.date else None,
                    'type': record.type,
                    'category_id': record.category_id.id if record.category_id else None,
                    'category_name': record.category_id.name if record.category_id else None,
                    'points': record.points,
                    'description': record.description,
                    'teacher_id': record.teacher_id.id if record.teacher_id else None,
                    'teacher_name': record.teacher_id.name if record.teacher_id else None,
                    'location': record.location,
                    'witnesses': record.witnesses,
                    'actions_taken': record.actions_taken,
                    'followup_notes': record.followup_notes,
                    'state': record.state
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de l'enregistrement {record_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/behavior-records/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_behavior_record(self, **kwargs):
        """Créer un nouvel enregistrement comportemental"""
        try:
            # Validation des données requises
            required_fields = ['student_id', 'type', 'description']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Le champ {field} est requis'}
            
            # Préparer les données
            data = {
                'student_id': int(kwargs['student_id']),
                'date': kwargs.get('date'),
                'type': kwargs['type'],
                'category_id': int(kwargs['category_id']) if kwargs.get('category_id') else None,
                'points': int(kwargs.get('points', 0)),
                'description': kwargs['description'],
                'teacher_id': int(kwargs['teacher_id']) if kwargs.get('teacher_id') else None,
                'location': kwargs.get('location'),
                'witnesses': kwargs.get('witnesses'),
                'actions_taken': kwargs.get('actions_taken'),
                'followup_notes': kwargs.get('followup_notes')
            }
            
            record = request.env['student.behavior.record'].create(data)
            
            return {
                'success': True,
                'message': 'Enregistrement comportemental créé avec succès',
                'data': {
                    'id': record.id,
                    'name': record.name,
                    'type': record.type
                }
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la création de l'enregistrement: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/behavior-records/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_behavior_record(self, **kwargs):
        """Mettre à jour un enregistrement comportemental"""
        try:
            record_id = kwargs.get('record_id')
            if not record_id:
                return {'success': False, 'error': 'Le paramètre record_id est requis'}
            record = request.env['student.behavior.record'].browse(record_id)
            if not record.exists():
                return {'success': False, 'error': 'Enregistrement non trouvé'}
            
            # Préparer les données de mise à jour
            update_data = {}
            allowed_fields = [
                'date', 'type', 'category_id', 'points', 'description', 'teacher_id',
                'location', 'witnesses', 'actions_taken', 'followup_notes', 'state'
            ]
            
            for field in allowed_fields:
                if field in kwargs:
                    if field in ['category_id', 'teacher_id'] and kwargs[field]:
                        update_data[field] = int(kwargs[field])
                    else:
                        update_data[field] = kwargs[field]
            
            if update_data:
                record.write(update_data)
            
            return {
                'success': True,
                'message': 'Enregistrement mis à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour de l'enregistrement: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/behavior-records/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_behavior_record(self, **kwargs):
        """Supprimer un enregistrement comportemental"""
        try:
            record_id = kwargs.get('record_id')
            if not record_id:
                return {'success': False, 'error': 'Le paramètre record_id est requis'}
            record = request.env['student.behavior.record'].browse(record_id)
            if not record.exists():
                return {'success': False, 'error': 'Enregistrement non trouvé'}
            
            name = record.name
            record.unlink()
            
            return {
                'success': True,
                'message': f'Enregistrement {name} supprimé avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression de l'enregistrement: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/behavior-records/confirm', type='json', auth='user', methods=['POST'], csrf=False)
    def confirm_behavior_record(self, **kwargs):
        """Confirmer un enregistrement comportemental"""
        try:
            record_id = kwargs.get('record_id')
            if not record_id:
                return {'success': False, 'error': 'Le paramètre record_id est requis'}
            record = request.env['student.behavior.record'].browse(record_id)
            if not record.exists():
                return {'success': False, 'error': 'Enregistrement non trouvé'}
            
            record.action_confirm()
            
            return {
                'success': True,
                'message': 'Enregistrement confirmé avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la confirmation: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/students/behavior-summary', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_behavior_summary(self, **kwargs):
        """Récupérer le résumé comportemental d'un élève"""
        try:
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'Le paramètre student_id est requis'}
            student = request.env['op.student'].browse(student_id)
            if not student.exists():
                return {'success': False, 'error': 'Élève non trouvé'}
            
            # Statistiques générales
            total_records = len(student.behavior_records_ids)
            rewards = student.behavior_records_ids.filtered(lambda r: r.type == 'reward')
            sanctions = student.behavior_records_ids.filtered(lambda r: r.type == 'sanction')
            
            # Évolution mensuelle
            monthly_stats = {}
            for record in student.behavior_records_ids:
                if record.date:
                    month_key = record.date.strftime('%Y-%m')
                    if month_key not in monthly_stats:
                        monthly_stats[month_key] = {'rewards': 0, 'sanctions': 0, 'points': 0}
                    
                    if record.type == 'reward':
                        monthly_stats[month_key]['rewards'] += 1
                    else:
                        monthly_stats[month_key]['sanctions'] += 1
                    
                    monthly_stats[month_key]['points'] += record.points
            
            return {
                'success': True,
                'data': {
                    'student_id': student_id,
                    'student_name': student.name,
                    'total_records': total_records,
                    'total_rewards': len(rewards),
                    'total_sanctions': len(sanctions),
                    'total_points': student.behavior_score,
                    'behavior_trend': student.behavior_trend,
                    'monthly_stats': monthly_stats
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du résumé: {str(e)}")
            return {'success': False, 'error': str(e)}


class StudentBehaviorCategoryController(http.Controller):
    """API Controller pour StudentBehaviorCategory"""

    @http.route('/api/behavior-categories', type='json', auth='user', methods=['POST'], csrf=False)
    def get_behavior_categories(self, **kwargs):
        """Récupérer la liste des catégories comportementales"""
        try:
            domain = []
            
            if kwargs.get('type'):
                domain.append(('type', '=', kwargs['type']))
            
            categories = request.env['student.behavior.category'].search(domain, order='sequence, name')
            
            data = []
            for category in categories:
                data.append({
                    'id': category.id,
                    'name': category.name,
                    'code': category.code,
                    'type': category.type,
                    'points': category.points,
                    'sequence': category.sequence,
                    'description': category.description,
                    'active': category.active,
                    'record_count': category.record_count
                })
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des catégories: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/behavior-categories/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_behavior_category(self, **kwargs):
        """Créer une nouvelle catégorie comportementale"""
        try:
            # Validation des données requises
            required_fields = ['name', 'type']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Le champ {field} est requis'}
            
            data = {
                'name': kwargs['name'],
                'code': kwargs.get('code'),
                'type': kwargs['type'],
                'points': int(kwargs.get('points', 0)),
                'sequence': int(kwargs.get('sequence', 10)),
                'description': kwargs.get('description')
            }
            
            category = request.env['student.behavior.category'].create(data)
            
            return {
                'success': True,
                'message': 'Catégorie créée avec succès',
                'data': {
                    'id': category.id,
                    'name': category.name,
                    'type': category.type
                }
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la catégorie: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/behavior-categories/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_behavior_category(self, **kwargs):
        """Mettre à jour une catégorie comportementale"""
        try:
            category_id = kwargs.get('category_id')
            if not category_id:
                return {'success': False, 'error': 'Le paramètre category_id est requis'}
            category = request.env['student.behavior.category'].browse(category_id)
            if not category.exists():
                return {'success': False, 'error': 'Catégorie non trouvée'}
            
            # Préparer les données de mise à jour
            update_data = {}
            allowed_fields = ['name', 'code', 'type', 'points', 'sequence', 'description', 'active']
            
            for field in allowed_fields:
                if field in kwargs:
                    if field in ['points', 'sequence']:
                        update_data[field] = int(kwargs[field])
                    else:
                        update_data[field] = kwargs[field]
            
            if update_data:
                category.write(update_data)
            
            return {
                'success': True,
                'message': 'Catégorie mise à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour de la catégorie: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/behavior-categories/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_behavior_category(self, **kwargs):
        """Supprimer une catégorie comportementale"""
        try:
            category_id = kwargs.get('category_id')
            if not category_id:
                return {'success': False, 'error': 'Le paramètre category_id est requis'}
            category = request.env['student.behavior.category'].browse(category_id)
            if not category.exists():
                return {'success': False, 'error': 'Catégorie non trouvée'}
            
            # Vérifier s'il y a des enregistrements liés
            if category.record_count > 0:
                return {
                    'success': False, 
                    'error': f'Impossible de supprimer: {category.record_count} enregistrements utilisent cette catégorie'
                }
            
            name = category.name
            category.unlink()
            
            return {
                'success': True,
                'message': f'Catégorie {name} supprimée avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression de la catégorie: {str(e)}")
            return {'success': False, 'error': str(e)} 