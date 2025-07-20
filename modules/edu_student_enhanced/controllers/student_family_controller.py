# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)

class StudentFamilyController(http.Controller):
    """API Controller pour StudentFamilyGroup"""

    @http.route('/api/family-groups', type='json', auth='user', methods=['POST'], csrf=False)
    def get_family_groups(self, **kwargs):
        """Récupérer la liste des groupes familiaux"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('search'):
                search = kwargs['search']
                domain.append('|', ('family_name', 'ilike', search), ('family_code', 'ilike', search))
            
            if kwargs.get('family_income'):
                domain.append(('family_income', '=', kwargs['family_income']))
            
            # Pagination
            limit = int(kwargs.get('limit', 20))
            offset = int(kwargs.get('offset', 0))
            
            family_groups = request.env['student.family.group'].search(domain, limit=limit, offset=offset)
            total_count = request.env['student.family.group'].search_count(domain)
            
            data = []
            for family in family_groups:
                data.append({
                    'id': family.id,
                    'family_name': family.family_name,
                    'family_code': family.family_code,
                    'home_address': family.home_address,
                    'home_phone': family.home_phone,
                    'family_income': family.family_income,
                    'family_size': family.family_size,
                    'children_count': family.children_count,
                    'housing_type': family.housing_type,
                    'emergency_contact_name': family.emergency_contact_name,
                    'emergency_contact_phone': family.emergency_contact_phone,
                    'emergency_contact_relation': family.emergency_contact_relation
                })
            
            return {
                'success': True,
                'data': data,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des groupes familiaux: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/family-groups/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_family_group(self, **kwargs):
        """Récupérer les détails d'un groupe familial"""
        try:
            family_id = kwargs.get('family_id')
            if not family_id:
                return {'success': False, 'error': 'Le paramètre family_id est requis'}
            family = request.env['student.family.group'].browse(family_id)
            if not family.exists():
                return {'success': False, 'error': 'Groupe familial non trouvé'}
            
            # Détails des enfants
            children_data = []
            for student in family.student_ids:
                children_data.append({
                    'id': student.id,
                    'name': student.name,
                    'unique_code': student.unique_code,
                    'birth_date': student.birth_date.isoformat() if student.birth_date else None,
                    'gender': student.gender,
                    'class_name': student.course_detail_ids[0].course_id.name if student.course_detail_ids else None
                })
            
            # Détails des parents
            parents_data = []
            for parent in family.parent_ids:
                parents_data.append({
                    'id': parent.id,
                    'name': parent.name,
                    'email': parent.email,
                    'mobile': parent.mobile,
                    'relation': getattr(parent, 'relation', None)
                })
            
            return {
                'success': True,
                'data': {
                    'id': family.id,
                    'family_name': family.family_name,
                    'family_code': family.family_code,
                    'home_address': family.home_address,
                    'home_phone': family.home_phone,
                    'family_income': family.family_income,
                    'family_size': family.family_size,
                    'children_count': family.children_count,
                    'housing_type': family.housing_type,
                    'emergency_contact_name': family.emergency_contact_name,
                    'emergency_contact_phone': family.emergency_contact_phone,
                    'emergency_contact_relation': family.emergency_contact_relation,
                    'children': children_data,
                    'parents': parents_data
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du groupe familial {family_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/family-groups/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_family_group(self, **kwargs):
        """Créer un nouveau groupe familial"""
        try:
            # Validation des données requises
            required_fields = ['family_name', 'family_code']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Le champ {field} est requis'}
            
            # Préparer les données
            data = {
                'family_name': kwargs['family_name'],
                'family_code': kwargs['family_code'],
                'home_address': kwargs.get('home_address'),
                'home_phone': kwargs.get('home_phone'),
                'family_income': kwargs.get('family_income'),
                'housing_type': kwargs.get('housing_type'),
                'emergency_contact_name': kwargs.get('emergency_contact_name'),
                'emergency_contact_phone': kwargs.get('emergency_contact_phone'),
                'emergency_contact_relation': kwargs.get('emergency_contact_relation')
            }
            
            # Traiter les relations Many2many si fournies
            if kwargs.get('parent_ids'):
                data['parent_ids'] = [(6, 0, kwargs['parent_ids'])]
            
            if kwargs.get('student_ids'):
                data['student_ids'] = [(6, 0, kwargs['student_ids'])]
            
            family_group = request.env['student.family.group'].create(data)
            
            return {
                'success': True,
                'message': 'Groupe familial créé avec succès',
                'data': {
                    'id': family_group.id,
                    'family_name': family_group.family_name,
                    'family_code': family_group.family_code
                }
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la création du groupe familial: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/family-groups/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_family_group(self, **kwargs):
        """Mettre à jour un groupe familial"""
        try:
            family_id = kwargs.get('family_id')
            if not family_id:
                return {'success': False, 'error': 'Le paramètre family_id est requis'}
            family = request.env['student.family.group'].browse(family_id)
            if not family.exists():
                return {'success': False, 'error': 'Groupe familial non trouvé'}
            
            # Préparer les données de mise à jour
            update_data = {}
            allowed_fields = [
                'family_name', 'family_code', 'home_address', 'home_phone', 
                'family_income', 'housing_type', 'emergency_contact_name',
                'emergency_contact_phone', 'emergency_contact_relation'
            ]
            
            for field in allowed_fields:
                if field in kwargs:
                    update_data[field] = kwargs[field]
            
            # Traiter les relations Many2many
            if 'parent_ids' in kwargs:
                update_data['parent_ids'] = [(6, 0, kwargs['parent_ids'])]
            
            if 'student_ids' in kwargs:
                update_data['student_ids'] = [(6, 0, kwargs['student_ids'])]
            
            if update_data:
                family.write(update_data)
            
            return {
                'success': True,
                'message': 'Groupe familial mis à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour du groupe familial: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/family-groups/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_family_group(self, **kwargs):
        """Supprimer un groupe familial"""
        try:
            family_id = kwargs.get('family_id')
            if not family_id:
                return {'success': False, 'error': 'Le paramètre family_id est requis'}
            family = request.env['student.family.group'].browse(family_id)
            if not family.exists():
                return {'success': False, 'error': 'Groupe familial non trouvé'}
            
            # Vérifier s'il y a des enfants liés
            if family.children_count > 0:
                return {
                    'success': False,
                    'error': f'Impossible de supprimer: {family.children_count} enfants sont liés à ce groupe'
                }
            
            family_name = family.family_name
            family.unlink()
            
            return {
                'success': True,
                'message': f'Groupe familial {family_name} supprimé avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression du groupe familial: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/family-groups/add-student', type='json', auth='user', methods=['POST'], csrf=False)
    def add_student_to_family(self, **kwargs):
        """Ajouter un élève à un groupe familial"""
        try:
            family_id = kwargs.get('family_id')
            if not family_id:
                return {'success': False, 'error': 'Le paramètre family_id est requis'}
            family = request.env['student.family.group'].browse(family_id)
            if not family.exists():
                return {'success': False, 'error': 'Groupe familial non trouvé'}
            
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'ID élève requis'}
            
            student = request.env['op.student'].browse(int(student_id))
            if not student.exists():
                return {'success': False, 'error': 'Élève non trouvé'}
            
            # Ajouter l'élève au groupe familial
            student.family_group_id = family.id
            
            return {
                'success': True,
                'message': f'Élève {student.name} ajouté au groupe familial'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'ajout de l'élève au groupe familial: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/family-groups/remove-student', type='json', auth='user', methods=['POST'], csrf=False)
    def remove_student_from_family(self, **kwargs):
        """Retirer un élève d'un groupe familial"""
        try:
            family_id = kwargs.get('family_id')
            if not family_id:
                return {'success': False, 'error': 'Le paramètre family_id est requis'}
            family = request.env['student.family.group'].browse(family_id)
            if not family.exists():
                return {'success': False, 'error': 'Groupe familial non trouvé'}
            
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'ID élève requis'}
            
            student = request.env['op.student'].browse(int(student_id))
            if not student.exists():
                return {'success': False, 'error': 'Élève non trouvé'}
            
            # Retirer l'élève du groupe familial
            student.family_group_id = False
            
            return {
                'success': True,
                'message': f'Élève {student.name} retiré du groupe familial'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors du retrait de l'élève du groupe familial: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/family-groups/add-parent', type='json', auth='user', methods=['POST'], csrf=False)
    def add_parent_to_family(self, **kwargs):
        """Ajouter un parent à un groupe familial"""
        try:
            family_id = kwargs.get('family_id')
            if not family_id:
                return {'success': False, 'error': 'Le paramètre family_id est requis'}
            family = request.env['student.family.group'].browse(family_id)
            if not family.exists():
                return {'success': False, 'error': 'Groupe familial non trouvé'}
            
            parent_id = kwargs.get('parent_id')
            if not parent_id:
                return {'success': False, 'error': 'ID parent requis'}
            
            parent = request.env['op.parent'].browse(int(parent_id))
            if not parent.exists():
                return {'success': False, 'error': 'Parent non trouvé'}
            
            # Ajouter le parent au groupe familial
            family.parent_ids = [(4, parent.id)]
            
            return {
                'success': True,
                'message': f'Parent {parent.name} ajouté au groupe familial'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'ajout du parent au groupe familial: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/family-groups/statistics', type='json', auth='user', methods=['POST'], csrf=False)
    def get_family_statistics(self, **kwargs):
        """Récupérer les statistiques des groupes familiaux"""
        try:
            # Statistiques générales
            total_families = request.env['student.family.group'].search_count([])
            total_students_in_families = sum(
                request.env['student.family.group'].search([]).mapped('children_count')
            )
            
            # Répartition par taille de famille
            size_distribution = {}
            families = request.env['student.family.group'].search([])
            for family in families:
                size = family.children_count
                if size not in size_distribution:
                    size_distribution[size] = 0
                size_distribution[size] += 1
            
            # Répartition par niveau de revenus
            income_distribution = {}
            for family in families:
                income = family.family_income or 'non_renseigne'
                if income not in income_distribution:
                    income_distribution[income] = 0
                income_distribution[income] += 1
            
            # Répartition par type de logement
            housing_distribution = {}
            for family in families:
                housing = family.housing_type or 'non_renseigne'
                if housing not in housing_distribution:
                    housing_distribution[housing] = 0
                housing_distribution[housing] += 1
            
            return {
                'success': True,
                'data': {
                    'total_families': total_families,
                    'total_students_in_families': total_students_in_families,
                    'average_family_size': total_students_in_families / total_families if total_families > 0 else 0,
                    'size_distribution': size_distribution,
                    'income_distribution': income_distribution,
                    'housing_distribution': housing_distribution
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return {'success': False, 'error': str(e)} 