# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EduNotificationType(models.Model):
    _name = 'edu.notification.type'
    _description = 'Type de notification'
    
    name = fields.Char('Nom', required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')
    
    # Configuration des canaux
    use_email = fields.Boolean('Utiliser Email', default=True)
    use_sms = fields.Boolean('Utiliser SMS', default=False)
    use_push = fields.Boolean('Utiliser Push', default=False)
    use_chat = fields.Boolean('Utiliser Chat', default=False)
    
    # Templates
    email_template_id = fields.Many2one('mail.template', 'Template Email')
    sms_template_id = fields.Many2one('edu.message.template', 'Template SMS')
    push_template_id = fields.Many2one('edu.message.template', 'Template Push')
    
    # Configuration
    priority = fields.Selection([
        ('low', 'Bas'),
        ('normal', 'Normal'),
        ('high', 'Élevé'),
        ('urgent', 'Urgent')
    ], string='Priorité', default='normal')
    
    auto_send = fields.Boolean('Envoi automatique', default=False)
    active = fields.Boolean('Actif', default=True)
    
    # Groupes autorisés
    group_ids = fields.Many2many('res.groups', 'notification_type_group_rel',
                                'type_id', 'group_id', 
                                string='Groupes autorisés')
    
    @api.model
    def get_notification_channels(self, notification_type_code):
        """Obtenir les canaux activés pour un type de notification"""
        notification_type = self.search([('code', '=', notification_type_code)], limit=1)
        if not notification_type:
            return []
        
        channels = []
        if notification_type.use_email:
            channels.append('email')
        if notification_type.use_sms:
            channels.append('sms')
        if notification_type.use_push:
            channels.append('push')
        if notification_type.use_chat:
            channels.append('chat')
            
        return channels
