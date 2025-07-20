# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime, timedelta
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError, UserError
from odoo.http import serialize_exception

_logger = logging.getLogger(__name__)


class EduAttendanceDeviceController(http.Controller):
    """Contrôleur API pour la gestion des dispositifs de pointage"""

    @http.route('/api/attendance/devices', type='json', auth='user', methods=['GET'])
    def get_devices(self, **kwargs):
        """Récupère tous les dispositifs de pointage"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('active_only'):
                domain.append(('state', '=', 'active'))
            
            if kwargs.get('online_only'):
                domain.append(('online', '=', True))
                
            if kwargs.get('device_type'):
                domain.append(('device_type', '=', kwargs['device_type']))
                
            if kwargs.get('location_id'):
                domain.append(('location_id', '=', kwargs['location_id']))

            devices = request.env['edu.attendance.device'].search(domain)
            
            return {
                'status': 'success',
                'data': [self._format_device(device) for device in devices],
                'count': len(devices)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des dispositifs: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices/<int:device_id>', type='json', auth='user', methods=['GET'])
    def get_device(self, device_id, **kwargs):
        """Récupère un dispositif spécifique"""
        try:
            device = request.env['edu.attendance.device'].browse(device_id)
            if not device.exists():
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé')
                }
            
            return {
                'status': 'success',
                'data': self._format_device(device, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du dispositif {device_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices/by-code/<string:code>', type='json', auth='user', methods=['GET'])
    def get_device_by_code(self, code, **kwargs):
        """Récupère un dispositif par son code"""
        try:
            device = request.env['edu.attendance.device'].search([('code', '=', code)], limit=1)
            if not device:
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé')
                }
            
            return {
                'status': 'success',
                'data': self._format_device(device, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du dispositif {code}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices', type='json', auth='user', methods=['POST'])
    def create_device(self, **kwargs):
        """Crée un nouveau dispositif"""
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
                    'message': _('Le nom du dispositif est obligatoire')
                }

            if not data.get('code'):
                return {
                    'status': 'error',
                    'message': _('Le code du dispositif est obligatoire')
                }

            # Création du dispositif
            device_data = self._prepare_device_data(data)
            device = request.env['edu.attendance.device'].create(device_data)

            return {
                'status': 'success',
                'data': self._format_device(device, detailed=True),
                'message': _('Dispositif créé avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la création du dispositif: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices/<int:device_id>', type='json', auth='user', methods=['PUT'])
    def update_device(self, device_id, **kwargs):
        """Met à jour un dispositif existant"""
        try:
            device = request.env['edu.attendance.device'].browse(device_id)
            if not device.exists():
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Préparation des données
            device_data = self._prepare_device_data(data)
            device.write(device_data)

            return {
                'status': 'success',
                'data': self._format_device(device, detailed=True),
                'message': _('Dispositif mis à jour avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour du dispositif {device_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices/<int:device_id>', type='json', auth='user', methods=['DELETE'])
    def delete_device(self, device_id, **kwargs):
        """Supprime un dispositif"""
        try:
            device = request.env['edu.attendance.device'].browse(device_id)
            if not device.exists():
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé')
                }

            # Vérifier s'il y a des enregistrements de présence liés
            attendance_count = request.env['edu.attendance.record'].search_count([
                ('device_id', '=', device_id)
            ])
            
            if attendance_count > 0:
                return {
                    'status': 'error',
                    'message': _('Impossible de supprimer le dispositif: il a des enregistrements de présence associés')
                }

            device.unlink()

            return {
                'status': 'success',
                'message': _('Dispositif supprimé avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la suppression du dispositif {device_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices/<int:device_id>/ping', type='json', auth='user', methods=['POST'])
    def ping_device(self, device_id, **kwargs):
        """Teste la connexion au dispositif"""
        try:
            device = request.env['edu.attendance.device'].browse(device_id)
            if not device.exists():
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé')
                }

            result = device.action_ping_device()
            
            return {
                'status': 'success',
                'data': {
                    'online': device.online,
                    'last_ping': device.last_ping.isoformat() if device.last_ping else None
                },
                'message': _('Test de connexion effectué')
            }

        except Exception as e:
            _logger.error(f"Erreur lors du ping du dispositif {device_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices/<int:device_id>/reset', type='json', auth='user', methods=['POST'])
    def reset_device(self, device_id, **kwargs):
        """Redémarre le dispositif"""
        try:
            device = request.env['edu.attendance.device'].browse(device_id)
            if not device.exists():
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé')
                }

            device.action_reset_device()

            return {
                'status': 'success',
                'message': _('Redémarrage du dispositif lancé')
            }

        except Exception as e:
            _logger.error(f"Erreur lors du redémarrage du dispositif {device_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices/<int:device_id>/access-check', type='json', auth='user', methods=['POST'])
    def check_device_access(self, device_id, **kwargs):
        """Vérifie si l'utilisateur peut accéder au dispositif"""
        try:
            device = request.env['edu.attendance.device'].browse(device_id)
            if not device.exists():
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé')
                }

            user = request.env.user
            has_access = device.is_accessible_by_user(user)

            return {
                'status': 'success',
                'data': {
                    'has_access': has_access,
                    'device_active': device.active,
                    'device_online': device.online,
                    'working_hours': {
                        'start': device.working_hours_start,
                        'end': device.working_hours_end
                    }
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la vérification d'accès au dispositif {device_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices/<int:device_id>/location-check', type='json', auth='user', methods=['POST'])
    def check_device_location(self, device_id, **kwargs):
        """Vérifie la proximité géographique avec le dispositif"""
        try:
            device = request.env['edu.attendance.device'].browse(device_id)
            if not device.exists():
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé')
                }

            data = request.get_json_data()
            if not data or 'latitude' not in data or 'longitude' not in data:
                return {
                    'status': 'error',
                    'message': _('Coordonnées GPS manquantes')
                }

            latitude = data['latitude']
            longitude = data['longitude']
            
            in_range = device.is_in_range(latitude, longitude)

            return {
                'status': 'success',
                'data': {
                    'in_range': in_range,
                    'allowed_distance': device.allowed_distance,
                    'device_coordinates': {
                        'latitude': device.latitude,
                        'longitude': device.longitude
                    } if device.latitude and device.longitude else None
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la vérification de localisation du dispositif {device_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices/<int:device_id>/statistics', type='json', auth='user', methods=['GET'])
    def get_device_statistics(self, device_id, **kwargs):
        """Récupère les statistiques du dispositif"""
        try:
            device = request.env['edu.attendance.device'].browse(device_id)
            if not device.exists():
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé')
                }

            # Calcul des statistiques supplémentaires
            today = fields.Date.context_today(request.env['edu.attendance.device'])
            week_start = today - timedelta(days=today.weekday())
            
            # Statistiques de la semaine
            weekly_scans = request.env['edu.attendance.record'].search_count([
                ('device_id', '=', device_id),
                ('check_in_time', '>=', week_start),
                ('check_in_time', '<', today + timedelta(days=1))
            ])

            return {
                'status': 'success',
                'data': {
                    'device_id': device.id,
                    'device_name': device.name,
                    'daily_scans': device.total_scans_today,
                    'monthly_scans': device.total_scans_month,
                    'weekly_scans': weekly_scans,
                    'last_scan': device.last_scan_time.isoformat() if device.last_scan_time else None,
                    'online_status': device.online,
                    'last_ping': device.last_ping.isoformat() if device.last_ping else None,
                    'battery_level': device.battery_level
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des statistiques du dispositif {device_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices/<int:device_id>/attendance-records', type='json', auth='user', methods=['GET'])
    def get_device_attendance_records(self, device_id, **kwargs):
        """Récupère les enregistrements de présence du dispositif"""
        try:
            device = request.env['edu.attendance.device'].browse(device_id)
            if not device.exists():
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé')
                }

            domain = [('device_id', '=', device_id)]
            
            # Filtres optionnels
            if kwargs.get('date_from'):
                domain.append(('check_in_time', '>=', kwargs['date_from']))
            if kwargs.get('date_to'):
                domain.append(('check_in_time', '<=', kwargs['date_to']))

            limit = kwargs.get('limit', 100)
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
                'data': [self._format_attendance_record(record) for record in records],
                'count': len(records),
                'total_count': total_count
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des enregistrements du dispositif {device_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/devices/types', type='json', auth='user', methods=['GET'])
    def get_device_types(self, **kwargs):
        """Récupère la liste des types de dispositifs disponibles"""
        try:
            device_types = request.env['edu.attendance.device']._fields['device_type'].selection
            
            return {
                'status': 'success',
                'data': [{'value': value, 'label': label} for value, label in device_types]
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des types de dispositifs: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _format_device(self, device, detailed=False):
        """Formate les données du dispositif pour l'API"""
        data = {
            'id': device.id,
            'name': device.name,
            'code': device.code,
            'device_type': device.device_type,
            'active': device.active,
            'online': device.online,
            'last_ping': device.last_ping.isoformat() if device.last_ping else None,
            'location': {
                'id': device.location_id.id if device.location_id else None,
                'name': device.location_id.name if device.location_id else None
            },
            'room': {
                'id': device.room_id.id if device.room_id else None,
                'name': device.room_id.name if device.room_id else None
            },
            'building': device.building,
            'floor': device.floor,
            'statistics': {
                'total_scans_today': device.total_scans_today,
                'total_scans_month': device.total_scans_month,
                'last_scan_time': device.last_scan_time.isoformat() if device.last_scan_time else None
            }
        }

        if detailed:
            data.update({
                'description': device.description,
                'ip_address': device.ip_address,
                'mac_address': device.mac_address,
                'serial_number': device.serial_number,
                'battery_level': device.battery_level,
                'allow_check_in': device.allow_check_in,
                'allow_check_out': device.allow_check_out,
                'require_photo': device.require_photo,
                'require_geolocation': device.require_geolocation,
                'allowed_distance': device.allowed_distance,
                'coordinates': {
                    'latitude': device.latitude,
                    'longitude': device.longitude
                } if device.latitude and device.longitude else None,
                'working_hours': {
                    'start': device.working_hours_start,
                    'end': device.working_hours_end
                },
                'timezone': device.timezone,
                'installation_date': device.installation_date.isoformat() if device.installation_date else None,
                'last_maintenance': device.last_maintenance.isoformat() if device.last_maintenance else None,
                'next_maintenance': device.next_maintenance.isoformat() if device.next_maintenance else None,
                'warranty_end': device.warranty_end.isoformat() if device.warranty_end else None,
                'vendor': device.vendor,
                'model': device.model,
                'firmware_version': device.firmware_version,
                'create_date': device.create_date.isoformat() if device.create_date else None,
                'write_date': device.write_date.isoformat() if device.write_date else None
            })

        return data

    def _format_attendance_record(self, record):
        """Formate un enregistrement de présence"""
        return {
            'id': record.id,
            'student': {
                'id': record.student_id.id if record.student_id else None,
                'name': record.student_id.name if record.student_id else None
            },
            'check_in_time': record.check_in_time.isoformat() if record.check_in_time else None,
            'check_out_time': record.check_out_time.isoformat() if record.check_out_time else None,
            'status': record.status if hasattr(record, 'status') else None
        }

    def _prepare_device_data(self, data):
        """Prépare les données pour la création/mise à jour"""
        allowed_fields = [
            'name', 'code', 'description', 'device_type', 'location_id', 'room_id',
            'building', 'floor', 'ip_address', 'mac_address', 'serial_number',
            'api_key', 'api_endpoint', 'active', 'battery_level', 'allow_check_in',
            'allow_check_out', 'require_photo', 'require_geolocation', 'allowed_distance',
            'latitude', 'longitude', 'working_hours_start', 'working_hours_end',
            'timezone', 'installation_date', 'last_maintenance', 'next_maintenance',
            'warranty_end', 'vendor', 'model', 'firmware_version'
        ]
        
        device_data = {}
        for field in allowed_fields:
            if field in data:
                device_data[field] = data[field]
        
        # Gestion des relations Many2many
        if 'user_group_ids' in data:
            device_data['user_group_ids'] = [(6, 0, data['user_group_ids'])]
        
        if 'standard_ids' in data:
            device_data['standard_ids'] = [(6, 0, data['standard_ids'])]
        
        return device_data


class EduAttendanceDevicePublicController(http.Controller):
    """Contrôleur API public pour les dispositifs de pointage"""

    @http.route('/api/public/attendance/devices/<string:code>/info', type='json', auth='public', methods=['GET'])
    def get_public_device_info(self, code, **kwargs):
        """Récupère les informations publiques d'un dispositif"""
        try:
            device = request.env['edu.attendance.device'].sudo().search([
                ('code', '=', code),
                ('active', '=', True)
            ], limit=1)
            
            if not device:
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé ou inactif')
                }

            # Retourner uniquement les données publiques nécessaires
            return {
                'status': 'success',
                'data': {
                    'name': device.name,
                    'device_type': device.device_type,
                    'require_photo': device.require_photo,
                    'require_geolocation': device.require_geolocation,
                    'allowed_distance': device.allowed_distance,
                    'coordinates': {
                        'latitude': device.latitude,
                        'longitude': device.longitude
                    } if device.latitude and device.longitude else None,
                    'working_hours': {
                        'start': device.working_hours_start,
                        'end': device.working_hours_end
                    },
                    'timezone': device.timezone
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des infos publiques du dispositif {code}: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la récupération des informations')
            }

    @http.route('/api/public/attendance/devices/<string:code>/heartbeat', type='json', auth='public', methods=['POST'])
    def device_heartbeat(self, code, **kwargs):
        """Endpoint pour le heartbeat des dispositifs"""
        try:
            device = request.env['edu.attendance.device'].sudo().search([
                ('code', '=', code)
            ], limit=1)
            
            if not device:
                return {
                    'status': 'error',
                    'message': _('Dispositif non trouvé')
                }

            # Mettre à jour le timestamp de dernière connexion
            device.sudo().write({
                'last_ping': fields.Datetime.now()
            })

            # Optionnel: mettre à jour le niveau de batterie s'il est fourni
            data = request.get_json_data()
            if data and 'battery_level' in data:
                device.sudo().write({
                    'battery_level': data['battery_level']
                })

            return {
                'status': 'success',
                'data': {
                    'timestamp': fields.Datetime.now().isoformat(),
                    'device_active': device.active
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors du heartbeat du dispositif {code}: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la mise à jour du heartbeat')
            }