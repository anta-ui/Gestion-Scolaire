# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class NotificationPreferenceController(http.Controller):

    @http.route('/api/notification/preferences', type='json', auth='user', methods=['POST'])
    def create_notification_preference(self, **kw):
        """Créer une nouvelle préférence de notification"""
        values = kw.get('params', {})
        preference = request.env['edu.notification.preference'].create(values)
        return {'id': preference.id, 'message': 'Préférence créée avec succès'}

    @http.route('/api/notification/preferences/<int:preference_id>', type='json', auth='user', methods=['GET'])
    def get_notification_preference(self, preference_id):
        """Obtenir une préférence de notification spécifique"""
        preference = request.env['edu.notification.preference'].browse(preference_id)
        if not preference.exists():
            return {'error': 'Préférence non trouvée'}
        
        return {
            'id': preference.id,
            'name': preference.name,
            'notification_type': preference.notification_type,
            'channels': preference.get_notification_channels(),
            'frequency': preference.frequency,
            'active': preference.active,
        }

    @http.route('/api/notification/preferences', type='json', auth='user', methods=['GET'])
    def list_notification_preferences(self, **kw):
        """Lister les préférences de notification de l'utilisateur connecté"""
        user_id = request.env.user.id
        preferences = request.env['edu.notification.preference'].search([('user_id', '=', user_id)])
        
        return [{
            'id': pref.id,
            'name': pref.name,
            'notification_type': pref.notification_type,
            'channels': pref.get_notification_channels(),
            'frequency': pref.frequency,
            'active': pref.active,
        } for pref in preferences]

    @http.route('/api/notification/preferences/<int:preference_id>', type='json', auth='user', methods=['PUT'])
    def update_notification_preference(self, preference_id, **kw):
        """Mettre à jour une préférence existante"""
        values = kw.get('params', {})
        preference = request.env['edu.notification.preference'].browse(preference_id)
        if not preference.exists():
            return {'error': 'Préférence non trouvée'}
        
        preference.write(values)
        return {'message': 'Préférence mise à jour avec succès'}

    @http.route('/api/notification/preferences/<int:preference_id>', type='json', auth='user', methods=['DELETE'])
    def delete_notification_preference(self, preference_id):
        """Supprimer une préférence"""
        preference = request.env['edu.notification.preference'].browse(preference_id)
        if not preference.exists():
            return {'error': 'Préférence non trouvée'}
        
        preference.unlink()
        return {'message': 'Préférence supprimée avec succès'}
