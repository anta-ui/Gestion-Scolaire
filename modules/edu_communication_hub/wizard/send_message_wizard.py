# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SendMessageWizard(models.TransientModel):
    """Assistant d'envoi de messages"""
    _name = 'edu.send.message.wizard'
    _description = 'Assistant d\'envoi de messages'

    # Configuration du message
    subject = fields.Char(
        string='Sujet',
        required=True,
        help="Sujet du message"
    )
    
    message = fields.Html(
        string='Message',
        required=True,
        help="Contenu du message"
    )
    
    message_type = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Notification Push'),
        ('all', 'Tous les canaux')
    ], string='Type de message', default='email', required=True)
    
    # Destinataires
    recipient_type = fields.Selection([
        ('students', 'Étudiants'),
        ('parents', 'Parents'),
        ('faculty', 'Personnel enseignant'),
        ('all', 'Tous'),
        ('custom', 'Personnalisé')
    ], string='Type de destinataires', default='students', required=True)
    
    student_ids = fields.Many2many(
        'op.student',
        string='Étudiants',
        help="Sélectionner les étudiants"
    )
    
    parent_ids = fields.Many2many(
        'op.parent',
        string='Parents',
        help="Sélectionner les parents"
    )
    
    faculty_ids = fields.Many2many(
        'op.faculty',
        string='Personnel enseignant',
        help="Sélectionner le personnel enseignant"
    )
    
    # Options d'envoi
    send_immediately = fields.Boolean(
        string='Envoyer immédiatement',
        default=True,
        help="Envoyer le message immédiatement"
    )
    
    scheduled_date = fields.Datetime(
        string='Date programmée',
        help="Date et heure d'envoi programmé"
    )
    
    # Template
    template_id = fields.Many2one(
        'edu.message.template',
        string='Modèle de message',
        help="Utiliser un modèle prédéfini"
    )
    
    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Charge le contenu du template"""
        if self.template_id:
            self.subject = self.template_id.subject
            self.message = self.template_id.body
            self.message_type = self.template_id.message_type
    
    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        """Vérifie que la date programmée est dans le futur"""
        for record in self:
            if not record.send_immediately and record.scheduled_date:
                if record.scheduled_date <= fields.Datetime.now():
                    raise ValidationError(_("La date programmée doit être dans le futur"))
    
    def action_send_message(self):
        """Envoie le message"""
        self.ensure_one()
        
        # Validation
        if not self.send_immediately and not self.scheduled_date:
            raise UserError(_("Veuillez spécifier une date d'envoi ou cocher 'Envoyer immédiatement'"))
        
        # Récupérer les destinataires
        recipients = self._get_recipients()
        
        if not recipients:
            raise UserError(_("Aucun destinataire sélectionné"))
        
        # Créer le message
        message_vals = {
            'subject': self.subject,
            'body': self.message,
            'message_type': self.message_type,
            'state': 'draft' if not self.send_immediately else 'sending',
            'scheduled_date': self.scheduled_date if not self.send_immediately else False,
        }
        
        message = self.env['edu.message'].create(message_vals)
        
        # Ajouter les destinataires
        for recipient in recipients:
            self.env['edu.message.recipient'].create({
                'message_id': message.id,
                'partner_id': recipient.partner_id.id if hasattr(recipient, 'partner_id') else recipient.id,
                'recipient_type': self._get_recipient_type(recipient),
            })
        
        # Envoyer immédiatement si demandé
        if self.send_immediately:
            message.action_send()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Message créé'),
            'res_model': 'edu.message',
            'res_id': message.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _get_recipients(self):
        """Récupère la liste des destinataires selon le type sélectionné"""
        recipients = []
        
        if self.recipient_type == 'students':
            recipients = self.env['op.student'].search([])
        elif self.recipient_type == 'parents':
            recipients = self.env['op.parent'].search([])
        elif self.recipient_type == 'faculty':
            recipients = self.env['op.faculty'].search([])
        elif self.recipient_type == 'all':
            recipients = (
                self.env['op.student'].search([]) +
                self.env['op.parent'].search([]) +
                self.env['op.faculty'].search([])
            )
        elif self.recipient_type == 'custom':
            recipients = self.student_ids + self.parent_ids + self.faculty_ids
        
        return recipients
    
    def _get_recipient_type(self, recipient):
        """Détermine le type de destinataire"""
        if hasattr(recipient, '_name'):
            if recipient._name == 'op.student':
                return 'student'
            elif recipient._name == 'op.parent':
                return 'parent'
            elif recipient._name == 'op.faculty':
                return 'faculty'
        return 'other'
    
    def action_preview_message(self):
        """Prévisualise le message"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Aperçu du message'),
            'res_model': 'edu.message.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_subject': self.subject,
                'default_message': self.message,
                'default_message_type': self.message_type,
            }
        } 