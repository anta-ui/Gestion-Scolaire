# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class CommunicationAPIController(http.Controller):
    """Contrôleur API pour les intégrations externes"""

    @http.route('/api/communication/webhook', type='json', auth='none', csrf=False, methods=['POST'])
    def webhook_handler(self, **kw):
        """Gestionnaire de webhook pour les services externes"""
        try:
            data = request.jsonrequest
            provider = data.get('provider', '')
            event_type = data.get('event_type', '')
            
            # Traiter les différents types d'événements
            if provider == 'twilio' and event_type == 'message_status':
                return self._handle_twilio_status(data)
            elif provider == 'sendgrid' and event_type == 'delivered':
                return self._handle_sendgrid_status(data)
            
            return {'status': 'success', 'message': 'Webhook traité'}
        except Exception as e:
            _logger.error(f"Erreur webhook: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def _handle_twilio_status(self, data):
        """Traiter les statuts Twilio"""
        message_sid = data.get('MessageSid', '')
        status = data.get('MessageStatus', '')
        
        if message_sid:
            messages = request.env['edu.message'].sudo().search([
                ('external_id', '=', message_sid)
            ])
            if messages:
                messages.write({'status': status})
        
        return {'status': 'success'}

    def _handle_sendgrid_status(self, data):
        """Traiter les statuts SendGrid"""
        email_id = data.get('sg_message_id', '')
        status = data.get('event', '')
        
        if email_id:
            messages = request.env['edu.message'].sudo().search([
                ('external_id', '=', email_id)
            ])
            if messages:
                messages.write({'status': status})
        
        return {'status': 'success'}

    @http.route('/api/communication/send', type='json', auth='user', methods=['POST'])
    def api_send_message(self, **kw):
        """API pour envoyer des messages"""
        try:
            data = request.jsonrequest
            
            message_vals = {
                'subject': data.get('subject', ''),
                'body': data.get('body', ''),
                'message_type': data.get('type', 'email'),
                'recipient_ids': [(6, 0, data.get('recipient_ids', []))],
            }
            
            message = request.env['edu.message'].create(message_vals)
            message.send_message()
            
            return {
                'status': 'success', 
                'message_id': message.id,
                'message': 'Message envoyé avec succès'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
