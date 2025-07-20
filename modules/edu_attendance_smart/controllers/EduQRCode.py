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


class EduQRCodeController(http.Controller):
    """Contrôleur API pour la gestion des QR codes"""

    @http.route('/api/qr-codes', type='json', auth='user', methods=['GET'])
    def get_qr_codes(self, **kwargs):
        """Récupère tous les QR codes"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('qr_type'):
                domain.append(('qr_type', '=', kwargs['qr_type']))
            
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
                
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', kwargs['student_id']))
                
            if kwargs.get('teacher_id'):
                domain.append(('teacher_id', '=', kwargs['teacher_id']))
                
            if kwargs.get('session_id'):
                domain.append(('session_id', '=', kwargs['session_id']))
                
            if kwargs.get('device_id'):
                domain.append(('device_id', '=', kwargs['device_id']))
                
            if kwargs.get('expired') is not None:
                if kwargs['expired']:
                    domain.append(('is_expired', '=', True))
                else:
                    domain.append(('is_expired', '=', False))
                    
            if kwargs.get('date_from'):
                domain.append(('create_date', '>=', kwargs['date_from']))
                
            if kwargs.get('date_to'):
                domain.append(('create_date', '<=', kwargs['date_to']))

            # Pagination
            limit = kwargs.get('limit', 100)
            offset = kwargs.get('offset', 0)
            
            qr_codes = request.env['edu.qr.code'].search(
                domain, 
                limit=limit, 
                offset=offset,
                order='create_date desc, id desc'
            )
            
            total_count = request.env['edu.qr.code'].search_count(domain)
            
            return {
                'status': 'success',
                'data': [self._format_qr_code(qr) for qr in qr_codes],
                'count': len(qr_codes),
                'total_count': total_count
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des QR codes: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/<int:qr_id>', type='json', auth='user', methods=['GET'])
    def get_qr_code(self, qr_id, **kwargs):
        """Récupère un QR code spécifique"""
        try:
            qr_code = request.env['edu.qr.code'].browse(qr_id)
            if not qr_code.exists():
                return {
                    'status': 'error',
                    'message': _('QR code non trouvé')
                }
            
            return {
                'status': 'success',
                'data': self._format_qr_code(qr_code, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du QR code {qr_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes', type='json', auth='user', methods=['POST'])
    def create_qr_code(self, **kwargs):
        """Crée un nouveau QR code"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des données obligatoires
            required_fields = ['name', 'qr_type']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'status': 'error',
                        'message': _('Le champ %s est obligatoire') % field
                    }

            # Validation selon le type de QR code
            qr_type = data['qr_type']
            if qr_type == 'student' and not data.get('student_id'):
                return {
                    'status': 'error',
                    'message': _('ID étudiant requis pour un QR code étudiant')
                }
            elif qr_type == 'faculty' and not data.get('teacher_id'):
                return {
                    'status': 'error',
                    'message': _('ID enseignant requis pour un QR code enseignant')
                }
            elif qr_type == 'session' and not data.get('session_id'):
                return {
                    'status': 'error',
                    'message': _('ID session requis pour un QR code session')
                }
            elif qr_type == 'device' and not data.get('device_id'):
                return {
                    'status': 'error',
                    'message': _('ID dispositif requis pour un QR code dispositif')
                }

            # Vérifier les doublons pour les QR codes personnels
            if qr_type in ['student', 'faculty'] and data.get('student_id' if qr_type == 'student' else 'teacher_id'):
                existing = request.env['edu.qr.code'].search([
                    ('qr_type', '=', qr_type),
                    ('student_id' if qr_type == 'student' else 'teacher_id', '=', 
                     data.get('student_id' if qr_type == 'student' else 'teacher_id')),
                    ('active', '=', True)
                ])
                
                if existing:
                    return {
                        'status': 'error',
                        'message': _('Un QR code actif existe déjà pour cette personne')
                    }

            # Préparation des données
            qr_data = self._prepare_qr_data(data)
            qr_code = request.env['edu.qr.code'].create(qr_data)

            return {
                'status': 'success',
                'data': self._format_qr_code(qr_code, detailed=True),
                'message': _('QR code créé avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la création du QR code: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/<int:qr_id>', type='json', auth='user', methods=['PUT'])
    def update_qr_code(self, qr_id, **kwargs):
        """Met à jour un QR code existant"""
        try:
            qr_code = request.env['edu.qr.code'].browse(qr_id)
            if not qr_code.exists():
                return {
                    'status': 'error',
                    'message': _('QR code non trouvé')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Préparation des données (certains champs sensibles sont exclus)
            qr_data = self._prepare_qr_data(data, update=True)
            qr_code.write(qr_data)

            return {
                'status': 'success',
                'data': self._format_qr_code(qr_code, detailed=True),
                'message': _('QR code mis à jour avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour du QR code {qr_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/<int:qr_id>', type='json', auth='user', methods=['DELETE'])
    def delete_qr_code(self, qr_id, **kwargs):
        """Supprime un QR code"""
        try:
            qr_code = request.env['edu.qr.code'].browse(qr_id)
            if not qr_code.exists():
                return {
                    'status': 'error',
                    'message': _('QR code non trouvé')
                }

            qr_code.unlink()

            return {
                'status': 'success',
                'message': _('QR code supprimé avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la suppression du QR code {qr_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Actions sur les QR codes
    @http.route('/api/qr-codes/<int:qr_id>/activate', type='json', auth='user', methods=['POST'])
    def activate_qr_code(self, qr_id, **kwargs):
        """Active un QR code"""
        try:
            qr_code = request.env['edu.qr.code'].browse(qr_id)
            if not qr_code.exists():
                return {
                    'status': 'error',
                    'message': _('QR code non trouvé')
                }

            qr_code.action_activate()

            return {
                'status': 'success',
                'data': self._format_qr_code(qr_code),
                'message': _('QR code activé avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de l'activation du QR code {qr_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/<int:qr_id>/deactivate', type='json', auth='user', methods=['POST'])
    def deactivate_qr_code(self, qr_id, **kwargs):
        """Désactive un QR code"""
        try:
            qr_code = request.env['edu.qr.code'].browse(qr_id)
            if not qr_code.exists():
                return {
                    'status': 'error',
                    'message': _('QR code non trouvé')
                }

            qr_code.action_deactivate()

            return {
                'status': 'success',
                'data': self._format_qr_code(qr_code),
                'message': _('QR code désactivé avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la désactivation du QR code {qr_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/<int:qr_id>/regenerate-token', type='json', auth='user', methods=['POST'])
    def regenerate_token(self, qr_id, **kwargs):
        """Régénère le token d'un QR code"""
        try:
            qr_code = request.env['edu.qr.code'].browse(qr_id)
            if not qr_code.exists():
                return {
                    'status': 'error',
                    'message': _('QR code non trouvé')
                }

            qr_code.regenerate_token()

            return {
                'status': 'success',
                'data': self._format_qr_code(qr_code, detailed=True),
                'message': _('Token régénéré avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la régénération du token {qr_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/<int:qr_id>/regenerate', type='json', auth='user', methods=['POST'])
    def regenerate_qr_code(self, qr_id, **kwargs):
        """Régénère complètement un QR code"""
        try:
            qr_code = request.env['edu.qr.code'].browse(qr_id)
            if not qr_code.exists():
                return {
                    'status': 'error',
                    'message': _('QR code non trouvé')
                }

            qr_code.regenerate_qr_code()

            return {
                'status': 'success',
                'data': self._format_qr_code(qr_code, detailed=True),
                'message': _('QR code régénéré avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la régénération du QR code {qr_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/<int:qr_id>/reset-usage', type='json', auth='user', methods=['POST'])
    def reset_usage(self, qr_id, **kwargs):
        """Remet à zéro les compteurs d'usage"""
        try:
            qr_code = request.env['edu.qr.code'].browse(qr_id)
            if not qr_code.exists():
                return {
                    'status': 'error',
                    'message': _('QR code non trouvé')
                }

            qr_code.action_reset_usage()

            return {
                'status': 'success',
                'data': self._format_qr_code(qr_code),
                'message': _('Compteurs remis à zéro avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la remise à zéro {qr_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/<int:qr_id>/image', type='http', auth='user', methods=['GET'])
    def download_qr_image(self, qr_id, **kwargs):
        """Télécharge l'image du QR code"""
        try:
            qr_code = request.env['edu.qr.code'].browse(qr_id)
            if not qr_code.exists():
                return request.not_found()

            if not qr_code.qr_image:
                return request.not_found()

            # Décoder l'image base64
            image_data = base64.b64decode(qr_code.qr_image)
            
            return request.make_response(
                image_data,
                headers=[
                    ('Content-Type', 'image/png'),
                    ('Content-Disposition', f'attachment; filename="{qr_code.qr_image_filename}"'),
                    ('Content-Length', len(image_data))
                ]
            )

        except Exception as e:
            _logger.error(f"Erreur lors du téléchargement de l'image QR {qr_id}: {e}")
            return request.not_found()

    @http.route('/api/qr-codes/<int:qr_id>/logs', type='json', auth='user', methods=['GET'])
    def get_qr_logs(self, qr_id, **kwargs):
        """Récupère les logs de sécurité d'un QR code"""
        try:
            qr_code = request.env['edu.qr.code'].browse(qr_id)
            if not qr_code.exists():
                return {
                    'status': 'error',
                    'message': _('QR code non trouvé')
                }

            limit = kwargs.get('limit', 50)
            offset = kwargs.get('offset', 0)
            
            logs = request.env['edu.qr.code.log'].search([
                ('qr_code_id', '=', qr_id)
            ], limit=limit, offset=offset, order='timestamp desc')

            return {
                'status': 'success',
                'data': [self._format_qr_log(log) for log in logs],
                'count': len(logs)
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des logs {qr_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Scan de QR codes
    @http.route('/api/qr-codes/scan', type='json', auth='user', methods=['POST'])
    def scan_qr_code(self, **kwargs):
        """Traite un scan de QR code"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            if not data.get('content'):
                return {
                    'status': 'error',
                    'message': _('Contenu du QR code manquant')
                }

            # Récupérer les informations de la requête
            device_id = data.get('device_id')
            ip_address = request.httprequest.environ.get('REMOTE_ADDR')
            user_agent = request.httprequest.environ.get('HTTP_USER_AGENT')

            # Traiter le scan
            result = request.env['edu.qr.code'].scan_qr_code(
                data['content'],
                device_id=device_id,
                ip_address=ip_address,
                user_agent=user_agent
            )

            return {
                'status': 'success' if result['success'] else 'error',
                'data': result,
                'message': result['message']
            }

        except Exception as e:
            _logger.error(f"Erreur lors du scan de QR code: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Génération rapide de QR codes
    @http.route('/api/qr-codes/generate/student', type='json', auth='user', methods=['POST'])
    def generate_student_qr(self, **kwargs):
        """Génère un QR code personnel pour un étudiant"""
        try:
            data = request.get_json_data()
            if not data or not data.get('student_id'):
                return {
                    'status': 'error',
                    'message': _('ID étudiant requis')
                }

            qr_code = request.env['edu.qr.code'].generate_student_qr(data['student_id'])

            return {
                'status': 'success',
                'data': self._format_qr_code(qr_code, detailed=True),
                'message': _('QR code étudiant généré avec succès')
            }

        except UserError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la génération QR étudiant: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/generate/session', type='json', auth='user', methods=['POST'])
    def generate_session_qr(self, **kwargs):
        """Génère un QR code pour une session"""
        try:
            data = request.get_json_data()
            if not data or not data.get('session_id'):
                return {
                    'status': 'error',
                    'message': _('ID session requis')
                }

            qr_code = request.env['edu.qr.code'].generate_session_qr(data['session_id'])

            return {
                'status': 'success',
                'data': self._format_qr_code(qr_code, detailed=True),
                'message': _('QR code session généré avec succès')
            }

        except UserError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la génération QR session: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # Recherche et statistiques
    @http.route('/api/qr-codes/search', type='json', auth='user', methods=['POST'])
    def search_qr_codes(self, **kwargs):
        """Recherche avancée de QR codes"""
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
                domain.append(('content', 'ilike', term))

            # Filtres multiples
            if data.get('qr_types'):
                domain.append(('qr_type', 'in', data['qr_types']))
                
            if data.get('active') is not None:
                domain.append(('active', '=', data['active']))
                
            if data.get('expired') is not None:
                domain.append(('is_expired', '=', data['expired']))

            # Période de création
            if data.get('date_range'):
                date_range = data['date_range']
                if date_range.get('start'):
                    domain.append(('create_date', '>=', date_range['start']))
                if date_range.get('end'):
                    domain.append(('create_date', '<=', date_range['end']))

            limit = data.get('limit', 50)
            qr_codes = request.env['edu.qr.code'].search(domain, limit=limit)

            return {
                'status': 'success',
                'data': [self._format_qr_code(qr) for qr in qr_codes],
                'count': len(qr_codes)
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la recherche de QR codes: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/statistics', type='json', auth='user', methods=['GET'])
    def get_qr_statistics(self, **kwargs):
        """Récupère les statistiques des QR codes"""
        try:
            # Statistiques par type
            stats_by_type = {}
            for qr_type, label in request.env['edu.qr.code']._fields['qr_type'].selection:
                total = request.env['edu.qr.code'].search_count([('qr_type', '=', qr_type)])
                active = request.env['edu.qr.code'].search_count([
                    ('qr_type', '=', qr_type), 
                    ('active', '=', True)
                ])
                expired = request.env['edu.qr.code'].search_count([
                    ('qr_type', '=', qr_type), 
                    ('is_expired', '=', True)
                ])
                stats_by_type[qr_type] = {
                    'label': label,
                    'total': total,
                    'active': active,
                    'expired': expired
                }

            # Statistiques d'usage
            all_qr = request.env['edu.qr.code'].search([])
            total_scans = sum(all_qr.mapped('scan_count'))
            total_success_scans = sum(all_qr.mapped('success_scan_count'))
            success_rate = (total_success_scans / total_scans * 100) if total_scans > 0 else 0

            # Top 10 des QR codes les plus utilisés
            top_qr_codes = request.env['edu.qr.code'].search([
                ('scan_count', '>', 0)
            ], order='scan_count desc', limit=10)

            return {
                'status': 'success',
                'data': {
                    'summary': {
                        'total_qr_codes': len(all_qr),
                        'active_qr_codes': len(all_qr.filtered('active')),
                        'expired_qr_codes': len(all_qr.filtered('is_expired')),
                        'total_scans': total_scans,
                        'successful_scans': total_success_scans,
                        'success_rate': round(success_rate, 2)
                    },
                    'by_type': stats_by_type,
                    'top_usage': [
                        {
                            'id': qr.id,
                            'name': qr.name,
                            'type': qr.qr_type,
                            'scan_count': qr.scan_count,
                            'success_count': qr.success_scan_count
                        } for qr in top_qr_codes
                    ]
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des statistiques QR: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/options', type='json', auth='user', methods=['GET'])
    def get_qr_options(self, **kwargs):
        """Récupère les options disponibles pour les QR codes"""
        try:
            qr_types = request.env['edu.qr.code']._fields['qr_type'].selection
            sizes = request.env['edu.qr.code']._fields['size'].selection
            error_corrections = request.env['edu.qr.code']._fields['error_correction'].selection
            
            return {
                'status': 'success',
                'data': {
                    'qr_types': [{'value': value, 'label': label} for value, label in qr_types],
                    'sizes': [{'value': value, 'label': label} for value, label in sizes],
                    'error_corrections': [{'value': value, 'label': label} for value, label in error_corrections]
                }
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des options QR: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _format_qr_code(self, qr_code, detailed=False):
        """Formate les données du QR code pour l'API"""
        data = {
            'id': qr_code.id,
            'name': qr_code.name,
            'qr_type': qr_code.qr_type,
            'active': qr_code.active,
            'is_expired': qr_code.is_expired,
            'size': qr_code.size,
            'error_correction': qr_code.error_correction,
            'usage_stats': {
                'scan_count': qr_code.scan_count,
                'success_scan_count': qr_code.success_scan_count,
                'current_uses': qr_code.current_uses,
                'max_uses': qr_code.max_uses
            },
            'expiry_date': qr_code.expiry_date.isoformat() if qr_code.expiry_date else None,
            'last_scan_date': qr_code.last_scan_date.isoformat() if qr_code.last_scan_date else None,
            'create_date': qr_code.create_date.isoformat() if qr_code.create_date else None
        }

        # Relations selon le type
        if qr_code.student_id:
            data['student'] = {
                'id': qr_code.student_id.id,
                'name': qr_code.student_id.name
            }
        if qr_code.faculty_id:
            data['faculty'] = {
                'id': qr_code.faculty_id.id,
                'name': qr_code.faculty_id.name
            }
        if qr_code.session_id:
            data['session'] = {
                'id': qr_code.session_id.id,
                'name': qr_code.session_id.name
            }
        if qr_code.device_id:
            data['device'] = {
                'id': qr_code.device_id.id,
                'name': qr_code.device_id.name
            }
        if qr_code.classroom_id:
            data['classroom'] = {
                'id': qr_code.classroom_id.id,
                'name': qr_code.classroom_id.name
            }

        if detailed:
            data.update({
                'content': qr_code.content,
                'qr_token': qr_code.qr_token[:10] + '...' if qr_code.qr_token else None,  # Masqué pour sécurité
                'security_hash': qr_code.security_hash[:16] + '...' if qr_code.security_hash else None,
                'border_size': qr_code.border_size,
                'is_single_use': qr_code.is_single_use,
                'time_restrictions': qr_code.time_restrictions,
                'valid_from_time': qr_code.valid_from_time,
                'valid_to_time': qr_code.valid_to_time,
                'has_qr_image': bool(qr_code.qr_image),
                'qr_image_filename': qr_code.qr_image_filename,
                'allowed_devices': [
                    {
                        'id': device.id,
                        'name': device.name,
                        'code': device.code
                    } for device in qr_code.allowed_devices
                ],
                'ip_whitelist': qr_code.ip_whitelist,
                'last_scan_ip': qr_code.last_scan_ip,
                'last_scan_device': qr_code.last_scan_device,
                'write_date': qr_code.write_date.isoformat() if qr_code.write_date else None
            })

        return data

    def _format_qr_log(self, log):
        """Formate un log de QR code pour l'API"""
        return {
            'id': log.id,
            'event_type': log.event_type,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None,
            'user': {
                'id': log.user_id.id if log.user_id else None,
                'name': log.user_id.name if log.user_id else None
            },
            'ip_address': log.ip_address,
            'device': {
                'id': log.device_id.id if log.device_id else None,
                'name': log.device_id.name if log.device_id else None
            },
            'user_agent': log.user_agent,
            'details': log.details
        }

    def _prepare_qr_data(self, data, update=False):
        """Prépare les données pour la création/mise à jour"""
        allowed_fields = [
            'name', 'qr_type', 'content', 'student_id', 'teacher_id', 'session_id',
            'device_id', 'classroom_name', 'size', 'error_correction', 'border_size',
            'active', 'expiry_date', 'max_uses', 'is_single_use', 'time_restrictions',
            'valid_from_time', 'valid_to_time', 'ip_whitelist'
        ]
        
        # En mode mise à jour, certains champs sensibles sont exclus
        if update:
            excluded_fields = ['qr_type', 'student_id', 'teacher_id', 'session_id', 'device_id']
            allowed_fields = [f for f in allowed_fields if f not in excluded_fields]
        
        qr_data = {}
        for field in allowed_fields:
            if field in data:
                qr_data[field] = data[field]
        
        # Gestion des relations Many2many
        if 'allowed_device_ids' in data:
            qr_data['allowed_devices'] = [(6, 0, data['allowed_device_ids'])]
        
        return qr_data


class EduQRCodePublicController(http.Controller):
    """Contrôleur API public pour les QR codes (accès très limité)"""

    @http.route('/api/public/qr-codes/scan', type='json', auth='public', methods=['POST'])
    def public_scan_qr_code(self, **kwargs):
        """Endpoint public pour scan de QR code avec authentification par token"""
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

            # Valider le token (à implémenter selon votre système de sécurité)
            if not self._validate_auth_token(data['auth_token']):
                return {
                    'status': 'error',
                    'message': _('Token d\'authentification invalide')
                }

            if not data.get('content'):
                return {
                    'status': 'error',
                    'message': _('Contenu du QR code manquant')
                }

            # Récupérer les informations de la requête
            device_id = data.get('device_id')
            ip_address = request.httprequest.environ.get('REMOTE_ADDR')
            user_agent = request.httprequest.environ.get('HTTP_USER_AGENT')

            # Traiter le scan avec sudo
            result = request.env['edu.qr.code'].sudo().scan_qr_code(
                data['content'],
                device_id=device_id,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Limiter les informations retournées en mode public
            if result['success']:
                return {
                    'status': 'success',
                    'data': {
                        'success': True,
                        'qr_type': result.get('qr_type'),
                        'message': result['message']
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': result['message']
                }

        except Exception as e:
            _logger.error(f"Erreur lors du scan public de QR code: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors du scan')
            }

    @http.route('/api/public/qr-codes/validate', type='json', auth='public', methods=['POST'])
    def public_validate_qr_code(self, **kwargs):
        """Valide un QR code sans l'utiliser (vérification préliminaire)"""
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

            if not data.get('content'):
                return {
                    'status': 'error',
                    'message': _('Contenu du QR code manquant')
                }

            # Parser le contenu pour validation
            try:
                parts = data['content'].split(':')
                if len(parts) < 3:
                    return {
                        'status': 'error',
                        'message': _('Format de QR code invalide')
                    }

                qr_type, record_id, token = parts[0], int(parts[1]), parts[2]

                # Trouver le QR code correspondant
                qr_code = request.env['edu.qr.code'].sudo().search([
                    ('qr_type', '=', qr_type),
                    ('qr_token', '=', token),
                    ('content', '=', data['content'])
                ], limit=1)

                if not qr_code:
                    return {
                        'status': 'error',
                        'message': _('QR code non trouvé ou invalide')
                    }

                # Vérifications de base (sans incrémenter les compteurs)
                valid = True
                reasons = []

                if not qr_code.active:
                    valid = False
                    reasons.append('inactive')

                if qr_code.is_expired:
                    valid = False
                    reasons.append('expired')

                # Vérifier les restrictions horaires
                if qr_code.time_restrictions:
                    import datetime
                    now = datetime.datetime.now()
                    current_time = now.hour + now.minute / 60.0
                    
                    if not (qr_code.valid_from_time <= current_time <= qr_code.valid_to_time):
                        valid = False
                        reasons.append('time_restricted')

                return {
                    'status': 'success',
                    'data': {
                        'valid': valid,
                        'qr_type': qr_code.qr_type,
                        'reasons': reasons,
                        'expiry_date': qr_code.expiry_date.isoformat() if qr_code.expiry_date else None,
                        'is_single_use': qr_code.is_single_use,
                        'current_uses': qr_code.current_uses,
                        'max_uses': qr_code.max_uses
                    }
                }

            except (ValueError, IndexError):
                return {
                    'status': 'error',
                    'message': _('Format de QR code invalide')
                }

        except Exception as e:
            _logger.error(f"Erreur lors de la validation publique de QR code: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la validation')
            }

    @http.route('/api/public/qr-codes/info', type='json', auth='public', methods=['POST'])
    def public_get_qr_info(self, **kwargs):
        """Récupère les informations publiques d'un QR code"""
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

            if not data.get('content'):
                return {
                    'status': 'error',
                    'message': _('Contenu du QR code manquant')
                }

            # Parser et trouver le QR code
            try:
                parts = data['content'].split(':')
                if len(parts) < 3:
                    return {
                        'status': 'error',
                        'message': _('Format de QR code invalide')
                    }

                qr_type, record_id, token = parts[0], int(parts[1]), parts[2]

                qr_code = request.env['edu.qr.code'].sudo().search([
                    ('qr_type', '=', qr_type),
                    ('qr_token', '=', token),
                    ('content', '=', data['content'])
                ], limit=1)

                if not qr_code:
                    return {
                        'status': 'error',
                        'message': _('QR code non trouvé')
                    }

                # Retourner uniquement les informations publiques
                public_info = {
                    'qr_type': qr_code.qr_type,
                    'name': qr_code.name,
                    'active': qr_code.active,
                    'is_expired': qr_code.is_expired,
                    'is_single_use': qr_code.is_single_use
                }

                # Ajouter des informations spécifiques selon le type
                if qr_code.qr_type == 'student' and qr_code.student_id:
                    public_info['student_name'] = qr_code.student_id.name
                elif qr_code.qr_type == 'faculty' and qr_code.faculty_id:
                    public_info['faculty_name'] = qr_code.faculty_id.name
                elif qr_code.qr_type == 'session' and qr_code.session_id:
                    public_info['session_name'] = qr_code.session_id.name

                return {
                    'status': 'success',
                    'data': public_info
                }

            except (ValueError, IndexError):
                return {
                    'status': 'error',
                    'message': _('Format de QR code invalide')
                }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des infos publiques QR: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la récupération des informations')
            }

    def _validate_auth_token(self, token):
        """Valide le token d'authentification pour l'API publique"""
        try:
            # Implémentation de validation de token à personnaliser
            # Exemple simple: vérifier contre une liste de tokens valides
            valid_tokens = request.env['ir.config_parameter'].sudo().get_param('qr.api.tokens', '').split(',')
            return token.strip() in [t.strip() for t in valid_tokens if t.strip()]
        except Exception:
            return False


class EduQRCodeBulkController(http.Controller):
    """Contrôleur pour les opérations en lot sur les QR codes"""

    @http.route('/api/qr-codes/bulk/generate', type='json', auth='user', methods=['POST'])
    def bulk_generate_qr_codes(self, **kwargs):
        """Génère plusieurs QR codes en lot"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            qr_type = data.get('qr_type')
            if not qr_type:
                return {
                    'status': 'error',
                    'message': _('Type de QR code requis')
                }

            generated_qr_codes = []
            errors = []

            if qr_type == 'student' and data.get('student_ids'):
                for student_id in data['student_ids']:
                    try:
                        qr_code = request.env['edu.qr.code'].generate_student_qr(student_id)
                        generated_qr_codes.append(self._format_qr_code(qr_code))
                    except Exception as e:
                        errors.append(f"Étudiant {student_id}: {str(e)}")

            elif qr_type == 'session' and data.get('session_ids'):
                for session_id in data['session_ids']:
                    try:
                        qr_code = request.env['edu.qr.code'].generate_session_qr(session_id)
                        generated_qr_codes.append(self._format_qr_code(qr_code))
                    except Exception as e:
                        errors.append(f"Session {session_id}: {str(e)}")

            else:
                return {
                    'status': 'error',
                    'message': _('Type de génération en lot non supporté ou IDs manquants')
                }

            return {
                'status': 'success' if not errors else 'partial',
                'data': {
                    'generated_qr_codes': generated_qr_codes,
                    'success_count': len(generated_qr_codes),
                    'error_count': len(errors),
                    'errors': errors
                },
                'message': f'{len(generated_qr_codes)} QR codes générés avec succès'
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la génération en lot: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/qr-codes/bulk/actions', type='json', auth='user', methods=['POST'])
    def bulk_actions_qr_codes(self, **kwargs):
        """Effectue des actions en lot sur plusieurs QR codes"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            qr_ids = data.get('qr_ids', [])
            action = data.get('action')

            if not qr_ids or not action:
                return {
                    'status': 'error',
                    'message': _('IDs des QR codes et action requis')
                }

            qr_codes = request.env['edu.qr.code'].browse(qr_ids)
            
            success_count = 0
            error_count = 0
            errors = []

            for qr_code in qr_codes:
                try:
                    if action == 'activate':
                        qr_code.action_activate()
                    elif action == 'deactivate':
                        qr_code.action_deactivate()
                    elif action == 'reset_usage':
                        qr_code.action_reset_usage()
                    elif action == 'regenerate_token':
                        qr_code.regenerate_token()
                    elif action == 'regenerate':
                        qr_code.regenerate_qr_code()
                    else:
                        errors.append(f"Action inconnue: {action}")
                        error_count += 1
                        continue
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"QR {qr_code.id}: {str(e)}")

            return {
                'status': 'success' if error_count == 0 else 'partial',
                'data': {
                    'success_count': success_count,
                    'error_count': error_count,
                    'total_count': len(qr_ids),
                    'errors': errors
                },
                'message': f'{success_count} QR codes traités avec succès'
            }

        except Exception as e:
            _logger.error(f"Erreur lors des actions en lot: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _format_qr_code(self, qr_code):
        """Formate les données du QR code (version simplifiée pour le bulk)"""
        controller = EduQRCodeController()
        return controller._format_qr_code(qr_code)