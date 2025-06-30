# -*- coding: utf-8 -*-

from odoo import models, fields


class EduChatMessage(models.Model):
    _name = 'edu.chat.message'
    _description = 'Message de chat'
    _order = 'create_date asc'
    
    chat_id = fields.Many2one('edu.chat', 'Chat', required=True, ondelete='cascade')
    sender_id = fields.Many2one('res.partner', 'Expéditeur', required=True)
    
    message = fields.Text('Message', required=True)
    message_type = fields.Selection([
        ('text', 'Texte'),
        ('file', 'Fichier'),
        ('image', 'Image'),
    ], string='Type', default='text')
    
    attachment_id = fields.Many2one('ir.attachment', 'Pièce jointe')
    
    is_read = fields.Boolean('Lu', default=False)
    read_date = fields.Datetime('Date de lecture')
