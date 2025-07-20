# -*- coding: utf-8 -*-

import json
import logging
import base64
from datetime import datetime, timedelta, date
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError, UserError
from odoo.http import serialize_exception

_logger = logging.getLogger(__name__)


class ResPartnerAttendanceController(http.Controller):
    """Contrôleur API pour la gestion des personnes avec données de présence"""

    @http.route('/api/persons', type='json', auth='user', methods=['GET'])
    def get_persons(self, **kwargs):
        """Récupère toutes les personnes (étudiants/enseignants)"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('is_student') is not None:
                domain.append(('is_student', '=', kwargs['is_student']))
            
            if kwargs.get('is_teacher') is not None:
                domain.append(('is_teacher', '=', kwargs['is_teacher']))
                
            if kwargs.get('has_biometric') is not None:
                domain.append(('has_biometric_data', '=', kwargs['has_biometric']))
                
            if kwargs.get('search_term'):
                term = kwargs['search_term']
                domain.extend([
                    '|', '|', '|',
                    ('name', 'ilike', term),
                    ('student_code', 'ilike', term),
                    ('teacher_code', 'ilike', term),
                    ('email', 'ilike', term)
                ])

            # Filtrer uniquement les personnes (pas les entreprises)
            domain.append(('is_company', '=', False))
            
            # Filtrer les personnes avec des codes ou marquées comme étudiant/enseignant
            domain.append('|')
            domain.append('|')
            domain.append('|')
            domain.append(('is_student', '=', True))
            domain.append(('is_teacher', '=', True))
            domain.append(('student_code', '!=', False))
            domain.append(('teacher_code', '!=', False))

            # Pagination
            limit = kwargs.get('limit', 100)
            offset = kwargs.get('offset', 0)
            
            persons = request.env['res.partner'].search(
                domain, 
                limit=limit, 
                offset=offset,
                order='name asc'
            )
            
            total_count = request.env['res.partner'].search_count(domain)
            
            return {
                'status': 'success',
                'data': [self._format_person(person) for person in persons],
                'count': len(persons),
                'total_count': total_count
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des personnes: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/persons/<int:person_id>', type='json', auth='user', methods=['GET'])
    def get_person(self, person_id, **kwargs):
        """Récupère une personne spécifique"""
        try:
            person = request.env['res.partner'].browse(person_id)
            if not person.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }
            
            return {
                'status': 'success',
                'data': self._format_person(person, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la personne {person_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/persons/by-code/<string:code>', type='json', auth='user', methods=['GET'])
    def get_person_by_code(self, code, **kwargs):
        """Récupère une personne par son code étudiant ou enseignant"""
        try:
            person = request.env['res.partner'].search([
                '|',
                ('student_code', '=', code),
                ('teacher_code', '=', code)
            ], limit=1)
            
            if not person:
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée avec ce code')
                }
            
            return {
                'status': 'success',
                'data': self._format_person(person, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la personne {code}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/persons', type='json', auth='user', methods=['POST'])
    def create_person(self, **kwargs):
        """Crée une nouvelle personne"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des données obligatoires
            if not data.get('name'):
                return {
                    'status': 'error',
                    'message': _('Le nom est obligatoire')
                }

            # Vérifier l'unicité des codes
            if data.get('student_code'):
                existing = request.env['res.partner'].search([('student_code', '=', data['student_code'])])
                if existing:
                    return {
                        'status': 'error',
                        'message': _('Le code étudiant %s existe déjà') % data['student_code']
                    }

            if data.get('teacher_code'):
                existing = request.env['res.partner'].search([('teacher_code', '=', data['teacher_code'])])
                if existing:
                    return {
                        'status': 'error',
                        'message': _('Le code enseignant %s existe déjà') % data['teacher_code']
                    }

            # Préparation des données
            person_data = self._prepare_person_data(data)
            person_data['is_company'] = False  # S'assurer que c'est une personne
            
            person = request.env['res.partner'].create(person_data)

            return {
                'status': 'success',
                'data': self._format_person(person, detailed=True),
                'message': _('Personne créée avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la personne: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/persons/<int:person_id>', type='json', auth='user', methods=['PUT'])
    def update_person(self, person_id, **kwargs):
        """Met à jour une personne existante"""
        try:
            person = request.env['res.partner'].browse(person_id)
            if not person.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Vérifier l'unicité des codes si modifiés
            if 'student_code' in data and data['student_code'] != person.student_code:
                existing = request.env['res.partner'].search([
                    ('student_code', '=', data['student_code']),
                    ('id', '!=', person_id)
                ])
                if existing:
                    return {
                        'status': 'error',
                        'message': _('Le code étudiant %s existe déjà') % data['student_code']
                    }

            if 'teacher_code' in data and data['teacher_code'] != person.teacher_code:
                existing = request.env['res.partner'].search([
                    ('teacher_code', '=', data['teacher_code']),
                    ('id', '!=', person_id)
                ])
                if existing:
                    return {
                        'status': 'error',
                        'message': _('Le code enseignant %s existe déjà') % data['teacher_code']
                    }

            # Préparation des données
            person_data = self._prepare_person_data(data)
            person.write(person_data)

            return {
                'status': 'success',
                'data': self._format_person(person, detailed=True),
                'message': _('Personne mise à jour avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour de la personne {person_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Données de présence
    @http.route('/api/persons/<int:person_id>/attendance', type='json', auth='user', methods=['GET'])
    def get_person_attendance(self, person_id, **kwargs):
        """Récupère les données de présence d'une personne"""
        try:
            person = request.env['res.partner'].browse(person_id)
            if not person.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            # Filtres optionnels
            domain = []
            if person.is_student:
                domain.append(('student_id', '=', person_id))
            elif person.is_teacher:
                domain.append(('faculty_id', '=', person_id))
            else:
                return {
                    'status': 'error',
                    'message': _('Cette personne n\'est ni étudiant ni enseignant')
                }

            if kwargs.get('date_from'):
                domain.append(('check_in_time', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('check_in_time', '<=', kwargs['date_to']))
            if kwargs.get('attendance_status'):
                domain.append(('attendance_status', '=', kwargs['attendance_status']))

            limit = kwargs.get('limit', 50)
            offset = kwargs.get('offset', 0)

            records = request.env['edu.attendance.record'].search(
                domain,
                limit=limit,
                offset=offset,
                order='check_in_time desc'
            )

            total_count = request.env['edu.attendance.record'].search_count(domain)

            return {
                'status': 'success',
                'data': {
                    'person': {
                        'id': person.id,
                        'name': person.name,
                        'type': 'student' if person.is_student else 'teacher',
                        'code': person.student_code if person.is_student else person.teacher_code
                    },
                    'attendance_records': [self._format_attendance_record(record) for record in records],
                    'count': len(records),
                    'total_count': total_count,
                    'statistics': {
                        'total_records': person.total_attendance_records,
                        'present_count': person.present_count,
                        'absent_count': person.absent_count,
                        'late_count': person.late_count,
                        'excused_count': person.excused_count,
                        'attendance_rate': person.attendance_rate,
                        'absence_rate': person.absence_rate
                    }
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des présences de la personne {person_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/persons/<int:person_id>/attendance/today', type='json', auth='user', methods=['GET'])
    def check_attendance_today(self, person_id, **kwargs):
        """Vérifie la présence du jour pour une personne"""
        try:
            person = request.env['res.partner'].browse(person_id)
            if not person.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            result = person.check_attendance_today()

            return {
                'status': 'success',
                'data': result
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la vérification de présence du jour {person_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/persons/<int:person_id>/attendance/summary', type='json', auth='user', methods=['GET'])
    def get_attendance_summary(self, person_id, **kwargs):
        """Récupère un résumé des présences sur une période"""
        try:
            person = request.env['res.partner'].browse(person_id)
            if not person.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            
            if date_from:
                date_from = datetime.fromisoformat(date_from).date()
            if date_to:
                date_to = datetime.fromisoformat(date_to).date()

            summary = person.get_attendance_summary(date_from, date_to)

            return {
                'status': 'success',
                'data': {
                    'person': {
                        'id': person.id,
                        'name': person.name,
                        'type': 'student' if person.is_student else 'teacher'
                    },
                    'summary': summary
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la génération du résumé {person_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Justificatifs
    @http.route('/api/persons/<int:person_id>/excuses', type='json', auth='user', methods=['GET'])
    def get_person_excuses(self, person_id, **kwargs):
        """Récupère les justificatifs d'une personne"""
        try:
            person = request.env['res.partner'].browse(person_id)
            if not person.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            domain = [('student_id', '=', person_id)]
            
            # Filtres optionnels
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            if kwargs.get('excuse_type'):
                domain.append(('excuse_type', '=', kwargs['excuse_type']))
            if kwargs.get('date_from'):
                domain.append(('date', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('date', '<=', kwargs['date_to']))

            limit = kwargs.get('limit', 50)
            offset = kwargs.get('offset', 0)

            excuses = request.env['edu.attendance.excuse'].search(
                domain,
                limit=limit,
                offset=offset,
                order='date desc'
            )

            total_count = request.env['edu.attendance.excuse'].search_count(domain)

            return {
                'status': 'success',
                'data': {
                    'person': {
                        'id': person.id,
                        'name': person.name
                    },
                    'excuses': [self._format_excuse(excuse) for excuse in excuses],
                    'count': len(excuses),
                    'total_count': total_count
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des justificatifs {person_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Données biométriques
    @http.route('/api/persons/<int:person_id>/biometric', type='json', auth='user', methods=['GET'])
    def get_person_biometric_data(self, person_id, **kwargs):
        """Récupère les données biométriques d'une personne"""
        try:
            person = request.env['res.partner'].browse(person_id)
            if not person.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            biometric_data = []
            for bio in person.biometric_data_ids:
                biometric_data.append({
                    'id': bio.id,
                    'name': bio.name,
                    'biometric_type': bio.biometric_type,
                    'state': bio.state,
                    'active': bio.active,
                    'create_date': bio.create_date.isoformat() if bio.create_date else None
                })

            return {
                'status': 'success',
                'data': {
                    'person': {
                        'id': person.id,
                        'name': person.name,
                        'has_biometric_data': person.has_biometric_data
                    },
                    'biometric_data': biometric_data,
                    'count': len(biometric_data)
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des données biométriques {person_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # QR Code personnel
    @http.route('/api/persons/<int:person_id>/qr-code', type='json', auth='user', methods=['GET'])
    def get_person_qr_code(self, person_id, **kwargs):
        """Récupère le QR code personnel d'une personne"""
        try:
            person = request.env['res.partner'].browse(person_id)
            if not person.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            return {
                'status': 'success',
                'data': {
                    'person': {
                        'id': person.id,
                        'name': person.name
                    },
                    'qr_code': person.personal_qr_code,
                    'qr_image': person.qr_code_image.decode() if person.qr_code_image else None,
                    'has_qr_image': bool(person.qr_code_image)
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du QR code {person_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/persons/<int:person_id>/qr-code/image', type='http', auth='user', methods=['GET'])
    def download_person_qr_image(self, person_id, **kwargs):
        """Télécharge l'image QR code d'une personne"""
        try:
            person = request.env['res.partner'].browse(person_id)
            if not person.exists() or not person.qr_code_image:
                return request.not_found()

            image_data = base64.b64decode(person.qr_code_image)
            filename = f"qr_code_{person.name.replace(' ', '_')}.png"
            
            return request.make_response(
                image_data,
                headers=[
                    ('Content-Type', 'image/png'),
                    ('Content-Disposition', f'attachment; filename="{filename}"'),
                    ('Content-Length', len(image_data))
                ]
            )

        except Exception as e:
            _logger.error(f"Erreur lors du téléchargement QR image {person_id}: {e}")
            return request.not_found()

    # Notifications
    @http.route('/api/persons/<int:person_id>/send-absence-notification', type='json', auth='user', methods=['POST'])
    def send_absence_notification(self, person_id, **kwargs):
        """Envoie une notification d'absence aux parents"""
        try:
            person = request.env['res.partner'].browse(person_id)
            if not person.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            data = request.get_json_data()
            session_name = data.get('session_name') if data else None

            success = person.send_absence_notification(session_name)

            return {
                'status': 'success' if success else 'warning',
                'data': {
                    'notification_sent': success,
                    'parent_email': person.parent_email,
                    'parent_phone': person.parent_phone,
                    'notify_enabled': person.notify_parents_absence
                },
                'message': _('Notification envoyée') if success else _('Notification non envoyée')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi de notification {person_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Recherche et statistiques
    @http.route('/api/persons/search', type='json', auth='user', methods=['POST'])
    def search_persons(self, **kwargs):
        """Recherche avancée de personnes"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Critères de recherche manquants')
                }

            domain = [('is_company', '=', False)]
            
            # Recherche par texte
            if data.get('search_term'):
                term = data['search_term']
                domain.extend([
                    '|', '|', '|', '|',
                    ('name', 'ilike', term),
                    ('student_code', 'ilike', term),
                    ('teacher_code', 'ilike', term),
                    ('email', 'ilike', term),
                    ('badge_number', 'ilike', term)
                ])

            # Filtres de type
            if data.get('person_types'):
                type_domain = []
                if 'student' in data['person_types']:
                    type_domain.append(('is_student', '=', True))
                if 'teacher' in data['person_types']:
                    type_domain.append(('is_teacher', '=', True))
                
                if type_domain:
                    if len(type_domain) > 1:
                        domain.append('|')
                    domain.extend(type_domain)

            # Filtres de données
            if data.get('has_biometric') is not None:
                domain.append(('has_biometric_data', '=', data['has_biometric']))
            
            if data.get('has_badge') is not None:
                if data['has_badge']:
                    domain.append(('badge_number', '!=', False))
                else:
                    domain.append(('badge_number', '=', False))

            limit = data.get('limit', 50)
            persons = request.env['res.partner'].search(domain, limit=limit)

            return {
                'status': 'success',
                'data': [self._format_person(person) for person in persons],
                'count': len(persons)
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la recherche de personnes: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/persons/statistics', type='json', auth='user', methods=['GET'])
    def get_persons_statistics(self, **kwargs):
        """Récupère les statistiques des personnes"""
        try:
            # Comptages généraux
            total_persons = request.env['res.partner'].search_count([
                ('is_company', '=', False),
                '|', '|',
                ('is_student', '=', True),
                ('is_teacher', '=', True),
                ('student_code', '!=', False)
            ])
            
            students_count = request.env['res.partner'].search_count([('is_student', '=', True)])
            teachers_count = request.env['res.partner'].search_count([('is_teacher', '=', True)])
            
            # Données biométriques
            with_biometric = request.env['res.partner'].search_count([('has_biometric_data', '=', True)])
            
            # Badges
            with_badge = request.env['res.partner'].search_count([
                ('badge_number', '!=', False),
                ('is_company', '=', False)
            ])
            
            with_rfid = request.env['res.partner'].search_count([
                ('rfid_code', '!=', False),
                ('is_company', '=', False)
            ])

            # Moyennes de présence (sur les 30 derniers jours)
            date_30_days_ago = fields.Date.today() - timedelta(days=30)
            students_with_attendance = request.env['res.partner'].search([
                ('is_student', '=', True),
                ('attendance_record_ids', '!=', False)
            ])
            
            avg_attendance_rate = 0
            if students_with_attendance:
                total_rate = sum(students_with_attendance.mapped('attendance_rate'))
                avg_attendance_rate = total_rate / len(students_with_attendance)

            return {
                'status': 'success',
                'data': {
                    'summary': {
                        'total_persons': total_persons,
                        'students_count': students_count,
                        'teachers_count': teachers_count,
                        'with_biometric': with_biometric,
                        'with_badge': with_badge,
                        'with_rfid': with_rfid,
                        'avg_attendance_rate': round(avg_attendance_rate, 2)
                    },
                    'coverage': {
                        'biometric_coverage': (with_biometric / total_persons * 100) if total_persons else 0,
                        'badge_coverage': (with_badge / total_persons * 100) if total_persons else 0,
                        'rfid_coverage': (with_rfid / total_persons * 100) if total_persons else 0
                    }
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _format_person(self, person, detailed=False):
        """Formate les données d'une personne pour l'API"""
        data = {
            'id': person.id,
            'name': person.name,
            'email': person.email,
            'phone': person.phone,
            'is_student': person.is_student,
            'is_teacher': person.is_teacher,
            'student_code': person.student_code,
            'teacher_code': person.teacher_code,
            'badge_number': person.badge_number,
            'rfid_code': person.rfid_code,
            'has_biometric_data': person.has_biometric_data,
            'allow_mobile_checkin': person.allow_mobile_checkin,
            'require_location_checkin': person.require_location_checkin,
            'attendance_stats': {
                'total_records': person.total_attendance_records,
                'present_count': person.present_count,
                'absent_count': person.absent_count,
                'late_count': person.late_count,
                'excused_count': person.excused_count,
                'attendance_rate': person.attendance_rate,
                'absence_rate': person.absence_rate
            },
            'create_date': person.create_date.isoformat() if person.create_date else None
        }

        if detailed:
            data.update({
                'personal_qr_code': person.personal_qr_code,
                'has_qr_image': bool(person.qr_code_image),
                'max_late_minutes': person.max_late_minutes,
                'notification_settings': {
                    'notify_parents_absence': person.notify_parents_absence,
                    'parent_email': person.parent_email,
                    'parent_phone': person.parent_phone
                },
                'last_activities': {
                    'last_attendance_date': person.last_attendance_date.isoformat() if person.last_attendance_date else None,
                    'last_session_taught': person.last_session_taught.isoformat() if person.last_session_taught else None
                },
                'biometric_data_count': len(person.biometric_data_ids),
                'attendance_records_count': len(person.attendance_record_ids),
                'excuses_count': len(person.excuse_ids),
                'taught_sessions_count': len(person.taught_session_ids) if person.is_teacher else 0,
                'write_date': person.write_date.isoformat() if person.write_date else None
            })

        return data

    def _format_attendance_record(self, record):
        """Formate un enregistrement de présence"""
        return {
            'id': record.id,
            'session': {
                'id': record.session_id.id if record.session_id else None,
                'name': record.session_id.name if record.session_id else None
            },
            'check_in_time': record.check_in_time.isoformat() if record.check_in_time else None,
            'check_out_time': record.check_out_time.isoformat() if record.check_out_time else None,
            'attendance_status': record.attendance_status,
            'is_late': record.is_late,
            'late_minutes': record.late_minutes,
            'hours_present': record.hours_present,
            'presence_rate': record.presence_rate,
            'is_excused': record.is_excused,
            'validated': record.validated,
            'device': {
                'id': record.device_id.id if record.device_id else None,
                'name': record.device_id.name if record.device_id else None
            },
            'create_date': record.create_date.isoformat() if record.create_date else None
        }

    def _format_excuse(self, excuse):
        """Formate un justificatif"""
        return {
            'id': excuse.id,
            'name': excuse.name,
            'excuse_type': excuse.excuse_type,
            'date': excuse.date.isoformat() if excuse.date else None,
            'reason': excuse.reason,
            'state': excuse.state,
            'description': excuse.description,
            'approved_by': {
                'id': excuse.approved_by.id if excuse.approved_by else None,
                'name': excuse.approved_by.name if excuse.approved_by else None
            },
            'approval_date': excuse.approval_date.isoformat() if excuse.approval_date else None,
            'create_date': excuse.create_date.isoformat() if excuse.create_date else None
        }

    def _prepare_person_data(self, data):
        """Prépare les données pour la création/mise à jour"""
        allowed_fields = [
            'name', 'email', 'phone', 'is_student', 'is_teacher', 'student_code',
            'teacher_code', 'badge_number', 'rfid_code', 'allow_mobile_checkin',
            'require_location_checkin', 'max_late_minutes', 'notify_parents_absence',
            'parent_email', 'parent_phone'
        ]
        
        person_data = {}
        for field in allowed_fields:
            if field in data:
                person_data[field] = data[field]
        
        return person_data


class ResPartnerAttendancePublicController(http.Controller):
    """Contrôleur API public pour les personnes (accès limité)"""

    @http.route('/api/public/persons/verify', type='json', auth='public', methods=['POST'])
    def public_verify_person(self, **kwargs):
        """Vérifie l'existence d'une personne par code avec authentification"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Vérification du token d'authentification
            if not data.get('auth_token'):
                return {
                    'status': 'error',
                    'message': _('Token d\'authentification requis')
                }

            if not self._validate_auth_token(data['auth_token']):
                return {
                    'status': 'error',
                    'message': _('Token d\'authentification invalide')
                }

            # Recherche de la personne
            code = data.get('code')
            if not code:
                return {
                    'status': 'error',
                    'message': _('Code requis')
                }

            person = request.env['res.partner'].sudo().search([
                '|',
                ('student_code', '=', code),
                ('teacher_code', '=', code)
            ], limit=1)

            if not person:
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            # Retourner uniquement les données publiques
            return {
                'status': 'success',
                'data': {
                    'id': person.id,
                    'name': person.name,
                    'type': 'student' if person.is_student else 'teacher',
                    'code': code,
                    'allow_mobile_checkin': person.allow_mobile_checkin,
                    'require_location_checkin': person.require_location_checkin,
                    'has_biometric_data': person.has_biometric_data
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la vérification publique de personne: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la vérification')
            }

    @http.route('/api/public/persons/by-badge', type='json', auth='public', methods=['POST'])
    def public_verify_by_badge(self, **kwargs):
        """Vérifie une personne par numéro de badge ou RFID"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Vérification du token d'authentification
            if not data.get('auth_token'):
                return {
                    'status': 'error',
                    'message': _('Token d\'authentification requis')
                }

            if not self._validate_auth_token(data['auth_token']):
                return {
                    'status': 'error',
                    'message': _('Token d\'authentification invalide')
                }

            badge_number = data.get('badge_number')
            rfid_code = data.get('rfid_code')

            if not badge_number and not rfid_code:
                return {
                    'status': 'error',
                    'message': _('Numéro de badge ou code RFID requis')
                }

            # Recherche par badge ou RFID
            domain = [('is_company', '=', False)]
            if badge_number:
                domain.append(('badge_number', '=', badge_number))
            elif rfid_code:
                domain.append(('rfid_code', '=', rfid_code))

            person = request.env['res.partner'].sudo().search(domain, limit=1)

            if not person:
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée avec ce badge/RFID')
                }

            return {
                'status': 'success',
                'data': {
                    'id': person.id,
                    'name': person.name,
                    'type': 'student' if person.is_student else 'teacher',
                    'student_code': person.student_code,
                    'teacher_code': person.teacher_code,
                    'allow_mobile_checkin': person.allow_mobile_checkin,
                    'require_location_checkin': person.require_location_checkin
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la vérification par badge: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la vérification')
            }

    @http.route('/api/public/persons/attendance-status', type='json', auth='public', methods=['POST'])
    def public_get_attendance_status(self, **kwargs):
        """Récupère le statut de présence public d'une personne"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Vérification du token d'authentification
            if not data.get('auth_token'):
                return {
                    'status': 'error',
                    'message': _('Token d\'authentification requis')
                }

            if not self._validate_auth_token(data['auth_token']):
                return {
                    'status': 'error',
                    'message': _('Token d\'authentification invalide')
                }

            person_id = data.get('person_id')
            if not person_id:
                return {
                    'status': 'error',
                    'message': _('ID de personne requis')
                }

            person = request.env['res.partner'].sudo().browse(person_id)
            if not person.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            # Statut du jour
            today_status = person.check_attendance_today()

            return {
                'status': 'success',
                'data': {
                    'person_name': person.name,
                    'today_status': today_status,
                    'attendance_rate': person.attendance_rate,
                    'last_attendance': person.last_attendance_date.isoformat() if person.last_attendance_date else None
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du statut public: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la récupération du statut')
            }

    def _validate_auth_token(self, token):
        """Valide le token d'authentification pour l'API publique"""
        try:
            # Implémentation de validation de token à personnaliser
            valid_tokens = request.env['ir.config_parameter'].sudo().get_param('attendance.api.tokens', '').split(',')
            return token.strip() in [t.strip() for t in valid_tokens if t.strip()]
        except Exception:
            return False


class ResPartnerBulkController(http.Controller):
    """Contrôleur pour les opérations en lot sur les personnes"""

    @http.route('/api/persons/bulk/import', type='json', auth='user', methods=['POST'])
    def bulk_import_persons(self, **kwargs):
        """Importe plusieurs personnes en lot"""
        try:
            data = request.get_json_data()
            if not data or not data.get('persons'):
                return {
                    'status': 'error',
                    'message': _('Liste de personnes manquante')
                }

            created_persons = []
            updated_persons = []
            errors = []

            for person_data in data['persons']:
                try:
                    # Vérifier si la personne existe déjà
                    existing_person = None
                    if person_data.get('student_code'):
                        existing_person = request.env['res.partner'].search([
                            ('student_code', '=', person_data['student_code'])
                        ], limit=1)
                    elif person_data.get('teacher_code'):
                        existing_person = request.env['res.partner'].search([
                            ('teacher_code', '=', person_data['teacher_code'])
                        ], limit=1)
                    elif person_data.get('email'):
                        existing_person = request.env['res.partner'].search([
                            ('email', '=', person_data['email'])
                        ], limit=1)

                    controller = ResPartnerAttendanceController()
                    prepared_data = controller._prepare_person_data(person_data)
                    prepared_data['is_company'] = False

                    if existing_person:
                        # Mise à jour
                        existing_person.write(prepared_data)
                        updated_persons.append(controller._format_person(existing_person))
                    else:
                        # Création
                        if not person_data.get('name'):
                            errors.append(f"Nom manquant pour une entrée")
                            continue
                            
                        new_person = request.env['res.partner'].create(prepared_data)
                        created_persons.append(controller._format_person(new_person))

                except Exception as e:
                    error_msg = f"Erreur pour {person_data.get('name', 'entrée inconnue')}: {str(e)}"
                    errors.append(error_msg)

            return {
                'status': 'success' if not errors else 'partial',
                'data': {
                    'created_persons': created_persons,
                    'updated_persons': updated_persons,
                    'created_count': len(created_persons),
                    'updated_count': len(updated_persons),
                    'error_count': len(errors),
                    'errors': errors
                },
                'message': f'{len(created_persons)} créées, {len(updated_persons)} mises à jour'
            }

        except Exception as e:
            _logger.error(f"Erreur lors de l'import en lot: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/persons/bulk/generate-codes', type='json', auth='user', methods=['POST'])
    def bulk_generate_codes(self, **kwargs):
        """Génère des codes pour plusieurs personnes"""
        try:
            data = request.get_json_data()
            if not data or not data.get('person_ids'):
                return {
                    'status': 'error',
                    'message': _('IDs des personnes manquants')
                }

            person_type = data.get('type', 'student')  # 'student' ou 'teacher'
            prefix = data.get('prefix', 'STU' if person_type == 'student' else 'TEA')
            start_number = data.get('start_number', 1)

            persons = request.env['res.partner'].browse(data['person_ids'])
            updated_persons = []
            errors = []

            counter = start_number
            for person in persons:
                try:
                    # Générer le code
                    new_code = f"{prefix}{counter:04d}"
                    
                    # Vérifier l'unicité
                    field_name = 'student_code' if person_type == 'student' else 'teacher_code'
                    existing = request.env['res.partner'].search([
                        (field_name, '=', new_code),
                        ('id', '!=', person.id)
                    ])
                    
                    if existing:
                        errors.append(f"Code {new_code} déjà utilisé pour {person.name}")
                        continue

                    # Mettre à jour
                    update_data = {
                        field_name: new_code,
                        'is_student': person_type == 'student',
                        'is_teacher': person_type == 'teacher'
                    }
                    person.write(update_data)
                    
                    controller = ResPartnerAttendanceController()
                    updated_persons.append(controller._format_person(person))
                    counter += 1

                except Exception as e:
                    errors.append(f"Erreur pour {person.name}: {str(e)}")

            return {
                'status': 'success' if not errors else 'partial',
                'data': {
                    'updated_persons': updated_persons,
                    'updated_count': len(updated_persons),
                    'error_count': len(errors),
                    'errors': errors,
                    'next_available_number': counter
                },
                'message': f'{len(updated_persons)} codes générés avec succès'
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la génération de codes en lot: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/persons/bulk/export', type='json', auth='user', methods=['POST'])
    def bulk_export_persons(self, **kwargs):
        """Exporte les données de personnes"""
        try:
            data = request.get_json_data()
            domain = [('is_company', '=', False)]
            
            # Filtres d'export
            if data and data.get('filters'):
                filters = data['filters']
                if filters.get('is_student'):
                    domain.append(('is_student', '=', True))
                if filters.get('is_teacher'):
                    domain.append(('is_teacher', '=', True))
                if filters.get('has_biometric'):
                    domain.append(('has_biometric_data', '=', True))

            persons = request.env['res.partner'].search(domain)
            
            export_data = []
            controller = ResPartnerAttendanceController()
            
            for person in persons:
                export_data.append(controller._format_person(person, detailed=True))

            return {
                'status': 'success',
                'data': {
                    'persons': export_data,
                    'count': len(export_data),
                    'export_date': fields.Datetime.now().isoformat()
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de l'export en lot: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }