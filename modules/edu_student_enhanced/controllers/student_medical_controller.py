# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)

class StudentMedicalController(http.Controller):
    """API Controller pour StudentMedicalInfo"""

    @http.route('/api/medical-info', type='json', auth='user', methods=['POST'], csrf=False)
    def get_medical_info(self, **kwargs):
        """Récupérer la liste des informations médicales"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', int(kwargs['student_id'])))
            
            if kwargs.get('medical_type'):
                domain.append(('medical_type', '=', kwargs['medical_type']))
            
            if kwargs.get('severity'):
                domain.append(('severity', '=', kwargs['severity']))
            
            if kwargs.get('is_active') is not None:
                domain.append(('is_active', '=', kwargs['is_active']))
            
            if kwargs.get('is_critical') is not None:
                domain.append(('is_critical', '=', kwargs['is_critical']))
            
            # Pagination
            limit = int(kwargs.get('limit', 20))
            offset = int(kwargs.get('offset', 0))
            
            medical_infos = request.env['student.medical.info'].search(domain, limit=limit, offset=offset)
            total_count = request.env['student.medical.info'].search_count(domain)
            
            data = []
            for info in medical_infos:
                data.append({
                    'id': info.id,
                    'student_id': info.student_id.id,
                    'student_name': info.student_name,
                    'medical_type': info.medical_type,
                    'title': info.title,
                    'description': info.description,
                    'severity': info.severity,
                    'date': info.date.isoformat() if info.date else None,
                    'start_date': info.start_date.isoformat() if info.start_date else None,
                    'end_date': info.end_date.isoformat() if info.end_date else None,
                    'next_checkup': info.next_checkup.isoformat() if info.next_checkup else None,
                    'doctor_name': info.doctor_name,
                    'doctor_phone': info.doctor_phone,
                    'hospital': info.hospital,
                    'is_active': info.is_active,
                    'is_critical': info.is_critical,
                    'requires_attention': info.requires_attention,
                    'days_since': info.days_since,
                    'status_color': info.status_color
                })
            
            return {
                'success': True,
                'data': data,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des informations médicales: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/medical-info/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_medical_info_detail(self, **kwargs):
        """Récupérer les détails d'une information médicale"""
        try:
            info_id = kwargs.get('info_id')
            if not info_id:
                return {'success': False, 'error': 'Le paramètre info_id est requis'}
            info = request.env['student.medical.info'].browse(info_id)
            if not info.exists():
                return {'success': False, 'error': 'Information médicale non trouvée'}
            
            return {
                'success': True,
                'data': {
                    'id': info.id,
                    'student_id': info.student_id.id,
                    'student_name': info.student_name,
                    'medical_type': info.medical_type,
                    'title': info.title,
                    'description': info.description,
                    'severity': info.severity,
                    'date': info.date.isoformat() if info.date else None,
                    'start_date': info.start_date.isoformat() if info.start_date else None,
                    'end_date': info.end_date.isoformat() if info.end_date else None,
                    'next_checkup': info.next_checkup.isoformat() if info.next_checkup else None,
                    'doctor_name': info.doctor_name,
                    'doctor_phone': info.doctor_phone,
                    'hospital': info.hospital,
                    'treatment': info.treatment,
                    'medication_name': info.medication_name,
                    'dosage': info.dosage,
                    'frequency': info.frequency,
                    'is_active': info.is_active,
                    'is_critical': info.is_critical,
                    'requires_attention': info.requires_attention,
                    'notify_parents': info.notify_parents,
                    'notify_teachers': info.notify_teachers,
                    'notify_nurse': info.notify_nurse,
                    'notes': info.notes,
                    'created_by': info.created_by.name if info.created_by else None,
                    'days_since': info.days_since,
                    'status_color': info.status_color
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de l'information médicale {info_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/medical-info/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_medical_info(self, **kwargs):
        """Créer une nouvelle information médicale"""
        try:
            # Validation des données requises
            required_fields = ['student_id', 'medical_type', 'title']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Le champ {field} est requis'}
            
            # Préparer les données
            data = {
                'student_id': int(kwargs['student_id']),
                'medical_type': kwargs['medical_type'],
                'title': kwargs['title'],
                'description': kwargs.get('description'),
                'severity': kwargs.get('severity', 'low'),
                'date': kwargs.get('date'),
                'start_date': kwargs.get('start_date'),
                'end_date': kwargs.get('end_date'),
                'next_checkup': kwargs.get('next_checkup'),
                'doctor_name': kwargs.get('doctor_name'),
                'doctor_phone': kwargs.get('doctor_phone'),
                'hospital': kwargs.get('hospital'),
                'treatment': kwargs.get('treatment'),
                'medication_name': kwargs.get('medication_name'),
                'dosage': kwargs.get('dosage'),
                'frequency': kwargs.get('frequency'),
                'requires_attention': kwargs.get('requires_attention', False),
                'notify_parents': kwargs.get('notify_parents', False),
                'notify_teachers': kwargs.get('notify_teachers', False),
                'notify_nurse': kwargs.get('notify_nurse', True),
                'notes': kwargs.get('notes')
            }
            
            medical_info = request.env['student.medical.info'].create(data)
            
            return {
                'success': True,
                'message': 'Information médicale créée avec succès',
                'data': {
                    'id': medical_info.id,
                    'title': medical_info.title,
                    'medical_type': medical_info.medical_type,
                    'is_critical': medical_info.is_critical
                }
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la création de l'information médicale: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/medical-info/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_medical_info(self, **kwargs):
        """Mettre à jour une information médicale"""
        try:
            info_id = kwargs.get('info_id')
            if not info_id:
                return {'success': False, 'error': 'Le paramètre info_id est requis'}
            info = request.env['student.medical.info'].browse(info_id)
            if not info.exists():
                return {'success': False, 'error': 'Information médicale non trouvée'}
            
            # Préparer les données de mise à jour
            update_data = {}
            allowed_fields = [
                'medical_type', 'title', 'description', 'severity', 'date', 'start_date', 
                'end_date', 'next_checkup', 'doctor_name', 'doctor_phone', 'hospital',
                'treatment', 'medication_name', 'dosage', 'frequency', 'is_active',
                'requires_attention', 'notify_parents', 'notify_teachers', 'notify_nurse', 'notes'
            ]
            
            for field in allowed_fields:
                if field in kwargs:
                    update_data[field] = kwargs[field]
            
            if update_data:
                info.write(update_data)
            
            return {
                'success': True,
                'message': 'Information médicale mise à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour de l'information médicale: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/medical-info/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_medical_info(self, **kwargs):
        """Supprimer une information médicale"""
        try:
            info_id = kwargs.get('info_id')
            if not info_id:
                return {'success': False, 'error': 'Le paramètre info_id est requis'}
            info = request.env['student.medical.info'].browse(info_id)
            if not info.exists():
                return {'success': False, 'error': 'Information médicale non trouvée'}
            
            title = info.title
            info.unlink()
            
            return {
                'success': True,
                'message': f'Information médicale {title} supprimée avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression de l'information médicale: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/medical-info/archive', type='json', auth='user', methods=['POST'], csrf=False)
    def archive_medical_info(self, **kwargs):
        """Archiver une information médicale"""
        try:
            info_id = kwargs.get('info_id')
            if not info_id:
                return {'success': False, 'error': 'Le paramètre info_id est requis'}
            info = request.env['student.medical.info'].browse(info_id)
            if not info.exists():
                return {'success': False, 'error': 'Information médicale non trouvée'}
            
            info.action_archive()
            
            return {
                'success': True,
                'message': 'Information médicale archivée avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'archivage: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/medical-info/mark-critical', type='json', auth='user', methods=['POST'], csrf=False)
    def mark_critical(self, **kwargs):
        """Marquer une information médicale comme critique"""
        try:
            info_id = kwargs.get('info_id')
            if not info_id:
                return {'success': False, 'error': 'Le paramètre info_id est requis'}
            info = request.env['student.medical.info'].browse(info_id)
            if not info.exists():
                return {'success': False, 'error': 'Information médicale non trouvée'}
            
            info.action_mark_critical()
            
            return {
                'success': True,
                'message': 'Information marquée comme critique'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors du marquage critique: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/medical-info/notify', type='json', auth='user', methods=['POST'], csrf=False)
    def send_notifications(self, **kwargs):
        """Envoyer les notifications pour une information médicale"""
        try:
            info_id = kwargs.get('info_id')
            if not info_id:
                return {'success': False, 'error': 'Le paramètre info_id est requis'}
            info = request.env['student.medical.info'].browse(info_id)
            if not info.exists():
                return {'success': False, 'error': 'Information médicale non trouvée'}
            
            info.action_send_notifications()
            
            return {
                'success': True,
                'message': 'Notifications envoyées avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi des notifications: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/students/medical-summary', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_medical_summary(self, **kwargs):
        """Récupérer le résumé médical d'un élève"""
        try:
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'Le paramètre student_id est requis'}
            student = request.env['op.student'].browse(student_id)
            if not student.exists():
                return {'success': False, 'error': 'Élève non trouvé'}
            
            medical_infos = student.medical_info_ids
            
            # Statistiques générales
            total_records = len(medical_infos)
            active_records = len(medical_infos.filtered(lambda r: r.is_active))
            critical_records = len(medical_infos.filtered(lambda r: r.is_critical))
            
            # Répartition par type
            type_stats = {}
            for info in medical_infos:
                if info.medical_type not in type_stats:
                    type_stats[info.medical_type] = 0
                type_stats[info.medical_type] += 1
            
            # Alertes actives
            active_alerts = medical_infos.filtered(lambda r: r.is_active and r.requires_attention)
            
            return {
                'success': True,
                'data': {
                    'student_id': student_id,
                    'student_name': student.name,
                    'blood_group': student.blood_group,
                    'allergies': student.allergies,
                    'chronic_diseases': student.chronic_diseases,
                    'current_medications': student.current_medications,
                    'doctor_name': student.doctor_name,
                    'doctor_phone': student.doctor_phone,
                    'has_medical_alerts': student.has_medical_alerts,
                    'medical_alerts_count': student.medical_alerts_count,
                    'statistics': {
                        'total_records': total_records,
                        'active_records': active_records,
                        'critical_records': critical_records,
                        'active_alerts': len(active_alerts)
                    },
                    'type_distribution': type_stats,
                    'active_alerts': [
                        {
                            'id': alert.id,
                            'title': alert.title,
                            'medical_type': alert.medical_type,
                            'severity': alert.severity,
                            'date': alert.date.isoformat() if alert.date else None
                        }
                        for alert in active_alerts
                    ]
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du résumé médical: {str(e)}")
            return {'success': False, 'error': str(e)}


class StudentVaccinationController(http.Controller):
    """API Controller pour StudentVaccination"""

    @http.route('/api/vaccinations', type='json', auth='user', methods=['POST'], csrf=False)
    def get_vaccinations(self, **kwargs):
        """Récupérer la liste des vaccinations"""
        try:
            domain = []
            
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', int(kwargs['student_id'])))
            
            if kwargs.get('vaccine_type'):
                domain.append(('vaccine_type', '=', kwargs['vaccine_type']))
            
            if kwargs.get('is_up_to_date') is not None:
                domain.append(('is_up_to_date', '=', kwargs['is_up_to_date']))
            
            # Pagination
            limit = int(kwargs.get('limit', 20))
            offset = int(kwargs.get('offset', 0))
            
            vaccinations = request.env['student.vaccination'].search(domain, limit=limit, offset=offset)
            total_count = request.env['student.vaccination'].search_count(domain)
            
            data = []
            for vaccination in vaccinations:
                data.append({
                    'id': vaccination.id,
                    'student_id': vaccination.student_id.id,
                    'student_name': vaccination.student_id.name,
                    'vaccine_name': vaccination.vaccine_name,
                    'vaccine_type': vaccination.vaccine_type,
                    'administration_date': vaccination.administration_date.isoformat() if vaccination.administration_date else None,
                    'expiry_date': vaccination.expiry_date.isoformat() if vaccination.expiry_date else None,
                    'dose_number': vaccination.dose_number,
                    'is_booster': vaccination.is_booster,
                    'next_dose_date': vaccination.next_dose_date.isoformat() if vaccination.next_dose_date else None,
                    'is_up_to_date': vaccination.is_up_to_date,
                    'administered_by': vaccination.administered_by,
                    'location': vaccination.location
                })
            
            return {
                'success': True,
                'data': data,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des vaccinations: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/vaccinations/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_vaccination(self, **kwargs):
        """Créer une nouvelle vaccination"""
        try:
            # Validation des données requises
            required_fields = ['student_id', 'vaccine_name', 'administration_date']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Le champ {field} est requis'}
            
            data = {
                'student_id': int(kwargs['student_id']),
                'vaccine_name': kwargs['vaccine_name'],
                'vaccine_type': kwargs.get('vaccine_type'),
                'administration_date': kwargs['administration_date'],
                'expiry_date': kwargs.get('expiry_date'),
                'batch_number': kwargs.get('batch_number'),
                'administered_by': kwargs.get('administered_by'),
                'location': kwargs.get('location'),
                'dose_number': int(kwargs.get('dose_number', 1)),
                'is_booster': kwargs.get('is_booster', False),
                'next_dose_date': kwargs.get('next_dose_date'),
                'notes': kwargs.get('notes')
            }
            
            vaccination = request.env['student.vaccination'].create(data)
            
            return {
                'success': True,
                'message': 'Vaccination créée avec succès',
                'data': {
                    'id': vaccination.id,
                    'vaccine_name': vaccination.vaccine_name,
                    'vaccine_type': vaccination.vaccine_type
                }
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la vaccination: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/students/vaccination-card', type='json', auth='user', methods=['POST'], csrf=False)
    def get_vaccination_card(self, **kwargs):
        """Récupérer le carnet de vaccination d'un élève"""
        try:
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'Le paramètre student_id est requis'}
            student = request.env['op.student'].browse(student_id)
            if not student.exists():
                return {'success': False, 'error': 'Élève non trouvé'}
            
            vaccinations = request.env['student.vaccination'].search([('student_id', '=', student_id)])
            
            # Organiser par type de vaccin
            vaccine_groups = {}
            for vaccination in vaccinations:
                vaccine_type = vaccination.vaccine_type or 'other'
                if vaccine_type not in vaccine_groups:
                    vaccine_groups[vaccine_type] = []
                
                vaccine_groups[vaccine_type].append({
                    'id': vaccination.id,
                    'vaccine_name': vaccination.vaccine_name,
                    'administration_date': vaccination.administration_date.isoformat() if vaccination.administration_date else None,
                    'expiry_date': vaccination.expiry_date.isoformat() if vaccination.expiry_date else None,
                    'dose_number': vaccination.dose_number,
                    'is_booster': vaccination.is_booster,
                    'next_dose_date': vaccination.next_dose_date.isoformat() if vaccination.next_dose_date else None,
                    'is_up_to_date': vaccination.is_up_to_date,
                    'administered_by': vaccination.administered_by,
                    'location': vaccination.location,
                    'batch_number': vaccination.batch_number
                })
            
            # Statistiques
            total_vaccinations = len(vaccinations)
            up_to_date = len(vaccinations.filtered(lambda v: v.is_up_to_date))
            needs_update = total_vaccinations - up_to_date
            
            return {
                'success': True,
                'data': {
                    'student_id': student_id,
                    'student_name': student.name,
                    'vaccine_groups': vaccine_groups,
                    'statistics': {
                        'total_vaccinations': total_vaccinations,
                        'up_to_date': up_to_date,
                        'needs_update': needs_update,
                        'completion_rate': (up_to_date / total_vaccinations * 100) if total_vaccinations > 0 else 0
                    }
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du carnet de vaccination: {str(e)}")
            return {'success': False, 'error': str(e)}


class StudentMedicalCategoryController(http.Controller):
    """API Controller pour StudentMedicalCategory"""

    @http.route('/api/medical-categories', type='json', auth='user', methods=['POST'], csrf=False)
    def get_medical_categories(self, **kwargs):
        """Récupérer la liste des catégories médicales"""
        try:
            categories = request.env['student.medical.category'].search([])
            
            data = []
            for category in categories:
                data.append({
                    'id': category.id,
                    'name': category.name,
                    'code': category.code,
                    'description': category.description,
                    'color': category.color,
                    'active': category.active,
                    'icon': category.icon
                })
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des catégories médicales: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/medical-categories/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_medical_category(self, **kwargs):
        """Créer une nouvelle catégorie médicale"""
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
                'color': int(kwargs.get('color', 1)),
                'icon': kwargs.get('icon')
            }
            
            category = request.env['student.medical.category'].create(data)
            
            return {
                'success': True,
                'message': 'Catégorie médicale créée avec succès',
                'data': {
                    'id': category.id,
                    'name': category.name,
                    'code': category.code
                }
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la catégorie médicale: {str(e)}")
            return {'success': False, 'error': str(e)} 