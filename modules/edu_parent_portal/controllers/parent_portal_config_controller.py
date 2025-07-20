# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class ParentPortalConfigController(http.Controller):

    @http.route('/api/portal/config/active', type='json', auth='public', methods=['GET'])
    def get_active_config(self):
        """Récupère la configuration active du portail"""
        config = request.env['edu.parent.portal.config'].sudo().get_active_config()
        return {
            'success': True,
            'config': {
                'name': config.name,
                'theme_colors': config.get_theme_colors(),
                'enable_notifications': config.enable_notifications,
                'enable_payments': config.enable_payments,
                'enable_appointments': config.enable_appointments,
                'maintenance_mode': config.maintenance_mode,
                'maintenance_message': config.maintenance_message,
                'session_timeout': config.session_timeout,
                'available_hours': {
                    'start': config.available_hours_start,
                    'end': config.available_hours_end
                }
            }
        }

    @http.route('/api/portal/config/<int:config_id>/maintenance', type='json', auth='user', methods=['POST'])
    def toggle_maintenance_mode(self, config_id, **kw):
        """Activer ou désactiver le mode maintenance"""
        action = kw.get('action')
        config = request.env['edu.parent.portal.config'].sudo().browse(config_id)

        if not config.exists():
            return {'success': False, 'error': 'Config not found'}

        if action == 'enable':
            config.action_enable_maintenance()
        elif action == 'disable':
            config.action_disable_maintenance()
        else:
            return {'success': False, 'error': 'Invalid action'}

        return {'success': True, 'maintenance_mode': config.maintenance_mode}

    @http.route('/api/portal/config/<int:config_id>/reset_sessions', type='json', auth='user', methods=['POST'])
    def reset_all_sessions(self, config_id):
        """Réinitialiser toutes les sessions des utilisateurs du portail"""
        config = request.env['edu.parent.portal.config'].sudo().browse(config_id)

        if not config.exists():
            return {'success': False, 'error': 'Config not found'}

        config.action_reset_all_sessions()
        return {'success': True}

    @http.route('/api/portal/config/stats', type='json', auth='user', methods=['GET'])
    def portal_statistics(self):
        """Obtenir les statistiques du portail"""
        config = request.env['edu.parent.portal.config'].sudo().get_active_config()

        return {
            'success': True,
            'statistics': {
                'total_active_parents': config.total_active_parents,
                'total_portal_users': config.total_portal_users,
                'avg_daily_visits': config.avg_daily_visits
            }
        }

    @http.route('/api/portal/config/<int:config_id>/sync_users', type='json', auth='user', methods=['POST'])
    def sync_portal_users(self, config_id):
        """Synchroniser les utilisateurs du portail"""
        config = request.env['edu.parent.portal.config'].sudo().browse(config_id)

        if not config.exists():
            return {'success': False, 'error': 'Config not found'}

        result = config.action_sync_users()
        return {
            'success': True,
            'message': result.get('params', {}).get('message', '')
        }

    @http.route('/api/portal/config/<int:config_id>', type='json', auth='user', methods=['PUT'])
    def update_portal_config(self, config_id, **kw):
        """Mettre à jour la configuration du portail"""
        config = request.env['edu.parent.portal.config'].sudo().browse(config_id)
        if not config.exists():
            return {'success': False, 'error': 'Config not found'}

        vals = kw.get('data', {})
        config.write(vals)
        return {'success': True}

