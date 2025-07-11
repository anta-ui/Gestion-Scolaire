# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.tools.translate import _
import json


class CommunicationController(http.Controller):
    """Contrôleur principal pour le hub de communication"""

    @http.route('/communication/dashboard', type='http', auth='user', website=True)
    def communication_dashboard(self, **kw):
        """Tableau de bord de communication"""
        return request.render('edu_communication_hub.communication_dashboard_template')

    @http.route('/communication/send_message', type='json', auth='user', methods=['POST'])
    def send_message(self, **kw):
        """Envoyer un message via l'interface web"""
        try:
            message_data = {
                'recipient_ids': kw.get('recipient_ids', []),
                'subject': kw.get('subject', ''),
                'body': kw.get('body', ''),
                'message_type': kw.get('message_type', 'email'),
            }
            
            # Créer et envoyer le message
            message = request.env['edu.message'].create(message_data)
            message.send_message()
            
            return {'status': 'success', 'message': _('Message envoyé avec succès')}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/communication/messages', type='json', auth='user')
    def get_messages(self, **kw):
        """Récupérer la liste des messages"""
        try:
            messages = request.env['edu.message'].search([], limit=50)
            message_data = []
            
            for message in messages:
                message_data.append({
                    'id': message.id,
                    'subject': message.subject,
                    'body': message.body,
                    'date': message.create_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'sender': message.sender_id.name,
                    'status': message.status,
                })
            
            return {'status': 'success', 'messages': message_data}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
