# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CreateCampaignWizard(models.TransientModel):
    """Assistant de création de campagne"""
    _name = 'edu.create.campaign.wizard'
    _description = 'Assistant de création de campagne'

    # Informations de base
    name = fields.Char(
        string='Nom de la campagne',
        required=True,
        help="Nom de la campagne de communication"
    )
    
    description = fields.Text(
        string='Description',
        help="Description de la campagne"
    )
    
    # Configuration de la campagne
    campaign_type = fields.Selection([
        ('announcement', 'Annonce générale'),
        ('event', 'Événement'),
        ('reminder', 'Rappel'),
        ('emergency', 'Urgence'),
        ('newsletter', 'Newsletter'),
        ('marketing', 'Marketing')
    ], string='Type de campagne', required=True, default='announcement')
    
    # Messages de la campagne
    message_ids = fields.One2many(
        'edu.campaign.message.line',
        'wizard_id',
        string='Messages'
    )
    
    # Programmation
    start_date = fields.Datetime(
        string='Date de début',
        required=True,
        default=fields.Datetime.now,
        help="Date de début de la campagne"
    )
    
    end_date = fields.Datetime(
        string='Date de fin',
        help="Date de fin de la campagne"
    )
    
    # Options avancées
    auto_send = fields.Boolean(
        string='Envoi automatique',
        default=True,
        help="Envoyer automatiquement les messages selon la programmation"
    )
    
    priority = fields.Selection([
        ('low', 'Basse'),
        ('normal', 'Normale'),
        ('high', 'Haute'),
        ('urgent', 'Urgente')
    ], string='Priorité', default='normal')
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Vérifie la cohérence des dates"""
        for record in self:
            if record.end_date and record.start_date >= record.end_date:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début"))
    
    def action_create_campaign(self):
        """Crée la campagne"""
        self.ensure_one()
        
        if not self.message_ids:
            raise UserError(_("Veuillez ajouter au moins un message à la campagne"))
        
        # Créer la campagne
        campaign_vals = {
            'name': self.name,
            'description': self.description,
            'campaign_type': self.campaign_type,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'auto_send': self.auto_send,
            'priority': self.priority,
            'state': 'draft',
        }
        
        campaign = self.env['edu.campaign'].create(campaign_vals)
        
        # Ajouter les messages à la campagne
        for line in self.message_ids:
            message_vals = {
                'campaign_id': campaign.id,
                'subject': line.subject,
                'body': line.message,
                'message_type': line.message_type,
                'scheduled_date': line.scheduled_date,
                'state': 'draft',
            }
            
            message = self.env['edu.message'].create(message_vals)
            
            # Ajouter les destinataires si spécifiés
            if line.recipient_ids:
                for recipient in line.recipient_ids:
                    self.env['edu.message.recipient'].create({
                        'message_id': message.id,
                        'partner_id': recipient.id,
                        'recipient_type': 'custom',
                    })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Campagne créée'),
            'res_model': 'edu.campaign',
            'res_id': campaign.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_add_message(self):
        """Ajoute un message à la campagne"""
        self.ensure_one()
        
        # Ajouter une ligne de message vide
        self.env['edu.campaign.message.line'].create({
            'wizard_id': self.id,
            'subject': 'Nouveau message',
            'message': '<p>Contenu du message...</p>',
            'message_type': 'email',
            'scheduled_date': self.start_date,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'edu.create.campaign.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class CampaignMessageLine(models.TransientModel):
    """Ligne de message pour la campagne"""
    _name = 'edu.campaign.message.line'
    _description = 'Ligne de message de campagne'

    wizard_id = fields.Many2one(
        'edu.create.campaign.wizard',
        string='Assistant',
        required=True,
        ondelete='cascade'
    )
    
    subject = fields.Char(
        string='Sujet',
        required=True
    )
    
    message = fields.Html(
        string='Message',
        required=True
    )
    
    message_type = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Notification Push'),
        ('all', 'Tous les canaux')
    ], string='Type', default='email', required=True)
    
    scheduled_date = fields.Datetime(
        string='Date programmée',
        required=True
    )
    
    recipient_ids = fields.Many2many(
        'res.partner',
        string='Destinataires spécifiques',
        help="Laisser vide pour utiliser les destinataires par défaut"
    ) 