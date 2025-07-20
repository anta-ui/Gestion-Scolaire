# -*- coding: utf-8 -*-

import json
from odoo import http
from odoo.http import request

class TestController(http.Controller):
    """Controller de test pour vérifier le fonctionnement des APIs"""

    @http.route('/api/test', type='http', auth='none', methods=['GET'], csrf=False)
    def test_api(self, **kwargs):
        """Endpoint de test simple"""
        result = {
            'success': True,
            'message': 'API edu_student_enhanced fonctionne!',
            'module': 'edu_student_enhanced',
            'timestamp': str(request.env.cr.now()),
            'parameters': dict(kwargs)
        }
        
        return request.make_response(
            json.dumps(result, indent=2),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/api/test/students', type='http', auth='public', methods=['GET'], csrf=False)
    def test_students_simple(self, **kwargs):
        """Test simple des étudiants sans authentification"""
        try:
            # Compter les étudiants
            student_count = request.env['op.student'].sudo().search_count([])
            
            result = {
                'success': True,
                'message': 'Test simple réussi',
                'student_count': student_count,
                'database': request.env.cr.dbname
            }
            
            return request.make_response(
                json.dumps(result, indent=2),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'message': 'Erreur lors du test'
            }
            
            return request.make_response(
                json.dumps(result, indent=2),
                headers=[('Content-Type', 'application/json')]
            )

    @http.route('/api/test/models', type='http', auth='public', methods=['GET'], csrf=False)
    def test_models(self, **kwargs):
        """Tester la présence des modèles du module"""
        try:
            models_info = {}
            
            # Tester chaque modèle
            model_names = [
                'op.student',
                'student.category',
                'student.behavior.record',
                'student.behavior.category',
                'student.document',
                'student.document.type',
                'student.medical.info',
                'student.vaccination',
                'student.medical.category',
                'student.family.group'
            ]
            
            for model_name in model_names:
                try:
                    count = request.env[model_name].sudo().search_count([])
                    models_info[model_name] = {
                        'exists': True,
                        'count': count
                    }
                except Exception as e:
                    models_info[model_name] = {
                        'exists': False,
                        'error': str(e)
                    }
            
            result = {
                'success': True,
                'message': 'Test des modèles terminé',
                'models': models_info
            }
            
            return request.make_response(
                json.dumps(result, indent=2),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e)
            }
            
            return request.make_response(
                json.dumps(result, indent=2),
                headers=[('Content-Type', 'application/json')]
            )

    @http.route('/api/test/create-data', type='http', auth='public', methods=['POST'], csrf=False)
    def create_test_data(self, **kwargs):
        """Créer des données de test"""
        try:
            created_data = {}
            
            # 1. Créer des catégories de comportement
            behavior_categories = [
                {
                    'name': 'Excellent',
                    'code': 'EXCELLENT',
                    'description': 'Comportement exemplaire',
                    'behavior_impact': 2.0,
                    'color': 'green'
                },
                {
                    'name': 'Bon',
                    'code': 'BON',
                    'description': 'Bon comportement général',
                    'behavior_impact': 1.0,
                    'color': 'blue'
                },
                {
                    'name': 'À améliorer',
                    'code': 'AMELIORER',
                    'description': 'Comportement à améliorer',
                    'behavior_impact': -1.0,
                    'color': 'orange'
                }
            ]
            
            behavior_cats_created = []
            for cat_data in behavior_categories:
                # Vérifier si existe déjà
                existing = request.env['student.behavior.category'].sudo().search([('code', '=', cat_data['code'])])
                if not existing:
                    cat = request.env['student.behavior.category'].sudo().create(cat_data)
                    behavior_cats_created.append({'id': cat.id, 'name': cat.name})
                else:
                    behavior_cats_created.append({'id': existing.id, 'name': existing.name, 'note': 'Existait déjà'})
            
            created_data['behavior_categories'] = behavior_cats_created
            
            # 2. Créer des catégories d'étudiants
            student_categories = [
                {
                    'name': 'Élève méritant',
                    'code': 'MERITANT',
                    'description': 'Élèves avec d\'excellents résultats',
                    'color': 'gold',
                    'criteria': 'Moyenne > 15/20',
                    'benefits': 'Réductions, bourses d\'excellence'
                },
                {
                    'name': 'Élève en difficulté',
                    'code': 'DIFFICULTE',
                    'description': 'Élèves nécessitant un accompagnement',
                    'color': 'red',
                    'criteria': 'Moyenne < 10/20 ou absences répétées',
                    'benefits': 'Soutien scolaire, suivi personnalisé'
                }
            ]
            
            student_cats_created = []
            for cat_data in student_categories:
                # Vérifier si existe déjà
                existing = request.env['student.category'].sudo().search([('code', '=', cat_data['code'])])
                if not existing:
                    cat = request.env['student.category'].sudo().create(cat_data)
                    student_cats_created.append({'id': cat.id, 'name': cat.name})
                else:
                    student_cats_created.append({'id': existing.id, 'name': existing.name, 'note': 'Existait déjà'})
            
            created_data['student_categories'] = student_cats_created
            
            # 3. Créer quelques enregistrements comportementaux
            students = request.env['op.student'].sudo().search([], limit=3)
            behavior_cats = request.env['student.behavior.category'].sudo().search([])
            
            behaviors_created = []
            if students and behavior_cats:
                for i, student in enumerate(students):
                    behavior_data = {
                        'student_id': student.id,
                        'category_id': behavior_cats[i % len(behavior_cats)].id,
                        'incident_type': 'positive' if i % 2 == 0 else 'negative',
                        'description': f'Comportement observé pour {student.name}',
                        'location': 'Salle de classe',
                        'severity': 'low' if i % 2 == 0 else 'medium',
                        'points_awarded': 5 if i % 2 == 0 else -3
                    }
                    
                    behavior = request.env['student.behavior.record'].sudo().create(behavior_data)
                    behaviors_created.append({
                        'id': behavior.id,
                        'student': student.name,
                        'type': behavior.incident_type,
                        'points': behavior.points_awarded
                    })
            
            created_data['behavior_records'] = behaviors_created
            
            # 4. Statistiques finales
            stats = {
                'students': request.env['op.student'].sudo().search_count([]),
                'student_categories': request.env['student.category'].sudo().search_count([]),
                'behavior_categories': request.env['student.behavior.category'].sudo().search_count([]),
                'behavior_records': request.env['student.behavior.record'].sudo().search_count([]),
                'document_types': request.env['student.document.type'].sudo().search_count([]),
                'medical_categories': request.env['student.medical.category'].sudo().search_count([])
            }
            
            result = {
                'success': True,
                'message': 'Données de test créées avec succès',
                'data': created_data,
                'statistics': stats
            }
            
            return request.make_response(
                json.dumps(result, indent=2),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e)
            }
            
            return request.make_response(
                json.dumps(result, indent=2),
                headers=[('Content-Type', 'application/json')]
            ) 