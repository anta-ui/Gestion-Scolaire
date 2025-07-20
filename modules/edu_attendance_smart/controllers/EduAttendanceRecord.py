# -*- coding: utf-8 -*-

import json
import logging
import base64
from datetime import datetime, timedelta
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError, UserError
from odoo.http import serialize_exception

_logger = logging.getLogger(__name__)


class EduAttendanceRecordController(http.Controller):
    """Contrôleur API pour la gestion des enregistrements de présence"""

    @http.route('/api/attendance/records', type='json', auth='user', methods=['GET'])
    def get_records(self, **kwargs):
        """Récupère tous les enregistrements de présence"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('session_id'):
                domain.append(('session_id', '=', kwargs['session_id']))
            
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', kwargs['student_id']))
                
            if kwargs.get('teacher_id'):
                domain.append(('teacher_id', '=', kwargs['teacher_id']))
                
            if kwargs.get('device_id'):
                domain.append(('device_id', '=', kwargs['device_id']))
                
            if kwargs.get('attendance_status'):
                domain.append(('attendance_status', '=', kwargs['attendance_status']))
                
            if kwargs.get('date_from'):
                domain.append(('check_in_time', '>=', kwargs['date_from']))
                
            if kwargs.get('date_to'):
                domain.append(('check_in_time', '<=', kwargs['date_to']))
                
            if kwargs.get('is_absent') is not None:
                domain.append(('is_absent', '=', kwargs['is_absent']))
                
            if kwargs.get('is_late') is not None:
                domain.append(('is_late', '=', kwargs['is_late']))
                
            if kwargs.get('validated') is not None:
                domain.append(('validated', '=', kwargs['validated']))

            # Pagination
            limit = kwargs.get('limit', 100)
            offset = kwargs.get('offset', 0)
            
            records = request.env['edu.attendance.record'].search(
                domain, 
                limit=limit, 
                offset=offset,
                order='check_in_time desc, id desc'
            )
            
            total_count = request.env['edu.attendance.record'].search_count(domain)
            
            return {
                'status': 'success',
                'data': [self._format_record(record) for record in records],
                'count': len(records),
                'total_count': total_count
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des enregistrements: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/<int:record_id>', type='json', auth='user', methods=['GET'])
    def get_record(self, record_id, **kwargs):
        """Récupère un enregistrement de présence spécifique"""
        try:
            record = request.env['edu.attendance.record'].browse(record_id)
            if not record.exists():
                return {
                    'status': 'error',
                    'message': _('Enregistrement non trouvé')
                }
            
            return {
                'status': 'success',
                'data': self._format_record(record, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de l'enregistrement {record_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records', type='json', auth='user', methods=['POST'])
    def create_record(self, **kwargs):
        """Crée un nouveau enregistrement de présence"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des données obligatoires
            if not data.get('session_id'):
                return {
                    'status': 'error',
                    'message': _('La session est obligatoire')
                }

            if not data.get('student_id') and not data.get('teacher_id'):
                return {
                    'status': 'error',
                    'message': _('Un étudiant ou un enseignant doit être spécifié')
                }

            # Vérifier que la session existe
            session = request.env['edu.attendance.session'].browse(data['session_id'])
            if not session.exists():
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            # Préparation des données
            record_data = self._prepare_record_data(data)
            record = request.env['edu.attendance.record'].create(record_data)

            return {
                'status': 'success',
                'data': self._format_record(record, detailed=True),
                'message': _('Enregistrement créé avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la création de l'enregistrement: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/<int:record_id>', type='json', auth='user', methods=['PUT'])
    def update_record(self, record_id, **kwargs):
        """Met à jour un enregistrement de présence"""
        try:
            record = request.env['edu.attendance.record'].browse(record_id)
            if not record.exists():
                return {
                    'status': 'error',
                    'message': _('Enregistrement non trouvé')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Préparation des données
            record_data = self._prepare_record_data(data)
            record.write(record_data)

            return {
                'status': 'success',
                'data': self._format_record(record, detailed=True),
                'message': _('Enregistrement mis à jour avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour de l'enregistrement {record_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/<int:record_id>', type='json', auth='user', methods=['DELETE'])
    def delete_record(self, record_id, **kwargs):
        """Supprime un enregistrement de présence"""
        try:
            record = request.env['edu.attendance.record'].browse(record_id)
            if not record.exists():
                return {
                    'status': 'error',
                    'message': _('Enregistrement non trouvé')
                }

            record.unlink()

            return {
                'status': 'success',
                'message': _('Enregistrement supprimé avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la suppression de l'enregistrement {record_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/<int:record_id>/check-in', type='json', auth='user', methods=['POST'])
    def check_in(self, record_id, **kwargs):
        """Effectue un pointage d'entrée"""
        try:
            record = request.env['edu.attendance.record'].browse(record_id)
            if not record.exists():
                return {
                    'status': 'error',
                    'message': _('Enregistrement non trouvé')
                }

            data = request.get_json_data() or {}
            
            # Paramètres du pointage
            method = data.get('method', 'manual')
            device_id = data.get('device_id')
            
            # Données supplémentaires
            extra_data = {}
            if data.get('latitude') and data.get('longitude'):
                extra_data.update({
                    'latitude': data['latitude'],
                    'longitude': data['longitude']
                })
            
            if data.get('photo'):
                extra_data['photo'] = data['photo']
                
            if data.get('user_agent'):
                extra_data['user_agent'] = data['user_agent']
                
            if data.get('ip_address'):
                extra_data['ip_address'] = data['ip_address']
                
            if data.get('source'):
                extra_data['source'] = data['source']

            # Effectuer le pointage
            record.action_check_in(method=method, device_id=device_id, **extra_data)

            return {
                'status': 'success',
                'data': self._format_record(record),
                'message': _('Pointage d\'entrée effectué avec succès')
            }

        except UserError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors du pointage d'entrée {record_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/<int:record_id>/check-out', type='json', auth='user', methods=['POST'])
    def check_out(self, record_id, **kwargs):
        """Effectue un pointage de sortie"""
        try:
            record = request.env['edu.attendance.record'].browse(record_id)
            if not record.exists():
                return {
                    'status': 'error',
                    'message': _('Enregistrement non trouvé')
                }

            data = request.get_json_data() or {}
            
            # Paramètres du pointage
            method = data.get('method', 'manual')
            device_id = data.get('device_id')
            
            # Données supplémentaires
            extra_data = {}
            if data.get('latitude') and data.get('longitude'):
                extra_data.update({
                    'latitude': data['latitude'],
                    'longitude': data['longitude']
                })
            
            if data.get('photo'):
                extra_data['photo'] = data['photo']
                
            if data.get('source'):
                extra_data['source'] = data['source']

            # Effectuer le pointage
            record.action_check_out(method=method, device_id=device_id, **extra_data)

            return {
                'status': 'success',
                'data': self._format_record(record),
                'message': _('Pointage de sortie effectué avec succès')
            }

        except UserError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors du pointage de sortie {record_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/<int:record_id>/mark-present', type='json', auth='user', methods=['POST'])
    def mark_present(self, record_id, **kwargs):
        """Marque comme présent manuellement"""
        try:
            record = request.env['edu.attendance.record'].browse(record_id)
            if not record.exists():
                return {
                    'status': 'error',
                    'message': _('Enregistrement non trouvé')
                }

            record.action_mark_present()

            return {
                'status': 'success',
                'data': self._format_record(record),
                'message': _('Marqué comme présent')
            }

        except Exception as e:
            _logger.error(f"Erreur lors du marquage présent {record_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/<int:record_id>/mark-absent', type='json', auth='user', methods=['POST'])
    def mark_absent(self, record_id, **kwargs):
        """Marque comme absent"""
        try:
            record = request.env['edu.attendance.record'].browse(record_id)
            if not record.exists():
                return {
                    'status': 'error',
                    'message': _('Enregistrement non trouvé')
                }

            record.action_mark_absent()

            return {
                'status': 'success',
                'data': self._format_record(record),
                'message': _('Marqué comme absent')
            }

        except Exception as e:
            _logger.error(f"Erreur lors du marquage absent {record_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/<int:record_id>/validate', type='json', auth='user', methods=['POST'])
    def validate_record(self, record_id, **kwargs):
        """Valide l'enregistrement"""
        try:
            record = request.env['edu.attendance.record'].browse(record_id)
            if not record.exists():
                return {
                    'status': 'error',
                    'message': _('Enregistrement non trouvé')
                }

            record.action_validate()

            return {
                'status': 'success',
                'data': self._format_record(record),
                'message': _('Enregistrement validé')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la validation {record_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/<int:record_id>/send-notification', type='json', auth='user', methods=['POST'])
    def send_notification(self, record_id, **kwargs):
        """Envoie une notification aux parents"""
        try:
            record = request.env['edu.attendance.record'].browse(record_id)
            if not record.exists():
                return {
                    'status': 'error',
                    'message': _('Enregistrement non trouvé')
                }

            success = record.send_notification_to_parents()

            return {
                'status': 'success' if success else 'warning',
                'data': self._format_record(record),
                'message': _('Notification envoyée') if success else _('Notification non applicable')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de l'envoi de notification {record_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/session/<int:session_id>', type='json', auth='user', methods=['GET'])
    def get_session_records(self, session_id, **kwargs):
        """Récupère les enregistrements d'une session"""
        try:
            domain = [('session_id', '=', session_id)]
            
            # Filtres additionnels
            if kwargs.get('attendance_status'):
                domain.append(('attendance_status', '=', kwargs['attendance_status']))
                
            if kwargs.get('validated') is not None:
                domain.append(('validated', '=', kwargs['validated']))

            records = request.env['edu.attendance.record'].search(domain)
            
            return {
                'status': 'success',
                'data': [self._format_record(record) for record in records],
                'count': len(records)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des enregistrements de session {session_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/student/<int:student_id>', type='json', auth='user', methods=['GET'])
    def get_student_records(self, student_id, **kwargs):
        """Récupère les enregistrements d'un étudiant"""
        try:
            domain = [('student_id', '=', student_id)]
            
            # Filtres optionnels
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
                'data': [self._format_record(record) for record in records],
                'count': len(records),
                'total_count': total_count
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des enregistrements de l'étudiant {student_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/summary', type='json', auth='user', methods=['GET'])
    def get_attendance_summary(self, **kwargs):
        """Récupère un résumé des présences"""
        try:
            domain = []
            
            # Filtres
            if kwargs.get('date_from'):
                domain.append(('check_in_time', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('check_in_time', '<=', kwargs['date_to']))
            if kwargs.get('session_id'):
                domain.append(('session_id', '=', kwargs['session_id']))

            groupby = kwargs.get('groupby', 'session_id')
            
            summary = request.env['edu.attendance.record'].get_attendance_summary(
                domain=domain,
                groupby=groupby
            )

            return {
                'status': 'success',
                'data': summary,
                'groupby': groupby
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la génération du résumé: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/student/<int:student_id>/rate', type='json', auth='user', methods=['GET'])
    def get_student_attendance_rate(self, student_id, **kwargs):
        """Calcule le taux de présence d'un étudiant"""
        try:
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            
            rate = request.env['edu.attendance.record'].get_student_attendance_rate(
                student_id=student_id,
                date_from=date_from,
                date_to=date_to
            )

            return {
                'status': 'success',
                'data': {
                    'student_id': student_id,
                    'attendance_rate': rate,
                    'period': {
                        'date_from': date_from,
                        'date_to': date_to
                    }
                }
            }
        except Exception as e:
            _logger.error(f"Erreur lors du calcul du taux de présence de l'étudiant {student_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/statistics', type='json', auth='user', methods=['GET'])
    def get_attendance_statistics(self, **kwargs):
        """Récupère les statistiques détaillées des présences"""
        try:
            domain = []
            
            # Filtres
            if kwargs.get('date_from'):
                domain.append(('check_in_time', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('check_in_time', '<=', kwargs['date_to']))
            if kwargs.get('session_id'):
                domain.append(('session_id', '=', kwargs['session_id']))

            records = request.env['edu.attendance.record'].search(domain)

            # Calculs des statistiques
            total_records = len(records)
            present_count = len(records.filtered(lambda r: r.attendance_status == 'present'))
            absent_count = len(records.filtered(lambda r: r.attendance_status == 'absent'))
            late_count = len(records.filtered(lambda r: r.attendance_status == 'late'))
            excused_count = len(records.filtered(lambda r: r.attendance_status == 'excused'))
            partial_count = len(records.filtered(lambda r: r.attendance_status == 'partial'))
            
            validated_count = len(records.filtered('validated'))
            
            avg_late_minutes = sum(records.mapped('late_minutes')) / len(records) if records else 0
            avg_presence_rate = sum(records.mapped('presence_rate')) / len(records) if records else 0

            return {
                'status': 'success',
                'data': {
                    'total_records': total_records,
                    'by_status': {
                        'present': present_count,
                        'absent': absent_count,
                        'late': late_count,
                        'excused': excused_count,
                        'partial': partial_count
                    },
                    'percentages': {
                        'present': (present_count / total_records * 100) if total_records else 0,
                        'absent': (absent_count / total_records * 100) if total_records else 0,
                        'late': (late_count / total_records * 100) if total_records else 0,
                        'excused': (excused_count / total_records * 100) if total_records else 0,
                        'partial': (partial_count / total_records * 100) if total_records else 0
                    },
                    'validated_count': validated_count,
                    'validation_rate': (validated_count / total_records * 100) if total_records else 0,
                    'average_late_minutes': round(avg_late_minutes, 2),
                    'average_presence_rate': round(avg_presence_rate, 2)
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la génération des statistiques: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/records/bulk-actions', type='json', auth='user', methods=['POST'])
    def bulk_actions(self, **kwargs):
        """Effectue des actions en lot sur plusieurs enregistrements"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            record_ids = data.get('record_ids', [])
            action = data.get('action')

            if not record_ids or not action:
                return {
                    'status': 'error',
                    'message': _('IDs des enregistrements et action requis')
                }

            records = request.env['edu.attendance.record'].browse(record_ids)
            
            success_count = 0
            error_count = 0
            errors = []

            for record in records:
                try:
                    if action == 'mark_present':
                        record.action_mark_present()
                    elif action == 'mark_absent':
                        record.action_mark_absent()
                    elif action == 'validate':
                        record.action_validate()
                    elif action == 'send_notification':
                        record.send_notification_to_parents()
                    else:
                        errors.append(f"Action inconnue: {action}")
                        error_count += 1
                        continue
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Erreur pour l'enregistrement {record.id}: {str(e)}")

            return {
                'status': 'success' if error_count == 0 else 'partial',
                'data': {
                    'success_count': success_count,
                    'error_count': error_count,
                    'total_count': len(record_ids),
                    'errors': errors
                },
                'message': f'{success_count} enregistrements traités avec succès'
            }

        except Exception as e:
            _logger.error(f"Erreur lors des actions en lot: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _format_record(self, record, detailed=False):
        """Formate les données de l'enregistrement pour l'API"""
        data = {
            'id': record.id,
            'display_name': record.display_name,
            'session': {
                'id': record.session_id.id,
                'name': record.session_id.name
            } if record.session_id else None,
            'student': {
                'id': record.student_id.id if record.student_id else None,
                'name': record.student_id.name if record.student_id else None
            },
            'faculty': {
                'id': record.faculty_id.id if record.faculty_id else None,
                'name': record.faculty_id.name if record.faculty_id else None
            },
            'device': {
                'id': record.device_id.id if record.device_id else None,
                'name': record.device_id.name if record.device_id else None
            },
            'check_in_time': record.check_in_time.isoformat() if record.check_in_time else None,
            'check_out_time': record.check_out_time.isoformat() if record.check_out_time else None,
            'attendance_status': record.attendance_status,
            'is_absent': record.is_absent,
            'is_late': record.is_late,
            'is_excused': record.is_excused,
            'late_minutes': record.late_minutes,
            'hours_present': record.hours_present,
            'hours_expected': record.hours_expected,
            'presence_rate': record.presence_rate,
            'validated': record.validated,
            'status_color': record.get_status_color(),
            'status_icon': record.get_status_icon(),
            'create_date': record.create_date.isoformat() if record.create_date else None
        }

        if detailed:
            data.update({
                'expected_check_in': record.expected_check_in.isoformat() if record.expected_check_in else None,
                'expected_check_out': record.expected_check_out.isoformat() if record.expected_check_out else None,
                'check_in_method': record.check_in_method,
                'check_out_method': record.check_out_method,
                'location': {
                    'check_in': {
                        'latitude': record.check_in_latitude,
                        'longitude': record.check_in_longitude
                    } if record.check_in_latitude and record.check_in_longitude else None,
                    'check_out': {
                        'latitude': record.check_out_latitude,
                        'longitude': record.check_out_longitude
                    } if record.check_out_latitude and record.check_out_longitude else None,
                    'verified': record.location_verified
                },
                'photos': {
                    'check_in': bool(record.check_in_photo),
                    'check_out': bool(record.check_out_photo),
                    'verified': record.photo_verified
                },
                'excuse': {
                    'id': record.excuse_id.id if record.excuse_id else None,
                    'name': record.excuse_id.name if record.excuse_id else None,
                    'reason': record.excuse_reason
                },
                'validation': {
                    'validated_by': {
                        'id': record.validated_by.id if record.validated_by else None,
                        'name': record.validated_by.name if record.validated_by else None
                    },
                    'validated_date': record.validated_date.isoformat() if record.validated_date else None
                },
                'notification': {
                    'sent': record.notification_sent,
                    'date': record.notification_date.isoformat() if record.notification_date else None
                },
                'technical': {
                    'user_agent': record.user_agent,
                    'ip_address': record.ip_address,
                    'check_in_source': record.check_in_source,
                    'check_out_source': record.check_out_source
                },
                'comment': record.comment,
                'write_date': record.write_date.isoformat() if record.write_date else None
            })

        return data

    def _prepare_record_data(self, data):
        """Prépare les données pour la création/mise à jour"""
        allowed_fields = [
            'session_id', 'student_id', 'faculty_id', 'device_id', 'excuse_id',
            'check_in_time', 'check_out_time', 'expected_check_in', 'expected_check_out',
            'check_in_method', 'check_out_method', 'is_absent', 'is_excused',
            'check_in_latitude', 'check_in_longitude', 'check_out_latitude', 'check_out_longitude',
            'location_verified', 'photo_verified', 'comment', 'excuse_reason',
            'validated', 'user_agent', 'ip_address', 'check_in_source', 'check_out_source'
        ]
        
        record_data = {}
        for field in allowed_fields:
            if field in data:
                record_data[field] = data[field]
        
        # Gestion des photos en base64
        if 'check_in_photo' in data and data['check_in_photo']:
            try:
                record_data['check_in_photo'] = base64.b64decode(data['check_in_photo'])
            except Exception as e:
                _logger.error(f"Erreur lors du décodage de la photo d'entrée: {e}")
        
        if 'check_out_photo' in data and data['check_out_photo']:
            try:
                record_data['check_out_photo'] = base64.b64decode(data['check_out_photo'])
            except Exception as e:
                _logger.error(f"Erreur lors du décodage de la photo de sortie: {e}")
        
        # Gestion du document justificatif
        if 'excuse_document' in data and data['excuse_document']:
            try:
                record_data['excuse_document'] = base64.b64decode(data['excuse_document'])
                if 'excuse_document_name' in data:
                    record_data['excuse_document_name'] = data['excuse_document_name']
            except Exception as e:
                _logger.error(f"Erreur lors du décodage du document justificatif: {e}")
        
        return record_data


class EduAttendanceRecordPublicController(http.Controller):
    """Contrôleur API public pour les enregistrements de présence"""

    @http.route('/api/public/attendance/check-in', type='json', auth='public', methods=['POST'])
    def public_check_in(self, **kwargs):
        """Endpoint public pour le pointage d'entrée"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des données requises
            required_fields = ['session_code', 'participant_code', 'device_code']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'status': 'error',
                        'message': _('Le champ %s est obligatoire') % field
                    }

            # Recherche de la session
            session = request.env['edu.attendance.session'].sudo().search([
                ('code', '=', data['session_code']),
                ('state', 'in', ['open', 'in_progress'])
            ], limit=1)
            
            if not session:
                return {
                    'status': 'error',
                    'message': _('Session non trouvée ou fermée')
                }

            # Recherche du dispositif
            device = request.env['edu.attendance.device'].sudo().search([
                ('code', '=', data['device_code']),
                ('active', '=', True)
            ], limit=1)
            
            if not device:
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé ou inactif')
                }

            # Recherche du participant (étudiant ou enseignant)
            participant = None
            student = request.env['op.student'].sudo().search([
                ('code', '=', data['participant_code'])
            ], limit=1)
            
            if student:
                participant = {'student_id': student.id}
            else:
                faculty = request.env['op.faculty'].sudo().search([
                    ('code', '=', data['participant_code'])
                ], limit=1)
                if faculty:
                    participant = {'faculty_id': faculty.id}
            
            if not participant:
                return {
                    'status': 'error',
                    'message': _('Participant non trouvé')
                }

            # Recherche de l'enregistrement existant
            domain = [('session_id', '=', session.id)]
            domain.extend([(k, '=', v) for k, v in participant.items()])
            
            record = request.env['edu.attendance.record'].sudo().search(domain, limit=1)
            
            if not record:
                # Créer un nouvel enregistrement
                record_data = {
                    'session_id': session.id,
                    'device_id': device.id,
                    **participant
                }
                record = request.env['edu.attendance.record'].sudo().create(record_data)

            # Vérifier si déjà pointé
            if record.check_in_time:
                return {
                    'status': 'warning',
                    'message': _('Entrée déjà enregistrée'),
                    'data': {
                        'record_id': record.id,
                        'check_in_time': record.check_in_time.isoformat()
                    }
                }

            # Vérifications de géolocalisation si requises
            if device.require_geolocation:
                if not data.get('latitude') or not data.get('longitude'):
                    return {
                        'status': 'error',
                        'message': _('Géolocalisation requise')
                    }
                
                if not device.is_in_range(data['latitude'], data['longitude']):
                    return {
                        'status': 'error',
                        'message': _('Vous êtes trop éloigné du dispositif')
                    }

            # Effectuer le pointage
            extra_data = {}
            if data.get('latitude') and data.get('longitude'):
                extra_data.update({
                    'latitude': data['latitude'],
                    'longitude': data['longitude']
                })
            
            if data.get('photo'):
                extra_data['photo'] = data['photo']
                
            if data.get('user_agent'):
                extra_data['user_agent'] = data['user_agent']
                
            # Récupération de l'IP depuis la requête
            extra_data['ip_address'] = request.httprequest.environ.get('REMOTE_ADDR')
            extra_data['source'] = 'public_api'

            record.action_check_in(
                method=device.device_type,
                device_id=device.id,
                **extra_data
            )

            return {
                'status': 'success',
                'data': {
                    'record_id': record.id,
                    'check_in_time': record.check_in_time.isoformat(),
                    'participant_name': student.name if student else faculty.name,
                    'session_name': session.name,
                    'device_name': device.name,
                    'is_late': record.is_late,
                    'late_minutes': record.late_minutes
                },
                'message': _('Pointage d\'entrée effectué avec succès')
            }

        except UserError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors du pointage public d'entrée: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors du pointage')
            }

    @http.route('/api/public/attendance/check-out', type='json', auth='public', methods=['POST'])
    def public_check_out(self, **kwargs):
        """Endpoint public pour le pointage de sortie"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des données requises
            required_fields = ['session_code', 'participant_code', 'device_code']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'status': 'error',
                        'message': _('Le champ %s est obligatoire') % field
                    }

            # Recherche de l'enregistrement
            session = request.env['edu.attendance.session'].sudo().search([
                ('code', '=', data['session_code'])
            ], limit=1)
            
            if not session:
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            device = request.env['edu.attendance.device'].sudo().search([
                ('code', '=', data['device_code']),
                ('active', '=', True)
            ], limit=1)
            
            if not device:
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé ou inactif')
                }

            # Recherche du participant
            participant_domain = [('session_id', '=', session.id)]
            
            student = request.env['op.student'].sudo().search([
                ('code', '=', data['participant_code'])
            ], limit=1)
            
            if student:
                participant_domain.append(('student_id', '=', student.id))
            else:
                faculty = request.env['op.faculty'].sudo().search([
                    ('code', '=', data['participant_code'])
                ], limit=1)
                if faculty:
                    participant_domain.append(('faculty_id', '=', faculty.id))
                else:
                    return {
                        'status': 'error',
                        'message': _('Participant non trouvé')
                    }

            record = request.env['edu.attendance.record'].sudo().search(participant_domain, limit=1)
            
            if not record:
                return {
                    'status': 'error',
                    'message': _('Aucun enregistrement d\'entrée trouvé')
                }

            # Vérifier si déjà pointé en sortie
            if record.check_out_time:
                return {
                    'status': 'warning',
                    'message': _('Sortie déjà enregistrée'),
                    'data': {
                        'record_id': record.id,
                        'check_out_time': record.check_out_time.isoformat()
                    }
                }

            # Effectuer le pointage de sortie
            extra_data = {}
            if data.get('latitude') and data.get('longitude'):
                extra_data.update({
                    'latitude': data['latitude'],
                    'longitude': data['longitude']
                })
            
            if data.get('photo'):
                extra_data['photo'] = data['photo']
                
            extra_data['source'] = 'public_api'

            record.action_check_out(
                method=device.device_type,
                device_id=device.id,
                **extra_data
            )

            return {
                'status': 'success',
                'data': {
                    'record_id': record.id,
                    'check_in_time': record.check_in_time.isoformat(),
                    'check_out_time': record.check_out_time.isoformat(),
                    'participant_name': student.name if student else faculty.name,
                    'session_name': session.name,
                    'device_name': device.name,
                    'hours_present': record.hours_present,
                    'presence_rate': record.presence_rate
                },
                'message': _('Pointage de sortie effectué avec succès')
            }

        except UserError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors du pointage public de sortie: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors du pointage')
            }

    @http.route('/api/public/attendance/status', type='json', auth='public', methods=['GET'])
    def get_public_attendance_status(self, **kwargs):
        """Récupère le statut de présence public"""
        try:
            session_code = kwargs.get('session_code')
            participant_code = kwargs.get('participant_code')
            
            if not session_code or not participant_code:
                return {
                    'status': 'error',
                    'message': _('Code de session et code participant requis')
                }

            # Recherche de la session
            session = request.env['edu.attendance.session'].sudo().search([
                ('code', '=', session_code)
            ], limit=1)
            
            if not session:
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            # Recherche du participant
            participant_domain = [('session_id', '=', session.id)]
            
            student = request.env['op.student'].sudo().search([
                ('code', '=', participant_code)
            ], limit=1)
            
            if student:
                participant_domain.append(('student_id', '=', student.id))
                participant_name = student.name
            else:
                faculty = request.env['op.faculty'].sudo().search([
                    ('code', '=', participant_code)
                ], limit=1)
                if faculty:
                    participant_domain.append(('faculty_id', '=', faculty.id))
                    participant_name = faculty.name
                else:
                    return {
                        'status': 'error',
                        'message': _('Participant non trouvé')
                    }

            record = request.env['edu.attendance.record'].sudo().search(participant_domain, limit=1)
            
            if not record:
                return {
                    'status': 'success',
                    'data': {
                        'participant_name': participant_name,
                        'session_name': session.name,
                        'attendance_status': 'not_registered',
                        'check_in_time': None,
                        'check_out_time': None
                    }
                }

            return {
                'status': 'success',
                'data': {
                    'record_id': record.id,
                    'participant_name': participant_name,
                    'session_name': session.name,
                    'attendance_status': record.attendance_status,
                    'check_in_time': record.check_in_time.isoformat() if record.check_in_time else None,
                    'check_out_time': record.check_out_time.isoformat() if record.check_out_time else None,
                    'is_late': record.is_late,
                    'late_minutes': record.late_minutes,
                    'hours_present': record.hours_present,
                    'presence_rate': record.presence_rate
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du statut public: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la récupération du statut')
            }

    @http.route('/api/public/attendance/session/<string:session_code>/info', type='json', auth='public', methods=['GET'])
    def get_public_session_info(self, session_code, **kwargs):
        """Récupère les informations publiques d'une session"""
        try:
            session = request.env['edu.attendance.session'].sudo().search([
                ('code', '=', session_code)
            ], limit=1)
            
            if not session:
                return {
                    'status': 'error',
                    'message': _('Session non trouvée')
                }

            return {
                'status': 'success',
                'data': {
                    'name': session.name,
                    'code': session.code,
                    'state': session.state,
                    'start_datetime': session.start_datetime.isoformat() if session.start_datetime else None,
                    'end_datetime': session.end_datetime.isoformat() if session.end_datetime else None,
                    'location': session.location if hasattr(session, 'location') else None,
                    'check_in_window': {
                        'open': session.is_check_in_open() if hasattr(session, 'is_check_in_open') else True,
                        'closes_at': session.check_in_deadline.isoformat() if hasattr(session, 'check_in_deadline') and session.check_in_deadline else None
                    },
                    'check_out_window': {
                        'open': session.is_check_out_open() if hasattr(session, 'is_check_out_open') else True,
                        'closes_at': session.check_out_deadline.isoformat() if hasattr(session, 'check_out_deadline') and session.check_out_deadline else None
                    },
                    'require_geolocation': session.require_gps_verification if hasattr(session, 'require_gps_verification') else False,
                    'require_photo': session.require_photo_verification if hasattr(session, 'require_photo_verification') else False
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des infos de session {session_code}: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la récupération des informations')
            }