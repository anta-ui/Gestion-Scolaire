# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime, timedelta
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError, UserError
from odoo.http import serialize_exception

_logger = logging.getLogger(__name__)


class EduAttendanceSessionController(http.Controller):
    """Contrôleur API pour la gestion des sessions de présence"""

    @http.route('/api/attendance/sessions', type='json', auth='user', methods=['GET'])
    def get_sessions(self, **kwargs):
        """Récupère toutes les sessions de présence"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            
            if kwargs.get('session_type'):
                domain.append(('session_type', '=', kwargs['session_type']))
                
            if kwargs.get('course_id'):
                domain.append(('course_id', '=', kwargs['course_id']))
                
            if kwargs.get('teacher_id'):
                domain.append(('teacher_id', '=', kwargs['teacher_id']))
                
            if kwargs.get('standard_id'):
                domain.append(('standard_id', '=', kwargs['standard_id']))
                
            if kwargs.get('classroom_id'):
                domain.append(('classroom_id', '=', kwargs['classroom_id']))
                
            if kwargs.get('date_from'):
                domain.append(('start_datetime', '>=', kwargs['date_from']))
                
            if kwargs.get('date_to'):
                domain.append(('start_datetime', '<=', kwargs['date_to']))
                
            if kwargs.get('today'):
                today = fields.Date.context_today(request.env['edu.attendance.session'])
                domain.extend([
                    ('start_datetime', '>=', f"{today} 00:00:00"),
                    ('start_datetime', '<=', f"{today} 23:59:59")
                ])
                
            if kwargs.get('this_week'):
                today = fields.Date.context_today(request.env['edu.attendance.session'])
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)
                domain.extend([
                    ('start_datetime', '>=', f"{week_start} 00:00:00"),
                    ('start_datetime', '<=', f"{week_end} 23:59:59")
                ])

            # Pagination
            limit = kwargs.get('limit', 100)
            offset = kwargs.get('offset', 0)
            
            sessions = request.env['edu.attendance.session'].search(
                domain, 
                limit=limit, 
                offset=offset,
                order='start_datetime desc, id desc'
            )
            
            total_count = request.env['edu.attendance.session'].search_count(domain)
            
            return {
                'status': 'success',
                'data': [self._format_session(session) for session in sessions],
                'count': len(sessions),
                'total_count': total_count
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des sessions: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/<int:session_id>', type='json', auth='user', methods=['GET'])
    def get_session(self, session_id, **kwargs):
        """Récupère une session spécifique"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }
            
            return {
                'status': 'success',
                'data': self._format_session(session, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/by-code/<string:code>', type='json', auth='user', methods=['GET'])
    def get_session_by_code(self, code, **kwargs):
        """Récupère une session par son code"""
        try:
            session = request.env['edu.attendance.session'].search([('code', '=', code)], limit=1)
            if not session:
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }
            
            return {
                'status': 'success',
                'data': self._format_session(session, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la session {code}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions', type='json', auth='user', methods=['POST'])
    def create_session(self, **kwargs):
        """Crée une nouvelle session"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des données obligatoires
            required_fields = ['name', 'session_type', 'start_datetime', 'end_datetime']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'status': 'error',
                        'message': _('Le champ %s est obligatoire') % field
                    }

            # Validation des dates
            try:
                start_dt = datetime.fromisoformat(data['start_datetime'].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(data['end_datetime'].replace('Z', '+00:00'))
                
                if start_dt >= end_dt:
                    return {
                        'status': 'error',
                        'message': _('La date de début doit être antérieure à la date de fin')
                    }
            except ValueError:
                return {
                    'status': 'error',
                    'message': _('Format de date invalide')
                }

            # Préparation des données
            session_data = self._prepare_session_data(data)
            session = request.env['edu.attendance.session'].create(session_data)

            # Auto-programmer si demandé
            if data.get('auto_schedule', False):
                session.action_schedule()

            return {
                'status': 'success',
                'data': self._format_session(session, detailed=True),
                'message': _('Session créée avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la session: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/<int:session_id>', type='json', auth='user', methods=['PUT'])
    def update_session(self, session_id, **kwargs):
        """Met à jour une session existante"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            # Vérifier si la session peut être modifiée
            if session.state in ['closed', 'cancelled']:
                return {
                    'status': 'error',
                    'message': _('Impossible de modifier une session fermée ou annulée')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Préparation des données
            session_data = self._prepare_session_data(data)
            session.write(session_data)

            return {
                'status': 'success',
                'data': self._format_session(session, detailed=True),
                'message': _('Session mise à jour avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour de la session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/<int:session_id>', type='json', auth='user', methods=['DELETE'])
    def delete_session(self, session_id, **kwargs):
        """Supprime une session"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            # Vérifier si la session peut être supprimée
            if session.state in ['in_progress', 'closed']:
                return {
                    'status': 'error',
                    'message': _('Impossible de supprimer une session en cours ou fermée')
                }

            session.unlink()

            return {
                'status': 'success',
                'message': _('Session supprimée avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la suppression de la session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Actions de workflow
    @http.route('/api/attendance/sessions/<int:session_id>/schedule', type='json', auth='user', methods=['POST'])
    def schedule_session(self, session_id, **kwargs):
        """Programme la session"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            session.action_schedule()

            return {
                'status': 'success',
                'data': self._format_session(session),
                'message': _('Session programmée avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la programmation de la session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/<int:session_id>/open', type='json', auth='user', methods=['POST'])
    def open_session(self, session_id, **kwargs):
        """Ouvre la session pour les pointages"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            session.action_open()

            return {
                'status': 'success',
                'data': self._format_session(session),
                'message': _('Session ouverte avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de l'ouverture de la session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/<int:session_id>/start', type='json', auth='user', methods=['POST'])
    def start_session(self, session_id, **kwargs):
        """Démarre la session"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            session.action_start()

            return {
                'status': 'success',
                'data': self._format_session(session),
                'message': _('Session démarrée avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors du démarrage de la session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/<int:session_id>/close', type='json', auth='user', methods=['POST'])
    def close_session(self, session_id, **kwargs):
        """Ferme la session"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            session.action_close()

            return {
                'status': 'success',
                'data': self._format_session(session),
                'message': _('Session fermée avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la fermeture de la session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/<int:session_id>/cancel', type='json', auth='user', methods=['POST'])
    def cancel_session(self, session_id, **kwargs):
        """Annule la session"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            session.action_cancel()

            return {
                'status': 'success',
                'data': self._format_session(session),
                'message': _('Session annulée avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de l'annulation de la session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/<int:session_id>/reopen', type='json', auth='user', methods=['POST'])
    def reopen_session(self, session_id, **kwargs):
        """Réouvre la session"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            session.action_reopen()

            return {
                'status': 'success',
                'data': self._format_session(session),
                'message': _('Session réouverte avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la réouverture de la session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Gestion des participants
    @http.route('/api/attendance/sessions/<int:session_id>/participants', type='json', auth='user', methods=['GET'])
    def get_session_participants(self, session_id, **kwargs):
        """Récupère les participants d'une session avec leur statut de présence"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            participants = []
            
            # Étudiants
            for student in session.student_ids:
                attendance_record = session.get_participant_attendance(student.id, 'student')
                participants.append({
                    'type': 'student',
                    'id': student.id,
                    'name': student.name,
                    'code': student.code if hasattr(student, 'code') else None,
                    'attendance': self._format_attendance_record(attendance_record) if attendance_record else None
                })
            
            # Enseignants
            for teacher in session.teacher_ids:
                attendance_record = session.get_participant_attendance(teacher.id, 'teacher')
                participants.append({
                    'type': 'teacher',
                    'id': teacher.id,
                    'name': teacher.name,
                    'code': teacher.teacher_code if hasattr(teacher, 'teacher_code') else None,
                    'attendance': self._format_attendance_record(attendance_record) if attendance_record else None
                })

            return {
                'status': 'success',
                'data': {
                    'session_id': session.id,
                    'session_name': session.name,
                    'participants': participants,
                    'total_expected': session.expected_count,
                    'total_present': session.present_count,
                    'attendance_rate': session.attendance_rate
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des participants {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/<int:session_id>/add-participants', type='json', auth='user', methods=['POST'])
    def add_participants(self, session_id, **kwargs):
        """Ajoute des participants à la session"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            added_count = 0

            # Ajouter des étudiants
            if data.get('student_ids'):
                new_students = request.env['op.student'].browse(data['student_ids'])
                session.student_ids = [(4, student.id) for student in new_students]
                added_count += len(new_students)

            # Ajouter des enseignants
            if data.get('faculty_ids'):
                new_faculties = request.env['op.faculty'].browse(data['faculty_ids'])
                session.faculty_ids = [(4, faculty.id) for faculty in new_faculties]
                added_count += len(new_faculties)

            # Recréer les enregistrements de présence si la session est ouverte
            if session.state in ['open', 'in_progress']:
                session._create_attendance_records()

            return {
                'status': 'success',
                'data': self._format_session(session),
                'message': f'{added_count} participants ajoutés avec succès'
            }

        except Exception as e:
            _logger.error(f"Erreur lors de l'ajout de participants à la session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/<int:session_id>/remove-participants', type='json', auth='user', methods=['POST'])
    def remove_participants(self, session_id, **kwargs):
        """Retire des participants de la session"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            removed_count = 0

            # Retirer des étudiants
            if data.get('student_ids'):
                session.student_ids = [(3, student_id) for student_id in data['student_ids']]
                
                # Supprimer les enregistrements de présence associés
                attendance_records = request.env['edu.attendance.record'].search([
                    ('session_id', '=', session.id),
                    ('student_id', 'in', data['student_ids'])
                ])
                attendance_records.unlink()
                removed_count += len(data['student_ids'])

            # Retirer des enseignants
            if data.get('teacher_ids'):
                session.teacher_ids = [(3, teacher_id) for teacher_id in data['teacher_ids']]
                
                # Supprimer les enregistrements de présence associés
                attendance_records = request.env['edu.attendance.record'].search([
                    ('session_id', '=', session.id),
                    ('teacher_id', 'in', data['teacher_ids'])
                ])
                attendance_records.unlink()
                removed_count += len(data['teacher_ids'])

            return {
                'status': 'success',
                'data': self._format_session(session),
                'message': f'{removed_count} participants retirés avec succès'
            }

        except Exception as e:
            _logger.error(f"Erreur lors du retrait de participants de la session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # QR Code et dispositifs
    @http.route('/api/attendance/sessions/<int:session_id>/qr-code', type='json', auth='user', methods=['GET'])
    def get_session_qr_code(self, session_id, **kwargs):
        """Récupère le QR code de la session"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            if not session.qr_code_id:
                session._generate_qr_code()

            qr_code = session.qr_code_id
            return {
                'status': 'success',
                'data': {
                    'id': qr_code.id,
                    'name': qr_code.name,
                    'content': qr_code.content if hasattr(qr_code, 'content') else None,
                    'qr_image': qr_code.qr_image if hasattr(qr_code, 'qr_image') else None,
                    'expiry_date': qr_code.expiry_date.isoformat() if qr_code.expiry_date else None,
                    'active': qr_code.active
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du QR code {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/<int:session_id>/devices', type='json', auth='user', methods=['GET'])
    def get_session_devices(self, session_id, **kwargs):
        """Récupère les dispositifs autorisés pour la session"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            devices = []
            for device in session.attendance_device_ids:
                devices.append({
                    'id': device.id,
                    'name': device.name,
                    'code': device.code,
                    'device_type': device.device_type,
                    'active': device.active,
                    'online': device.online if hasattr(device, 'online') else False
                })

            return {
                'status': 'success',
                'data': devices
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des dispositifs {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Statistiques et rapports
    @http.route('/api/attendance/sessions/<int:session_id>/statistics', type='json', auth='user', methods=['GET'])
    def get_session_statistics(self, session_id, **kwargs):
        """Récupère les statistiques détaillées de la session"""
        try:
            session = request.env['edu.attendance.session'].browse(session_id)
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            # Statistiques de base
            total_expected = session.expected_count
            present_count = session.present_count
            absent_count = session.absent_count
            late_count = session.late_count
            excused_count = session.excused_count

            # Statistiques avancées
            records = session.attendance_record_ids
            avg_check_in_delay = 0
            checked_out_count = len(records.filtered('check_out_time'))
            
            if records:
                delays = []
                for record in records.filtered(lambda r: r.check_in_time and r.expected_check_in):
                    delay = (record.check_in_time - record.expected_check_in).total_seconds() / 60
                    delays.append(delay)
                
                if delays:
                    avg_check_in_delay = sum(delays) / len(delays)

            return {
                'status': 'success',
                'data': {
                    'session_info': {
                        'id': session.id,
                        'name': session.name,
                        'code': session.code,
                        'state': session.state,
                        'duration': session.duration,
                        'attendance_rate': session.attendance_rate
                    },
                    'attendance_summary': {
                        'total_expected': total_expected,
                        'present_count': present_count,
                        'absent_count': absent_count,
                        'late_count': late_count,
                        'excused_count': excused_count,
                        'checked_out_count': checked_out_count
                    },
                    'percentages': {
                        'present_rate': (present_count / total_expected * 100) if total_expected else 0,
                        'absent_rate': (absent_count / total_expected * 100) if total_expected else 0,
                        'late_rate': (late_count / total_expected * 100) if total_expected else 0,
                        'excused_rate': (excused_count / total_expected * 100) if total_expected else 0,
                        'checkout_rate': (checked_out_count / present_count * 100) if present_count else 0
                    },
                    'timing': {
                        'average_check_in_delay_minutes': round(avg_check_in_delay, 2),
                        'check_in_window_open': session.is_check_in_open(),
                        'check_out_window_open': session.is_check_out_open()
                    }
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des statistiques {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Fonctions de recherche et filtrage
    @http.route('/api/attendance/sessions/search', type='json', auth='user', methods=['POST'])
    def search_sessions(self, **kwargs):
        """Recherche avancée de sessions"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Critères de recherche manquants')
                }

            domain = []
            
            # Recherche par texte
            if data.get('search_term'):
                term = data['search_term']
                domain.append('|')
                domain.append(('name', 'ilike', term))
                domain.append(('code', 'ilike', term))

            # Filtres multiples
            if data.get('states'):
                domain.append(('state', 'in', data['states']))
                
            if data.get('session_types'):
                domain.append(('session_type', 'in', data['session_types']))
                
            if data.get('teacher_ids'):
                domain.append('|')
                domain.append(('faculty_id', 'in', data['teacher_ids']))
                domain.append(('teacher_id', 'in', data['teacher_ids']))

            # Période
            if data.get('date_range'):
                date_range = data['date_range']
                if date_range.get('start'):
                    domain.append(('start_datetime', '>=', date_range['start']))
                if date_range.get('end'):
                    domain.append(('end_datetime', '<=', date_range['end']))

            limit = data.get('limit', 50)
            sessions = request.env['edu.attendance.session'].search(domain, limit=limit)

            return {
                'status': 'success',
                'data': [self._format_session(session) for session in sessions],
                'count': len(sessions)
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la recherche de sessions: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/dashboard', type='json', auth='user', methods=['GET'])
    def get_dashboard_data(self, **kwargs):
        """Récupère les données pour le tableau de bord"""
        try:
            today = fields.Date.context_today(request.env['edu.attendance.session'])
            
            # Sessions d'aujourd'hui
            today_sessions = request.env['edu.attendance.session'].search([
                ('start_datetime', '>=', f"{today} 00:00:00"),
                ('start_datetime', '<=', f"{today} 23:59:59")
            ])

            # Sessions en cours
            active_sessions = request.env['edu.attendance.session'].search([
                ('state', 'in', ['open', 'in_progress'])
            ])

            # Sessions à venir (prochaines 24h)
            tomorrow = today + timedelta(days=1)
            upcoming_sessions = request.env['edu.attendance.session'].search([
                ('start_datetime', '>=', f"{today} 23:59:59"),
                ('start_datetime', '<=', f"{tomorrow} 23:59:59"),
                ('state', 'in', ['draft', 'scheduled'])
            ])

            # Statistiques globales
            total_today = len(today_sessions)
            completed_today = len(today_sessions.filtered(lambda s: s.state == 'closed'))
            cancelled_today = len(today_sessions.filtered(lambda s: s.state == 'cancelled'))

            # Calcul du taux de présence moyen d'aujourd'hui
            avg_attendance_rate = 0
            if today_sessions:
                rates = [s.attendance_rate for s in today_sessions if s.attendance_rate > 0]
                avg_attendance_rate = sum(rates) / len(rates) if rates else 0

            return {
                'status': 'success',
                'data': {
                    'summary': {
                        'today_total': total_today,
                        'today_completed': completed_today,
                        'today_cancelled': cancelled_today,
                        'active_count': len(active_sessions),
                        'upcoming_count': len(upcoming_sessions),
                        'avg_attendance_rate': round(avg_attendance_rate, 2)
                    },
                    'today_sessions': [self._format_session(s) for s in today_sessions[:10]],
                    'active_sessions': [self._format_session(s) for s in active_sessions[:5]],
                    'upcoming_sessions': [self._format_session(s) for s in upcoming_sessions[:5]]
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des données du tableau de bord: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/sessions/options', type='json', auth='user', methods=['GET'])
    def get_session_options(self, **kwargs):
        """Récupère les options disponibles pour les sessions"""
        try:
            session_types = request.env['edu.attendance.session']._fields['session_type'].selection
            states = request.env['edu.attendance.session']._fields['state'].selection
            timezones = request.env['edu.attendance.session']._fields['timezone'].selection
            
            return {
                'status': 'success',
                'data': {
                    'session_types': [{'value': value, 'label': label} for value, label in session_types],
                    'states': [{'value': value, 'label': label} for value, label in states],
                    'timezones': [{'value': value, 'label': label} for value, label in timezones]
                }
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des options: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _format_session(self, session, detailed=False):
        """Formate les données de la session pour l'API"""
        data = {
            'id': session.id,
            'name': session.name,
            'code': session.code,
            'session_type': session.session_type,
            'state': session.state,
            'start_datetime': session.start_datetime.isoformat() if session.start_datetime else None,
            'end_datetime': session.end_datetime.isoformat() if session.end_datetime else None,
            'duration': session.duration,
            'timezone': session.timezone,
            'course': {
                'id': session.course_id.id if session.course_id else None,
                'name': session.course_id.name if session.course_id else None
            },
            'teacher': {
                'id': session.teacher_id.id if session.teacher_id else None,
                'name': session.teacher_id.name if session.teacher_id else None
            },
            'location': {
                'classroom_id': session.classroom_id.id if session.classroom_id else None,
                'classroom_name': session.classroom_id.name if session.classroom_id else None,
                'location_id': session.location_id.id if session.location_id else None,
                'location_name': session.location_id.name if session.location_id else None,
                'external_location': session.external_location
            },
            'attendance_stats': {
                'expected_count': session.expected_count,
                'present_count': session.present_count,
                'absent_count': session.absent_count,
                'late_count': session.late_count,
                'excused_count': session.excused_count,
                'attendance_rate': session.attendance_rate
            },
            'windows': {
                'check_in_open': session.is_check_in_open(),
                'check_out_open': session.is_check_out_open()
            },
            'create_date': session.create_date.isoformat() if session.create_date else None
        }

        if detailed:
            data.update({
                'description': session.description,
                'standard': {
                    'id': session.standard_id.id if session.standard_id else None,
                    'name': session.standard_id.name if session.standard_id else None
                },
                'batch': {
                    'id': session.batch_id.id if session.batch_id else None,
                    'name': session.batch_id.name if session.batch_id else None
                },
                'coordinates': {
                    'latitude': session.latitude,
                    'longitude': session.longitude,
                    'gps_radius': session.gps_radius
                } if session.latitude and session.longitude else None,
                'check_windows': {
                    'check_in_start': session.check_in_start.isoformat() if session.check_in_start else None,
                    'check_in_end': session.check_in_end.isoformat() if session.check_in_end else None,
                    'check_out_start': session.check_out_start.isoformat() if session.check_out_start else None,
                    'check_out_end': session.check_out_end.isoformat() if session.check_out_end else None
                },
                'rules': {
                    'allow_late_check_in': session.allow_late_check_in,
                    'late_threshold': session.late_threshold,
                    'require_check_out': session.require_check_out,
                    'require_photo': session.require_photo,
                    'auto_close_session': session.auto_close_session
                },
                'notifications': {
                    'notify_parents': session.notify_parents,
                    'notify_delay': session.notify_delay,
                    'template_id': session.notification_template_id.id if session.notification_template_id else None
                },
                'participants': {
                    'student_count': len(session.student_ids),
                    'faculty_count': len(session.faculty_ids),
                    'device_count': len(session.attendance_device_ids)
                },
                'qr_code': {
                    'id': session.qr_code_id.id if session.qr_code_id else None,
                    'active': session.qr_code_id.active if session.qr_code_id else False
                },
                'metadata': {
                    'created_by': {
                        'id': session.created_by.id if session.created_by else None,
                        'name': session.created_by.name if session.created_by else None
                    },
                    'opened_date': session.opened_date.isoformat() if session.opened_date else None,
                    'closed_date': session.closed_date.isoformat() if session.closed_date else None
                },
                'write_date': session.write_date.isoformat() if session.write_date else None
            })

        return data

    def _format_attendance_record(self, record):
        """Formate un enregistrement de présence simplifié"""
        if not record:
            return None
            
        return {
            'id': record.id,
            'check_in_time': record.check_in_time.isoformat() if record.check_in_time else None,
            'check_out_time': record.check_out_time.isoformat() if record.check_out_time else None,
            'attendance_status': record.attendance_status,
            'is_late': record.is_late,
            'is_absent': record.is_absent,
            'is_excused': record.is_excused,
            'late_minutes': record.late_minutes,
            'hours_present': record.hours_present,
            'presence_rate': record.presence_rate,
            'validated': record.validated
        }

    def _prepare_session_data(self, data):
        """Prépare les données pour la création/mise à jour"""
        allowed_fields = [
            'name', 'code', 'description', 'session_type', 'start_datetime', 'end_datetime',
            'timezone', 'course_name', 'teacher_id', 'class_name', 'batch_name',
            'classroom_name', 'location_id', 'external_location', 'latitude', 'longitude',
            'gps_radius', 'check_in_start', 'check_in_end', 'check_out_start', 'check_out_end',
            'allow_late_check_in', 'late_threshold', 'require_check_out', 'require_photo',
            'auto_close_session', 'notify_parents', 'notify_delay', 'notification_template_id'
        ]
        
        session_data = {}
        for field in allowed_fields:
            if field in data:
                session_data[field] = data[field]
        
        # Gestion des relations Many2many
        if 'student_ids' in data:
            session_data['student_ids'] = [(6, 0, data['student_ids'])]
        
        if 'teacher_ids' in data:
            session_data['teacher_ids'] = [(6, 0, data['teacher_ids'])]
            
        if 'attendance_device_ids' in data:
            session_data['attendance_device_ids'] = [(6, 0, data['attendance_device_ids'])]
        
        return session_data


class EduAttendanceSessionPublicController(http.Controller):
    """Contrôleur API public pour les sessions de présence"""

    @http.route('/api/public/attendance/sessions/<string:code>/info', type='json', auth='public', methods=['GET'])
    def get_public_session_info(self, code, **kwargs):
        """Récupère les informations publiques d'une session"""
        try:
            session = request.env['edu.attendance.session'].sudo().search([
                ('code', '=', code)
            ], limit=1)
            
            if not session:
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            return {
                'status': 'success',
                'data': {
                    'id': session.id,
                    'name': session.name,
                    'code': session.code,
                    'session_type': session.session_type,
                    'state': session.state,
                    'start_datetime': session.start_datetime.isoformat() if session.start_datetime else None,
                    'end_datetime': session.end_datetime.isoformat() if session.end_datetime else None,
                    'duration': session.duration,
                    'location': {
                        'classroom_name': session.classroom_id.name if session.classroom_id else None,
                        'external_location': session.external_location
                    },
                    'check_windows': {
                        'check_in_open': session.is_check_in_open(),
                        'check_out_open': session.is_check_out_open(),
                        'check_in_start': session.check_in_start.isoformat() if session.check_in_start else None,
                        'check_in_end': session.check_in_end.isoformat() if session.check_in_end else None,
                        'check_out_start': session.check_out_start.isoformat() if session.check_out_start else None,
                        'check_out_end': session.check_out_end.isoformat() if session.check_out_end else None
                    },
                    'requirements': {
                        'require_photo': session.require_photo,
                        'require_check_out': session.require_check_out,
                        'late_threshold': session.late_threshold,
                        'allow_late_check_in': session.allow_late_check_in
                    },
                    'geolocation': {
                        'latitude': session.latitude,
                        'longitude': session.longitude,
                        'gps_radius': session.gps_radius
                    } if session.latitude and session.longitude else None
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des infos publiques de session {code}: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la récupération des informations')
            }

    @http.route('/api/public/attendance/sessions/<string:code>/validate', type='json', auth='public', methods=['POST'])
    def validate_session_access(self, code, **kwargs):
        """Valide l'accès à une session pour un participant"""
        try:
            data = request.get_json_data()
            if not data or not data.get('participant_code'):
                return {
                    'status': 'error',
                    'message': _('Code participant requis')
                }

            session = request.env['edu.attendance.session'].sudo().search([
                ('code', '=', code)
            ], limit=1)
            
            if not session:
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            participant_code = data['participant_code']
            
            # Vérifier si le participant est un étudiant
            student = request.env['op.student'].sudo().search([
                ('code', '=', participant_code)
            ], limit=1)
            
            participant_found = False
            participant_name = None
            participant_type = None
            
            if student and student.id in session.student_ids.ids:
                participant_found = True
                participant_name = student.name
                participant_type = 'student'
            else:
                # Vérifier si c'est un enseignant
                faculty = request.env['op.faculty'].sudo().search([
                    ('code', '=', participant_code)
                ], limit=1)
                
                if faculty and faculty.id in session.faculty_ids.ids:
                    participant_found = True
                    participant_name = faculty.name
                    participant_type = 'faculty'

            if not participant_found:
                return {
                    'status': 'error',
                    'message': _('Participant non autorisé pour cette session')
                }

            # Vérifier l'état de la session
            if session.state not in ['open', 'in_progress']:
                return {
                    'status': 'error',
                    'message': _('Session non ouverte pour les pointages')
                }

            return {
                'status': 'success',
                'data': {
                    'session_name': session.name,
                    'participant_name': participant_name,
                    'participant_type': participant_type,
                    'access_granted': True,
                    'session_state': session.state,
                    'can_check_in': session.is_check_in_open(),
                    'can_check_out': session.is_check_out_open()
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la validation d'accès session {code}: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la validation')
            }

    @http.route('/api/public/attendance/sessions/active', type='json', auth='public', methods=['GET'])
    def get_active_sessions(self, **kwargs):
        """Récupère les sessions actuellement actives (publiques)"""
        try:
            # Filtrer par localisation si fournie
            domain = [('state', 'in', ['open', 'in_progress'])]
            
            if kwargs.get('location_id'):
                domain.append(('location_id', '=', kwargs['location_id']))
            
            sessions = request.env['edu.attendance.session'].sudo().search(
                domain, 
                limit=20,
                order='start_datetime asc'
            )

            active_sessions = []
            for session in sessions:
                active_sessions.append({
                    'code': session.code,
                    'name': session.name,
                    'session_type': session.session_type,
                    'start_time': session.start_datetime.strftime('%H:%M') if session.start_datetime else None,
                    'end_time': session.end_datetime.strftime('%H:%M') if session.end_datetime else None,
                    'location': session.classroom_id.name if session.classroom_id else session.external_location,
                    'state': session.state,
                    'check_in_open': session.is_check_in_open(),
                    'check_out_open': session.is_check_out_open()
                })

            return {
                'status': 'success',
                'data': active_sessions,
                'count': len(active_sessions)
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des sessions actives: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la récupération des sessions actives')
            }