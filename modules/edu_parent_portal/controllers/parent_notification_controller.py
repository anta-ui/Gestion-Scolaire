# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class ParentNotificationController(http.Controller):

    @http.route('/api/notifications/send', type='json', auth='user', methods=['POST'])
    def send_notification(self, **kw):
        """Créer et envoyer immédiatement une notification"""
        vals = kw.get('data', {})
        vals['sender_id'] = request.env.user.id
        notification = request.env['edu.parent.notification'].sudo().create(vals)
        notification.action_send()
        return {'success': True, 'notification_id': notification.id, 'state': notification.state}

    @http.route('/api/notifications', type='json', auth='user', methods=['POST'])
    def create_notification(self, **kw):
        """Créer une notification en brouillon"""
        vals = kw.get('data', {})
        vals['sender_id'] = request.env.user.id
        notification = request.env['edu.parent.notification'].sudo().create(vals)
        return {'success': True, 'notification_id': notification.id}

    @http.route('/api/notifications/<int:notification_id>/mark_read', type='json', auth='user', methods=['POST'])
    def mark_notification_read(self, notification_id):
        """Marquer une notification comme lue"""
        notification = request.env['edu.parent.notification'].sudo().browse(notification_id)
        if not notification.exists():
            return {'success': False, 'error': 'Notification not found'}

        notification.action_mark_read()
        return {'success': True, 'read_date': notification.read_date}

    @http.route('/api/notifications/<int:notification_id>/archive', type='json', auth='user', methods=['POST'])
    def archive_notification(self, notification_id):
        """Archiver une notification"""
        notification = request.env['edu.parent.notification'].sudo().browse(notification_id)
        if not notification.exists():
            return {'success': False, 'error': 'Notification not found'}

        notification.action_archive()
        return {'success': True, 'state': notification.state}

    @http.route('/api/notifications/list', type='json', auth='user', methods=['POST'])
    def list_notifications(self, **kw):
        """Lister les notifications reçues par l'utilisateur"""
        domain = [
            ('recipient_ids', 'in', [request.env.user.id]),
            ('state', 'in', ['sent', 'read'])
        ]
        notifications = request.env['edu.parent.notification'].sudo().search(domain, limit=kw.get('limit', 20))
        
        result = [{
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'type': notif.notification_type,
            'category': notif.category,
            'state': notif.state,
            'send_date': notif.send_date,
        } for notif in notifications]

        return {'success': True, 'notifications': result}

    @http.route('/api/notifications/<int:notification_id>', type='json', auth='user', methods=['GET'])
    def get_notification_detail(self, notification_id):
        """Récupérer les détails d'une notification"""
        notification = request.env['edu.parent.notification'].sudo().browse(notification_id)
        if not notification.exists():
            return {'success': False, 'error': 'Notification not found'}

        return {
            'success': True,
            'notification': {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'category': notification.category,
                'state': notification.state,
                'send_date': notification.send_date,
                'attachments': [
                    {
                        'id': att.id,
                        'name': att.name,
                        'url': f'/web/content/{att.id}?download=true'
                    } for att in notification.attachment_ids
                ],
            }
        }
