# -*- coding: utf-8 -*-

from odoo import models, fields


class EduChat(models.Model):
    _name = 'edu.chat'
    _description = 'Chat éducatif'
    _order = 'create_date desc'
    
    name = fields.Char('Nom du chat', required=True)
    description = fields.Text('Description')
    
    participant_ids = fields.Many2many('res.partner', 'chat_participant_rel',
                                     'chat_id', 'partner_id', 
                                     string='Participants')
    
    message_ids = fields.One2many('edu.chat.message', 'chat_id', 'Messages')
    
    is_active = fields.Boolean('Actif', default=True)
    is_group = fields.Boolean('Chat de groupe', default=False)
