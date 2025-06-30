# -*- coding: utf-8 -*-

from odoo import models, fields


class EduNotification(models.Model):
    _name = 'edu.notification'
    _description = 'Notification éducative'
    _order = 'create_date desc'
    
    name = fields.Char('Titre', required=True)
    message = fields.Text('Message', required=True)
    notification_type_id = fields.Many2one('edu.notification.type', 'Type')
    
    recipient_id = fields.Many2one('res.partner', 'Destinataire', required=True)
    sender_id = fields.Many2one('res.users', 'Expéditeur', default=lambda self: self.env.user)
    
    is_read = fields.Boolean('Lu', default=False)
    read_date = fields.Datetime('Date de lecture')
    
    priority = fields.Selection([
        ('low', 'Bas'),
        ('normal', 'Normal'),
        ('high', 'Élevé'),
        ('urgent', 'Urgent')
    ], string='Priorité', default='normal')
    
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        self.write({
            'is_read': True,
            'read_date': fields.Datetime.now()
        })
