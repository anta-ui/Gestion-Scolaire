# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)

class StudentEnhancedController(http.Controller):
    """API Controller pour StudentEnhanced"""

    # Méthode dépréciée - Utiliser get_students en JSON
    # @http.route('/api/students', type='http', auth='user', methods=['GET'], csrf=False)

    @http.route('/api/students', type='json', auth='user', methods=['POST'], csrf=False)
    def get_students(self, **kwargs):
        """Récupérer la liste des élèves avec pagination (POST JSON)"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('class_id'):
                domain.append(('class_id', '=', int(kwargs['class_id'])))
            
            if kwargs.get('search'):
                search = kwargs['search']
                domain.append('|', ('name', 'ilike', search), ('unique_code', 'ilike', search))
            
            # Pagination
            limit = int(kwargs.get('limit', 20))
            offset = int(kwargs.get('offset', 0))
            
            students = request.env['op.student'].search(domain, limit=limit, offset=offset)
            total_count = request.env['op.student'].search_count(domain)
            
            data = []
            for student in students:
                data.append({
                    'id': student.id,
                    'name': student.name,
                    'unique_code': student.unique_code,
                    'email': student.email,
                    'mobile': student.mobile,
                    'behavior_score': student.behavior_score,
                    'risk_dropout': student.risk_dropout,
                    'performance_prediction': student.performance_prediction,
                    'has_medical_alerts': student.has_medical_alerts,
                    'engagement_score': student.engagement_score,
                    'qr_code': student.qr_code,
                })
            
            return {
                'success': True,
                'data': data,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des élèves: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/students/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_http(self, **kwargs):
        """Récupérer les détails d'un élève (GET)"""
        try:
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'Le paramètre student_id est requis'}
            student = request.env['op.student'].browse(student_id)
            if not student.exists():
                result = {'success': False, 'error': 'Élève non trouvé'}
            else:
                result = {
                    'success': True,
                    'data': {
                        'id': student.id,
                        'name': student.name,
                        'unique_code': student.unique_code,
                        'email': student.email,
                        'mobile': student.mobile,
                        'birth_date': student.birth_date.isoformat() if student.birth_date else None,
                        'gender': student.gender,
                        'blood_group': student.blood_group,
                        'nationality_text': student.nationality_text,
                        'religion_choice': student.religion_choice,
                        'languages_spoken': student.languages_spoken,
                        'special_needs': student.special_needs,
                        'behavior_score': student.behavior_score,
                        'behavior_trend': student.behavior_trend,
                        'risk_dropout': student.risk_dropout,
                        'performance_prediction': student.performance_prediction,
                        'engagement_score': student.engagement_score,
                        'has_medical_alerts': student.has_medical_alerts,
                        'medical_alerts_count': student.medical_alerts_count,
                        'rewards_count': student.rewards_count,
                        'sanctions_count': student.sanctions_count,
                        'transport_required': student.transport_required,
                        'bus_route': student.bus_route,
                        'pickup_time': student.pickup_time,
                        'dropoff_time': student.dropoff_time,
                        'last_activity_date': student.last_activity_date.isoformat() if student.last_activity_date else None,
                        'qr_code': student.qr_code,
                    }
                }
            
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de l'élève {student_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/students/details', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student(self, **kwargs):
        """Récupérer les détails d'un élève (POST JSON)"""
        try:
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'Le paramètre student_id est requis'}
            student = request.env['op.student'].browse(student_id)
            if not student.exists():
                return {'success': False, 'error': 'Élève non trouvé'}
            
            return {
                'success': True,
                'data': {
                    'id': student.id,
                    'name': student.name,
                    'unique_code': student.unique_code,
                    'email': student.email,
                    'mobile': student.mobile,
                    'birth_date': student.birth_date.isoformat() if student.birth_date else None,
                    'gender': student.gender,
                    'nationality': student.nationality,
                    'address': student.address_home,
                    'category_id': student.category_id.id if student.category_id else None,
                    'category_name': student.category_id.name if student.category_id else None,
                    'class_id': student.class_id.id if student.class_id else None,
                    'class_name': student.class_id.name if student.class_id else None,
                    'parent_ids': [{'id': p.id, 'name': p.name} for p in student.parent_ids],
                    'behavior_score': student.behavior_score,
                    'risk_dropout': student.risk_dropout,
                    'performance_prediction': student.performance_prediction,
                    'has_medical_alerts': student.has_medical_alerts,
                    'engagement_score': student.engagement_score,
                    'qr_code': student.qr_code,
                    'last_sync': student.last_sync.isoformat() if student.last_sync else None,
                    'digital_signature': student.digital_signature,
                    'predicted_graduation_date': student.predicted_graduation_date.isoformat() if student.predicted_graduation_date else None
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de l'élève {student_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/students/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_student(self, **kwargs):
        """Créer un nouvel élève"""
        try:
            # Validation des données requises
            required_fields = ['name', 'email']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Le champ {field} est requis'}
            
            # Préparer les données
            data = {
                'name': kwargs['name'],
                'email': kwargs['email'],
                'mobile': kwargs.get('mobile'),
                'birth_date': kwargs.get('birth_date'),
                'gender': kwargs.get('gender', 'male'),
                'blood_group': kwargs.get('blood_group', 'O+'),
                'nationality_text': kwargs.get('nationality_text', 'Sénégalaise'),
                'religion_choice': kwargs.get('religion_choice', 'non_renseigne'),
                'languages_spoken': kwargs.get('languages_spoken', 'Français, Wolof'),
                'special_needs': kwargs.get('special_needs'),
                'transport_required': kwargs.get('transport_required', False),
                'bus_route': kwargs.get('bus_route'),
            }
            
            student = request.env['op.student'].create(data)
            
            return {
                'success': True,
                'message': 'Élève créé avec succès',
                'data': {
                    'id': student.id,
                    'unique_code': student.unique_code,
                    'name': student.name,
                    'qr_code': student.qr_code
                }
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la création de l'élève: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/students/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_student(self, **kwargs):
        """Mettre à jour un élève"""
        try:
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'Le paramètre student_id est requis'}
            student = request.env['op.student'].browse(student_id)
            if not student.exists():
                return {'success': False, 'error': 'Élève non trouvé'}
            
            # Préparer les données de mise à jour
            update_data = {}
            allowed_fields = [
                'name', 'email', 'mobile', 'birth_date', 'gender', 'blood_group',
                'nationality_text', 'religion_choice', 'languages_spoken', 'special_needs',
                'transport_required', 'bus_route', 'pickup_time', 'dropoff_time'
            ]
            
            for field in allowed_fields:
                if field in kwargs:
                    update_data[field] = kwargs[field]
            
            if update_data:
                student.write(update_data)
                student.update_last_activity()
            
            return {
                'success': True,
                'message': 'Élève mis à jour avec succès',
                'data': {'id': student.id, 'name': student.name}
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour de l'élève {student_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/students/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_student(self, **kwargs):
        """Supprimer un élève"""
        try:
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'Le paramètre student_id est requis'}
            student = request.env['op.student'].browse(student_id)
            if not student.exists():
                return {'success': False, 'error': 'Élève non trouvé'}
            
            name = student.name
            student.unlink()
            
            return {
                'success': True,
                'message': f'Élève {name} supprimé avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression de l'élève {student_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/students/qr-code', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_qr_code_http(self, **kwargs):
        """Récupérer le QR Code d'un élève (GET)"""
        try:
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'Le paramètre student_id est requis'}
            student = request.env['op.student'].browse(student_id)
            if not student.exists():
                result = {'success': False, 'error': 'Élève non trouvé'}
            else:
                return {
                'success': True,
                'data': {
                    'qr_code': student.qr_code,
                    'student_id': student.id,
                    'student_name': student.name,
                    'unique_code': student.unique_code
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du QR Code: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/students/analytics', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_analytics_http(self, **kwargs):
        """Récupérer les données analytiques d'un élève (GET)"""
        try:
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'Le paramètre student_id est requis'}
            student = request.env['op.student'].browse(student_id)
            if not student.exists():
                result = {'success': False, 'error': 'Élève non trouvé'}
            else:
                return {
                'success': True,
                'data': {
                    'student_id': student.id,
                    'student_name': student.name,
                    'behavior_score': student.behavior_score,
                    'risk_dropout': student.risk_dropout,
                    'performance_prediction': student.performance_prediction,
                    'engagement_score': student.engagement_score,
                    'predicted_graduation_date': student.predicted_graduation_date.isoformat() if student.predicted_graduation_date else None,
                    'analytics_updated': student.last_sync.isoformat() if student.last_sync else None
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des analytics: {str(e)}")
            return {'success': False, 'error': str(e)}


class StudentCategoryController(http.Controller):
    """API Controller pour StudentCategory"""

    @http.route('/api/student-categories', type='json', auth='user', methods=['POST'], csrf=False)
    def get_categories_http(self, **kwargs):
        """Récupérer la liste des catégories d'élèves (GET)"""
        try:
            categories = request.env['student.category'].search([])
            
            data = []
            for category in categories:
                data.append({
                    'id': category.id,
                    'name': category.name,
                    'code': category.code,
                    'description': category.description,
                    'color': category.color,
                    'criteria': category.criteria,
                    'benefits': category.benefits,
                    'sequence': category.sequence,
                    'active': category.active,
                    'icon': category.icon,
                    'student_count': category.student_count
                })
            
            return {
                'success': True,
                'data': data,
                'total': len(data)
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des catégories: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/student-categories/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_category(self, **kwargs):
        """Créer une nouvelle catégorie d'élève"""
        try:
            # Validation des données requises
            required_fields = ['name', 'code']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Le champ {field} est requis'}
            
            data = {
                'name': kwargs['name'],
                'code': kwargs['code'],
                'description': kwargs.get('description'),
                'color': kwargs.get('color', 1),
                'criteria': kwargs.get('criteria'),
                'benefits': kwargs.get('benefits'),
                'sequence': kwargs.get('sequence', 10),
                'icon': kwargs.get('icon')
            }
            
            category = request.env['student.category'].create(data)
            
            return {
                'success': True,
                'message': 'Catégorie créée avec succès',
                'data': {
                    'id': category.id,
                    'name': category.name,
                    'code': category.code
                }
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la catégorie: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/student-categories/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_category(self, **kwargs):
        """Mettre à jour une catégorie"""
        try:
            category_id = kwargs.get('category_id')
            if not category_id:
                return {'success': False, 'error': 'Le paramètre category_id est requis'}
            category = request.env['student.category'].browse(category_id)
            if not category.exists():
                return {'success': False, 'error': 'Catégorie non trouvée'}
            
            # Préparer les données de mise à jour
            update_data = {}
            allowed_fields = ['name', 'code', 'description', 'color', 'criteria', 'benefits', 'sequence', 'icon', 'active']
            
            for field in allowed_fields:
                if field in kwargs:
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

    @http.route('/api/student-categories/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_category(self, **kwargs):
        """Supprimer une catégorie"""
        try:
            category_id = kwargs.get('category_id')
            if not category_id:
                return {'success': False, 'error': 'Le paramètre category_id est requis'}
            category = request.env['student.category'].browse(category_id)
            if not category.exists():
                return {'success': False, 'error': 'Catégorie non trouvée'}
            
            name = category.name
            category.unlink()
            
            return {
                'success': True,
                'message': f'Catégorie {name} supprimée avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression de la catégorie: {str(e)}")
            return {'success': False, 'error': str(e)} 