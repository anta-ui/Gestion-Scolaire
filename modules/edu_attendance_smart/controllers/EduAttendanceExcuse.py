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


class EduAttendanceExcuseController(http.Controller):
    """Contrôleur API pour la gestion des justificatifs d'absence et de retard"""

    @http.route('/api/attendance/excuses', type='json', auth='user', methods=['GET'])
    def get_excuses(self, **kwargs):
        """Récupère tous les justificatifs"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', kwargs['student_id']))
            
            if kwargs.get('excuse_type'):
                domain.append(('excuse_type', '=', kwargs['excuse_type']))
                
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
                
            if kwargs.get('reason'):
                domain.append(('reason', '=', kwargs['reason']))
                
            if kwargs.get('date_from'):
                domain.append(('date', '>=', kwargs['date_from']))
                
            if kwargs.get('date_to'):
                domain.append(('date', '<=', kwargs['date_to']))

            # Pagination
            limit = kwargs.get('limit', 100)
            offset = kwargs.get('offset', 0)
            
            excuses = request.env['edu.attendance.excuse'].search(
                domain, 
                limit=limit, 
                offset=offset,
                order='date desc, id desc'
            )
            
            total_count = request.env['edu.attendance.excuse'].search_count(domain)
            
            return {
                'status': 'success',
                'data': [self._format_excuse(excuse) for excuse in excuses],
                'count': len(excuses),
                'total_count': total_count
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des justificatifs: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses/<int:excuse_id>', type='json', auth='user', methods=['GET'])
    def get_excuse(self, excuse_id, **kwargs):
        """Récupère un justificatif spécifique"""
        try:
            excuse = request.env['edu.attendance.excuse'].browse(excuse_id)
            if not excuse.exists():
                return {
                    'status': 'error',
                    'message': _('Justificatif non trouvé')
                }
            
            return {
                'status': 'success',
                'data': self._format_excuse(excuse, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du justificatif {excuse_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses/student/<int:student_id>', type='json', auth='user', methods=['GET'])
    def get_student_excuses(self, student_id, **kwargs):
        """Récupère les justificatifs d'un étudiant spécifique"""
        try:
            domain = [('student_id', '=', student_id)]
            
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
                'data': [self._format_excuse(excuse) for excuse in excuses],
                'count': len(excuses),
                'total_count': total_count
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des justificatifs de l'étudiant {student_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses', type='json', auth='user', methods=['POST'])
    def create_excuse(self, **kwargs):
        """Crée un nouveau justificatif"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des données obligatoires
            required_fields = ['student_id', 'excuse_type', 'date', 'reason']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'status': 'error',
                        'message': _('Le champ %s est obligatoire') % field
                    }

            # Validation du format de date
            try:
                date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
                if date_obj > fields.Date.today():
                    return {
                        'status': 'error',
                        'message': _('La date ne peut pas être dans le futur')
                    }
            except ValueError:
                return {
                    'status': 'error',
                    'message': _('Format de date invalide. Utilisez YYYY-MM-DD')
                }

            # Vérifier que l'étudiant existe
            student = request.env['res.partner'].browse(data['student_id'])
            if not student.exists():
                return {
                    'status': 'error',
                    'message': _('Étudiant non trouvé')
                }

            # Préparation des données
            excuse_data = self._prepare_excuse_data(data)
            excuse = request.env['edu.attendance.excuse'].create(excuse_data)

            # Gestion des pièces jointes
            if data.get('attachments'):
                self._handle_attachments(excuse, data['attachments'])

            return {
                'status': 'success',
                'data': self._format_excuse(excuse, detailed=True),
                'message': _('Justificatif créé avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la création du justificatif: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses/<int:excuse_id>', type='json', auth='user', methods=['PUT'])
    def update_excuse(self, excuse_id, **kwargs):
        """Met à jour un justificatif existant"""
        try:
            excuse = request.env['edu.attendance.excuse'].browse(excuse_id)
            if not excuse.exists():
                return {
                    'status': 'error',
                    'message': _('Justificatif non trouvé')
                }

            # Vérifier si le justificatif peut être modifié
            if excuse.state not in ['draft', 'rejected']:
                return {
                    'status': 'error',
                    'message': _('Seuls les justificatifs en brouillon ou rejetés peuvent être modifiés')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Préparation des données
            excuse_data = self._prepare_excuse_data(data)
            excuse.write(excuse_data)

            # Gestion des pièces jointes
            if 'attachments' in data:
                self._handle_attachments(excuse, data['attachments'])

            return {
                'status': 'success',
                'data': self._format_excuse(excuse, detailed=True),
                'message': _('Justificatif mis à jour avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour du justificatif {excuse_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses/<int:excuse_id>', type='json', auth='user', methods=['DELETE'])
    def delete_excuse(self, excuse_id, **kwargs):
        """Supprime un justificatif"""
        try:
            excuse = request.env['edu.attendance.excuse'].browse(excuse_id)
            if not excuse.exists():
                return {
                    'status': 'error',
                    'message': _('Justificatif non trouvé')
                }

            # Vérifier si le justificatif peut être supprimé
            if excuse.state == 'approved':
                return {
                    'status': 'error',
                    'message': _('Impossible de supprimer un justificatif approuvé')
                }

            excuse.unlink()

            return {
                'status': 'success',
                'message': _('Justificatif supprimé avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la suppression du justificatif {excuse_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses/<int:excuse_id>/submit', type='json', auth='user', methods=['POST'])
    def submit_excuse(self, excuse_id, **kwargs):
        """Soumet un justificatif pour approbation"""
        try:
            excuse = request.env['edu.attendance.excuse'].browse(excuse_id)
            if not excuse.exists():
                return {
                    'status': 'error',
                    'message': _('Justificatif non trouvé')
                }

            if excuse.state != 'draft':
                return {
                    'status': 'error',
                    'message': _('Seuls les justificatifs en brouillon peuvent être soumis')
                }

            excuse.action_submit()

            return {
                'status': 'success',
                'data': self._format_excuse(excuse),
                'message': _('Justificatif soumis pour approbation')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la soumission du justificatif {excuse_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses/<int:excuse_id>/approve', type='json', auth='user', methods=['POST'])
    def approve_excuse(self, excuse_id, **kwargs):
        """Approuve un justificatif"""
        try:
            excuse = request.env['edu.attendance.excuse'].browse(excuse_id)
            if not excuse.exists():
                return {
                    'status': 'error',
                    'message': _('Justificatif non trouvé')
                }

            if excuse.state != 'submitted':
                return {
                    'status': 'error',
                    'message': _('Seuls les justificatifs soumis peuvent être approuvés')
                }

            excuse.action_approve()

            return {
                'status': 'success',
                'data': self._format_excuse(excuse),
                'message': _('Justificatif approuvé avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de l'approbation du justificatif {excuse_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses/<int:excuse_id>/reject', type='json', auth='user', methods=['POST'])
    def reject_excuse(self, excuse_id, **kwargs):
        """Rejette un justificatif"""
        try:
            excuse = request.env['edu.attendance.excuse'].browse(excuse_id)
            if not excuse.exists():
                return {
                    'status': 'error',
                    'message': _('Justificatif non trouvé')
                }

            if excuse.state != 'submitted':
                return {
                    'status': 'error',
                    'message': _('Seuls les justificatifs soumis peuvent être rejetés')
                }

            data = request.get_json_data()
            rejection_reason = data.get('rejection_reason', '') if data else ''

            excuse.write({
                'state': 'rejected',
                'rejection_reason': rejection_reason
            })

            return {
                'status': 'success',
                'data': self._format_excuse(excuse),
                'message': _('Justificatif rejeté')
            }

        except Exception as e:
            _logger.error(f"Erreur lors du rejet du justificatif {excuse_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses/<int:excuse_id>/reset', type='json', auth='user', methods=['POST'])
    def reset_excuse(self, excuse_id, **kwargs):
        """Remet un justificatif en brouillon"""
        try:
            excuse = request.env['edu.attendance.excuse'].browse(excuse_id)
            if not excuse.exists():
                return {
                    'status': 'error',
                    'message': _('Justificatif non trouvé')
                }

            excuse.action_reset_to_draft()

            return {
                'status': 'success',
                'data': self._format_excuse(excuse),
                'message': _('Justificatif remis en brouillon')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la remise en brouillon du justificatif {excuse_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses/pending', type='json', auth='user', methods=['GET'])
    def get_pending_excuses(self, **kwargs):
        """Récupère les justificatifs en attente d'approbation"""
        try:
            domain = [('state', '=', 'submitted')]
            
            # Filtres optionnels
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
                'data': [self._format_excuse(excuse) for excuse in excuses],
                'count': len(excuses),
                'total_count': total_count
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des justificatifs en attente: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses/statistics', type='json', auth='user', methods=['GET'])
    def get_excuse_statistics(self, **kwargs):
        """Récupère les statistiques des justificatifs"""
        try:
            # Paramètres de période
            date_from = kwargs.get('date_from')
            date_to = kwargs.get('date_to')
            
            domain = []
            if date_from:
                domain.append(('date', '>=', date_from))
            if date_to:
                domain.append(('date', '<=', date_to))

            # Statistiques par état
            stats_by_state = {}
            for state, label in request.env['edu.attendance.excuse']._fields['state'].selection:
                count = request.env['edu.attendance.excuse'].search_count(domain + [('state', '=', state)])
                stats_by_state[state] = {'label': label, 'count': count}

            # Statistiques par type
            stats_by_type = {}
            for excuse_type, label in request.env['edu.attendance.excuse']._fields['excuse_type'].selection:
                count = request.env['edu.attendance.excuse'].search_count(domain + [('excuse_type', '=', excuse_type)])
                stats_by_type[excuse_type] = {'label': label, 'count': count}

            # Statistiques par raison
            stats_by_reason = {}
            for reason, label in request.env['edu.attendance.excuse']._fields['reason'].selection:
                count = request.env['edu.attendance.excuse'].search_count(domain + [('reason', '=', reason)])
                stats_by_reason[reason] = {'label': label, 'count': count}

            # Total
            total_excuses = request.env['edu.attendance.excuse'].search_count(domain)

            return {
                'status': 'success',
                'data': {
                    'total_excuses': total_excuses,
                    'by_state': stats_by_state,
                    'by_type': stats_by_type,
                    'by_reason': stats_by_reason,
                    'period': {
                        'date_from': date_from,
                        'date_to': date_to
                    }
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/excuses/options', type='json', auth='user', methods=['GET'])
    def get_excuse_options(self, **kwargs):
        """Récupère les options disponibles pour les justificatifs"""
        try:
            excuse_types = request.env['edu.attendance.excuse']._fields['excuse_type'].selection
            reasons = request.env['edu.attendance.excuse']._fields['reason'].selection
            states = request.env['edu.attendance.excuse']._fields['state'].selection
            
            return {
                'status': 'success',
                'data': {
                    'excuse_types': [{'value': value, 'label': label} for value, label in excuse_types],
                    'reasons': [{'value': value, 'label': label} for value, label in reasons],
                    'states': [{'value': value, 'label': label} for value, label in states]
                }
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des options: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _format_excuse(self, excuse, detailed=False):
        """Formate les données du justificatif pour l'API"""
        data = {
            'id': excuse.id,
            'name': excuse.name,
            'student': {
                'id': excuse.student_id.id,
                'name': excuse.student_id.name,
                'email': excuse.student_id.email
            },
            'excuse_type': excuse.excuse_type,
            'date': excuse.date.isoformat() if excuse.date else None,
            'reason': excuse.reason,
            'state': excuse.state,
            'time_from': excuse.time_from,
            'time_to': excuse.time_to,
            'create_date': excuse.create_date.isoformat() if excuse.create_date else None
        }

        if detailed:
            data.update({
                'description': excuse.description,
                'approved_by': {
                    'id': excuse.approved_by.id if excuse.approved_by else None,
                    'name': excuse.approved_by.name if excuse.approved_by else None
                },
                'approval_date': excuse.approval_date.isoformat() if excuse.approval_date else None,
                'rejection_reason': excuse.rejection_reason,
                'attachments': [self._format_attachment(att) for att in excuse.attachment_ids],
                'attendance_records': [
                    {
                        'id': rec.id,
                        'check_in_time': rec.check_in_time.isoformat() if rec.check_in_time else None,
                        'check_out_time': rec.check_out_time.isoformat() if rec.check_out_time else None
                    } for rec in excuse.attendance_record_ids
                ],
                'write_date': excuse.write_date.isoformat() if excuse.write_date else None
            })

        return data

    def _format_attachment(self, attachment):
        """Formate les données d'une pièce jointe"""
        return {
            'id': attachment.id,
            'name': attachment.name,
            'mimetype': attachment.mimetype,
            'file_size': attachment.file_size,
            'create_date': attachment.create_date.isoformat() if attachment.create_date else None
        }

    def _prepare_excuse_data(self, data):
        """Prépare les données pour la création/mise à jour"""
        allowed_fields = [
            'student_id', 'excuse_type', 'date', 'time_from', 'time_to',
            'reason', 'description', 'active'
        ]
        
        excuse_data = {}
        for field in allowed_fields:
            if field in data:
                excuse_data[field] = data[field]
        
        return excuse_data

    def _handle_attachments(self, excuse, attachments_data):
        """Gère les pièces jointes"""
        if not attachments_data:
            return

        for attachment_data in attachments_data:
            if 'content' in attachment_data and 'filename' in attachment_data:
                # Décoder le contenu base64
                try:
                    content = base64.b64decode(attachment_data['content'])
                    
                    attachment = request.env['ir.attachment'].create({
                        'name': attachment_data['filename'],
                        'datas': attachment_data['content'],
                        'res_model': 'edu.attendance.excuse',
                        'res_id': excuse.id,
                        'type': 'binary'
                    })
                    
                except Exception as e:
                    _logger.error(f"Erreur lors de la création de la pièce jointe: {e}")


class EduAttendanceExcusePublicController(http.Controller):
    """Contrôleur API public pour les justificatifs (accès limité)"""

    @http.route('/api/public/attendance/excuses/submit', type='json', auth='public', methods=['POST'])
    def submit_public_excuse(self, **kwargs):
        """Permet la soumission publique de justificatifs (avec token)"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Vérification du token (à implémenter selon vos besoins de sécurité)
            if not data.get('token'):
                return {
                    'status': 'error',
                    'message': _('Token d\'authentification requis')
                }

            # Validation des données obligatoires
            required_fields = ['student_id', 'excuse_type', 'date', 'reason']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'status': 'error',
                        'message': _('Le champ %s est obligatoire') % field
                    }

            # Création du justificatif avec sudo
            excuse_data = {
                'student_id': data['student_id'],
                'excuse_type': data['excuse_type'],
                'date': data['date'],
                'reason': data['reason'],
                'description': data.get('description', ''),
                'time_from': data.get('time_from'),
                'time_to': data.get('time_to'),
                'state': 'submitted'  # Directement soumis
            }

            excuse = request.env['edu.attendance.excuse'].sudo().create(excuse_data)

            return {
                'status': 'success',
                'data': {
                    'id': excuse.id,
                    'name': excuse.name,
                    'state': excuse.state
                },
                'message': _('Justificatif soumis avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la soumission publique: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la soumission du justificatif')
            }