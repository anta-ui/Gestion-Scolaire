# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduAccountingUtilsController(http.Controller):
    """Controller pour les utilitaires et services transversaux"""

    @http.route('/api/utils/academic-years', type='json', auth='user', methods=['POST'], csrf=False)
    def get_academic_years(self, **kwargs):
        """Liste des années académiques disponibles"""
        try:
            active_only = kwargs.get('active_only', True)
            
            # Vérifier si le modèle existe
            if 'op.academic.year' not in request.env:
                return {
                    'success': True,
                    'data': [],
                    'message': 'Module OpenERP Academic non installé'
                }
            
            # Essayer d'accéder au modèle et lister les champs disponibles
            try:
                model_obj = request.env['op.academic.year']
                model_fields = model_obj._fields.keys()
                
                domain = []
                # Ajouter le filtre 'active' seulement si le champ existe
                if active_only and 'active' in model_fields:
                    domain.append(('active', '=', True))
                
                years = model_obj.search(domain, order='name desc')
            except Exception as e:
                # Si le modèle n'est pas accessible ou a des problèmes
                return {
                    'success': True,
                    'data': [],
                    'message': f'Module OpenERP Academic non disponible: {str(e)}'
                }
            
            years_list = []
            for year in years:
                years_list.append({
                    'id': year.id,
                    'name': year.name,
                    'code': year.code if hasattr(year, 'code') else '',
                    'start_date': year.date_start.isoformat() if hasattr(year, 'date_start') and year.date_start else '',
                    'end_date': year.date_stop.isoformat() if hasattr(year, 'date_stop') and year.date_stop else '',
                    'active': year.active if hasattr(year, 'active') else True,
                    'current': year.current if hasattr(year, 'current') else False
                })
            
            return {
                'success': True,
                'data': years_list
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des années académiques: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/utils/courses', type='json', auth='user', methods=['POST'], csrf=False)
    def get_courses(self, **kwargs):
        """Liste des cours disponibles"""
        try:
            active_only = kwargs.get('active_only', True)
            academic_year_id = kwargs.get('academic_year_id')
            
            domain = []
            if active_only:
                domain.append(('active', '=', True))
            if academic_year_id:
                domain.append(('academic_year_id', '=', academic_year_id))
            
            courses = request.env['op.course'].search(domain, order='name')
            
            courses_list = []
            for course in courses:
                courses_list.append({
                    'id': course.id,
                    'name': course.name,
                    'code': course.code if hasattr(course, 'code') else '',
                    'department': course.department_id.name if hasattr(course, 'department_id') and course.department_id else '',
                    'academic_year': course.academic_year_id.name if hasattr(course, 'academic_year_id') and course.academic_year_id else '',
                    'duration': course.duration if hasattr(course, 'duration') else '',
                    'student_count': len(course.student_ids) if hasattr(course, 'student_ids') else 0,
                    'active': course.active if hasattr(course, 'active') else True
                })
            
            return {
                'success': True,
                'data': courses_list
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des cours: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/utils/students', type='json', auth='user', methods=['POST'], csrf=False)
    def get_students(self, **kwargs):
        """Liste des étudiants avec filtres"""
        try:
            active_only = kwargs.get('active_only', True)
            course_id = kwargs.get('course_id')
            academic_year_id = kwargs.get('academic_year_id')
            search_term = kwargs.get('search_term', '').strip()
            limit = kwargs.get('limit', 50)
            offset = kwargs.get('offset', 0)
            
            domain = [('is_student', '=', True)]
            if active_only:
                domain.append(('active', '=', True))
            if course_id:
                domain.append(('course_detail_ids.course_id', '=', course_id))
            if academic_year_id:
                domain.append(('course_detail_ids.academic_year_id', '=', academic_year_id))
            if search_term:
                domain.extend([
                    '|', '|', '|',
                    ('name', 'ilike', search_term),
                    ('email', 'ilike', search_term),
                    ('phone', 'ilike', search_term),
                    ('gr_no', 'ilike', search_term)
                ])
            
            students = request.env['res.partner'].search(domain, limit=limit, offset=offset, order='name')
            total_count = request.env['res.partner'].search_count(domain)
            
            students_list = []
            for student in students:
                # Récupérer le cours actuel
                current_course = ''
                if hasattr(student, 'course_detail_ids') and student.course_detail_ids:
                    active_course = student.course_detail_ids.filtered(lambda c: c.active if hasattr(c, 'active') else True)
                    if active_course:
                        current_course = active_course[0].course_id.name if active_course[0].course_id else ''
                
                students_list.append({
                    'id': student.id,
                    'name': student.name,
                    'email': student.email if hasattr(student, 'email') else '',
                    'phone': student.phone if hasattr(student, 'phone') else '',
                    'gr_no': student.gr_no if hasattr(student, 'gr_no') else '',
                    'current_course': current_course,
                    'image_url': f'/web/image/res.partner/{student.id}/image_1920' if hasattr(student, 'image_1920') and student.image_1920 else '',
                    'active': student.active
                })
            
            return {
                'success': True,
                'data': {
                    'students': students_list,
                    'total_count': total_count,
                    'has_more': (offset + limit) < total_count
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des étudiants: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/utils/payment-methods', type='json', auth='user', methods=['POST'], csrf=False)
    def get_payment_methods(self, **kwargs):
        """Liste des méthodes de paiement actives"""
        try:
            active_only = kwargs.get('active_only', True)
            
            domain = []
            if active_only:
                domain.append(('active', '=', True))
            
            methods = request.env['edu.payment.method'].search(domain, order='sequence, name')
            
            methods_list = []
            for method in methods:
                methods_list.append({
                    'id': method.id,
                    'name': method.name,
                    'method_type': method.method_type if hasattr(method, 'method_type') else '',
                    'is_default': method.is_default if hasattr(method, 'is_default') else False,
                    'fee_percentage': method.fee_percentage if hasattr(method, 'fee_percentage') else 0,
                    'fixed_fee': method.fixed_fee if hasattr(method, 'fixed_fee') else 0,
                    'active': method.active
                })
            
            return {
                'success': True,
                'data': methods_list
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des méthodes de paiement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/utils/calculate-total', type='json', auth='user', methods=['POST'], csrf=False)
    def calculate_total(self, **kwargs):
        """Calcule un montant total avec frais et remises"""
        try:
            base_amount = kwargs.get('base_amount', 0)
            discount_type = kwargs.get('discount_type', 'amount')  # 'amount' ou 'percentage'
            discount_value = kwargs.get('discount_value', 0)
            fee_percentage = kwargs.get('fee_percentage', 0)
            fixed_fee = kwargs.get('fixed_fee', 0)
            
            if not isinstance(base_amount, (int, float)) or base_amount < 0:
                return {'success': False, 'error': 'Montant de base invalide'}
            
            # Calcul de la remise
            if discount_type == 'percentage':
                if not (0 <= discount_value <= 100):
                    return {'success': False, 'error': 'Pourcentage de remise invalide (0-100)'}
                discount_amount = base_amount * (discount_value / 100)
            else:
                discount_amount = min(discount_value, base_amount)  # La remise ne peut pas être supérieure au montant
            
            # Montant après remise
            amount_after_discount = base_amount - discount_amount
            
            # Calcul des frais
            fee_amount = (amount_after_discount * (fee_percentage / 100)) + fixed_fee
            
            # Montant final
            total_amount = amount_after_discount + fee_amount
            
            calculation = {
                'base_amount': base_amount,
                'discount': {
                    'type': discount_type,
                    'value': discount_value,
                    'amount': discount_amount
                },
                'amount_after_discount': amount_after_discount,
                'fees': {
                    'percentage': fee_percentage,
                    'fixed': fixed_fee,
                    'total_fee': fee_amount
                },
                'final_amount': total_amount,
                'savings': discount_amount
            }
            
            return {
                'success': True,
                'data': calculation
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors du calcul: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/utils/validate-payment', type='json', auth='user', methods=['POST'], csrf=False)
    def validate_payment_data(self, **kwargs):
        """Valide les données de paiement avant traitement"""
        try:
            student_id = kwargs.get('student_id')
            amount = kwargs.get('amount', 0)
            payment_method_id = kwargs.get('payment_method_id')
            reference = kwargs.get('reference', '').strip()
            
            errors = []
            warnings = []
            
            # Validation de l'étudiant
            if not student_id:
                errors.append("ID étudiant requis")
            else:
                student = request.env['res.partner'].browse(student_id)
                if not student.exists():
                    errors.append("Étudiant non trouvé")
                elif not student.is_student:
                    warnings.append("Le partenaire sélectionné n'est pas marqué comme étudiant")
            
            # Validation du montant
            if not isinstance(amount, (int, float)) or amount <= 0:
                errors.append("Montant invalide (doit être positif)")
            elif amount > 1000000:
                warnings.append("Montant très élevé, vérifiez s'il est correct")
            
            # Validation de la méthode de paiement
            if not payment_method_id:
                errors.append("Méthode de paiement requise")
            else:
                method = request.env['edu.payment.method'].browse(payment_method_id)
                if not method.exists():
                    errors.append("Méthode de paiement non trouvée")
                elif not method.active:
                    errors.append("Méthode de paiement inactive")
            
            # Validation de la référence
            if not reference:
                warnings.append("Aucune référence fournie")
            elif len(reference) < 3:
                warnings.append("Référence très courte")
            else:
                # Vérifier l'unicité de la référence
                existing_payment = request.env['edu.student.payment'].search([('name', '=', reference)], limit=1)
                if existing_payment:
                    errors.append(f"Référence déjà utilisée dans le paiement #{existing_payment.id}")
            
            validation_result = {
                'is_valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'validated_data': {
                    'student_id': student_id,
                    'amount': amount,
                    'payment_method_id': payment_method_id,
                    'reference': reference
                }
            }
            
            return {
                'success': True,
                'data': validation_result
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la validation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/utils/system-info', type='json', auth='user', methods=['POST'], csrf=False)
    def get_system_info(self, **kwargs):
        """Informations système pour le module comptable"""
        try:
            # Compter les enregistrements par modèle
            models_count = {}
            
            # Modèles principaux
            main_models = [
                'edu.fee.structure',
                'edu.fee.type',
                'edu.student.invoice',
                'edu.student.payment',
                'edu.fee.collection',
                'edu.payment.plan',
                'edu.scholarship',
                'edu.discount',
                'edu.payment.method',
                'edu.accounting.config',
                'edu.financial.aid'
            ]
            
            for model in main_models:
                try:
                    count = request.env[model].search_count([])
                    models_count[model] = count
                except Exception:
                    models_count[model] = 0
            
            # Statistiques rapides
            total_invoices = models_count.get('edu.student.invoice', 0)
            total_payments = models_count.get('edu.student.payment', 0)
            active_collections = request.env['edu.fee.collection'].search_count([('state', '=', 'active')]) if 'edu.fee.collection' in request.env else 0
            
            # Version du module
            module_info = request.env['ir.module.module'].search([('name', '=', 'edu_accounting_pro')], limit=1)
            module_version = module_info.latest_version if module_info and hasattr(module_info, 'latest_version') else 'N/A'
            
            system_info = {
                'module_version': module_version,
                'database_name': request.env.cr.dbname,
                'current_user': {
                    'id': request.env.user.id,
                    'name': request.env.user.name,
                    'login': request.env.user.login
                },
                'models_count': models_count,
                'quick_stats': {
                    'total_invoices': total_invoices,
                    'total_payments': total_payments,
                    'active_collections': active_collections,
                    'active_students': request.env['res.partner'].search_count([('is_student', '=', True), ('active', '=', True)])
                },
                'server_time': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'data': system_info
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des infos système: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/utils/health-check', type='json', auth='user', methods=['POST'], csrf=False)
    def health_check(self, **kwargs):
        """Vérification de l'état de santé du module"""
        try:
            checks = {}
            overall_status = 'healthy'
            
            # Vérifier la connexion à la base de données
            try:
                request.env.cr.execute("SELECT 1")
                checks['database'] = {'status': 'ok', 'message': 'Connexion BD active'}
            except Exception as e:
                checks['database'] = {'status': 'error', 'message': f'Erreur BD: {str(e)}'}
                overall_status = 'error'
            
            # Vérifier les modèles critiques
            critical_models = ['edu.student.invoice', 'edu.student.payment', 'edu.payment.method']
            for model in critical_models:
                try:
                    request.env[model].search([], limit=1)
                    checks[f'model_{model}'] = {'status': 'ok', 'message': f'Modèle {model} accessible'}
                except Exception as e:
                    checks[f'model_{model}'] = {'status': 'error', 'message': f'Erreur modèle {model}: {str(e)}'}
                    overall_status = 'error'
            
            # Vérifier les permissions utilisateur
            try:
                request.env['edu.student.invoice'].check_access_rights('read')
                checks['permissions'] = {'status': 'ok', 'message': 'Permissions utilisateur OK'}
            except Exception as e:
                checks['permissions'] = {'status': 'warning', 'message': f'Permissions limitées: {str(e)}'}
                if overall_status == 'healthy':
                    overall_status = 'warning'
            
            health_report = {
                'overall_status': overall_status,
                'checks': checks,
                'timestamp': datetime.now().isoformat(),
                'user_id': request.env.user.id
            }
            
            return {
                'success': True,
                'data': health_report
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors du health check: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
