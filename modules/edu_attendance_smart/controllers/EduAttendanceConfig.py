# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduAttendanceConfigController(http.Controller):
    """Contrôleur API pour la configuration des présences"""

    @http.route('/api/attendance/config', type='json', auth='user', methods=['GET'])
    def get_configs(self, **kwargs):
        """Récupère toutes les configurations de présences"""
        try:
            configs = request.env['edu.attendance.config'].search([])
            return {
                'status': 'success',
                'data': [self._format_config(config) for config in configs],
                'count': len(configs)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des configurations: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/config/<int:config_id>', type='json', auth='user', methods=['GET'])
    def get_config(self, config_id, **kwargs):
        """Récupère une configuration spécifique"""
        try:
            config = request.env['edu.attendance.config'].browse(config_id)
            if not config.exists():
                return {
                    'status': 'error',
                    'message': _('Configuration non trouvée')
                }
            
            return {
                'status': 'success',
                'data': self._format_config(config)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la configuration {config_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/config/active', type='json', auth='user', methods=['GET'])
    def get_active_config(self, **kwargs):
        """Récupère la configuration active"""
        try:
            config = request.env['edu.attendance.config'].get_active_config()
            return {
                'status': 'success',
                'data': self._format_config(config)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la configuration active: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/config', type='json', auth='user', methods=['POST'])
    def create_config(self, **kwargs):
        """Crée une nouvelle configuration"""
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
                    'message': _('Le nom de la configuration est obligatoire')
                }

            # Création de la configuration
            config_data = self._prepare_config_data(data)
            config = request.env['edu.attendance.config'].create(config_data)

            return {
                'status': 'success',
                'data': self._format_config(config),
                'message': _('Configuration créée avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la configuration: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/config/<int:config_id>', type='json', auth='user', methods=['PUT'])
    def update_config(self, config_id, **kwargs):
        """Met à jour une configuration existante"""
        try:
            config = request.env['edu.attendance.config'].browse(config_id)
            if not config.exists():
                return {
                    'status': 'error',
                    'message': _('Configuration non trouvée')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Préparation des données
            config_data = self._prepare_config_data(data)
            config.write(config_data)

            return {
                'status': 'success',
                'data': self._format_config(config),
                'message': _('Configuration mise à jour avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour de la configuration {config_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/config/<int:config_id>', type='json', auth='user', methods=['DELETE'])
    def delete_config(self, config_id, **kwargs):
        """Supprime une configuration"""
        try:
            config = request.env['edu.attendance.config'].browse(config_id)
            if not config.exists():
                return {
                    'status': 'error',
                    'message': _('Configuration non trouvée')
                }

            # Vérifier si c'est la configuration active
            if config.active:
                return {
                    'status': 'error',
                    'message': _('Impossible de supprimer la configuration active')
                }

            config.unlink()

            return {
                'status': 'success',
                'message': _('Configuration supprimée avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la suppression de la configuration {config_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/config/<int:config_id>/activate', type='json', auth='user', methods=['POST'])
    def activate_config(self, config_id, **kwargs):
        """Active une configuration spécifique"""
        try:
            config = request.env['edu.attendance.config'].browse(config_id)
            if not config.exists():
                return {
                    'status': 'error',
                    'message': _('Configuration non trouvée')
                }

            # Désactiver toutes les autres configurations
            request.env['edu.attendance.config'].search([('id', '!=', config_id)]).write({'active': False})
            
            # Activer la configuration sélectionnée
            config.write({'active': True})

            return {
                'status': 'success',
                'data': self._format_config(config),
                'message': _('Configuration activée avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de l'activation de la configuration {config_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/attendance/config/validate', type='json', auth='user', methods=['POST'])
    def validate_config(self, **kwargs):
        """Valide les données de configuration sans les sauvegarder"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des données
            errors = self._validate_config_data(data)
            
            if errors:
                return {
                    'status': 'error',
                    'message': _('Données invalides'),
                    'errors': errors
                }

            return {
                'status': 'success',
                'message': _('Configuration valide')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la validation de la configuration: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _format_config(self, config):
        """Formate les données de configuration pour l'API"""
        return {
            'id': config.id,
            'name': config.name,
            'active': config.active,
            'auto_mark_absent_delay': config.auto_mark_absent_delay,
            'late_threshold': config.late_threshold,
            'early_departure_threshold': config.early_departure_threshold,
            'grace_period': config.grace_period,
            'require_excuse_for_absence': config.require_excuse_for_absence,
            'allow_self_excuse': config.allow_self_excuse,
            'max_excuse_days': config.max_excuse_days,
            'require_excuse_document': config.require_excuse_document,
            'notify_parents_absence': config.notify_parents_absence,
            'notification_delay': config.notification_delay,
            'notify_late_arrival': config.notify_late_arrival,
            'notify_early_departure': config.notify_early_departure,
            'working_days_only': config.working_days_only,
            'weekend_notification': config.weekend_notification,
            'holiday_notification': config.holiday_notification,
            'require_photo_verification': config.require_photo_verification,
            'require_gps_verification': config.require_gps_verification,
            'allow_manual_override': config.allow_manual_override,
            'require_validation': config.require_validation,
            'generate_daily_reports': config.generate_daily_reports,
            'generate_weekly_reports': config.generate_weekly_reports,
            'attendance_rate_threshold': config.attendance_rate_threshold,
            'auto_archive_delay': config.auto_archive_delay,
            'keep_logs_duration': config.keep_logs_duration,
            'create_date': config.create_date.isoformat() if config.create_date else None,
            'write_date': config.write_date.isoformat() if config.write_date else None,
        }

    def _prepare_config_data(self, data):
        """Prépare les données pour la création/mise à jour"""
        allowed_fields = [
            'name', 'active', 'auto_mark_absent_delay', 'late_threshold',
            'early_departure_threshold', 'grace_period', 'require_excuse_for_absence',
            'allow_self_excuse', 'max_excuse_days', 'require_excuse_document',
            'notify_parents_absence', 'notification_delay', 'notify_late_arrival',
            'notify_early_departure', 'working_days_only', 'weekend_notification',
            'holiday_notification', 'require_photo_verification', 'require_gps_verification',
            'allow_manual_override', 'require_validation', 'generate_daily_reports',
            'generate_weekly_reports', 'attendance_rate_threshold', 'auto_archive_delay',
            'keep_logs_duration'
        ]
        
        config_data = {}
        for field in allowed_fields:
            if field in data:
                config_data[field] = data[field]
        
        return config_data

    def _validate_config_data(self, data):
        """Valide les données de configuration"""
        errors = []
        
        # Validation du nom
        if not data.get('name'):
            errors.append(_('Le nom de la configuration est obligatoire'))
        
        # Validation des seuils
        if 'auto_mark_absent_delay' in data and data['auto_mark_absent_delay'] < 0:
            errors.append(_('Le délai d\'absence automatique doit être positif'))
        
        if 'late_threshold' in data and data['late_threshold'] < 0:
            errors.append(_('Le seuil de retard doit être positif'))
        
        if 'early_departure_threshold' in data and data['early_departure_threshold'] < 0:
            errors.append(_('Le seuil de départ anticipé doit être positif'))
        
        # Validation du taux de présence
        if 'attendance_rate_threshold' in data:
            rate = data['attendance_rate_threshold']
            if not (0 <= rate <= 100):
                errors.append(_('Le taux de présence doit être entre 0 et 100%'))
        
        return errors


class EduAttendanceConfigPublicController(http.Controller):
    """Contrôleur API public pour la configuration des présences (accès limité)"""

    @http.route('/api/public/attendance/config/active', type='json', auth='public', methods=['GET'])
    def get_public_active_config(self, **kwargs):
        """Récupère les paramètres publics de la configuration active"""
        try:
            config = request.env['edu.attendance.config'].sudo().get_active_config()
            
            # Retourner uniquement les données publiques
            public_data = {
                'late_threshold': config.late_threshold,
                'early_departure_threshold': config.early_departure_threshold,
                'grace_period': config.grace_period,
                'working_days_only': config.working_days_only,
                'require_photo_verification': config.require_photo_verification,
                'require_gps_verification': config.require_gps_verification,
            }
            
            return {
                'status': 'success',
                'data': public_data
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la configuration publique: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la récupération des paramètres')
            }