# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class EduMessage(models.Model):
    """Messages de communication (SMS, Email, Push)"""
    _name = 'edu.message'
    _description = 'Message de communication'
    _order = 'create_date desc'
    _rec_name = 'subject'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Identification
    subject = fields.Char(
        string='Sujet',
        required=True,
        help="Sujet du message"
    )
    
    reference = fields.Char(
        string='Référence',
        required=True,
        default=lambda self: self._generate_reference(),
        help="Référence unique du message"
    )
    
    # Type et contenu
    message_type = fields.Selection([
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Notification Push'),
        ('info', 'Information'),
        ('alert', 'Alerte'), 
        ('urgent', 'Urgent'),
        ('notification', 'Notification'),
        ('reminder', 'Rappel')
    ], string='Type de message', required=True, default='info')
    
    content = fields.Html(
        string='Contenu HTML',
        help="Contenu du message en HTML (pour emails)"
    )
    
    content_text = fields.Text(
        string='Contenu texte',
        required=True,
        help="Contenu du message en texte brut"
    )
    
    # Destinataires (simplifié)
    recipient_type = fields.Selection([
        ('individual', 'Individuel'),
        ('group', 'Groupe'),
        ('all', 'Tous'),
        ('custom', 'Sélection personnalisée')
    ], string='Type de destinataire', required=True, default='individual')
    
    recipient_ids = fields.Many2many(
        'res.partner',
        'message_recipient_rel',
        'message_id',
        'partner_id',
        string='Destinataires',
        help="Liste des destinataires"
    )
    
    # Relations
    campaign_id = fields.Many2one(
        'edu.campaign',
        string='Campagne',
        help="Campagne associée à ce message"
    )
    
    # Expéditeur
    sender_id = fields.Many2one(
        'res.users',
        string='Expéditeur',
        required=True,
        default=lambda self: self.env.user,
        help="Utilisateur expéditeur"
    )
    
    sender_name = fields.Char(
        string='Nom expéditeur',
        help="Nom affiché comme expéditeur"
    )
    
    # État et planification
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('scheduled', 'Programmé'),
        ('sending', 'En cours d\'envoi'),
        ('sent', 'Envoyé'),
        ('failed', 'Échec'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft')
    
    scheduled_date = fields.Datetime(
        string='Date programmée',
        help="Date et heure d'envoi programmé"
    )
    
    sent_date = fields.Datetime(
        string='Date d\'envoi',
        readonly=True,
        help="Date et heure d'envoi effectif"
    )
    
    # Priorité et importance
    priority = fields.Selection([
        ('low', 'Faible'),
        ('normal', 'Normal'),
        ('high', 'Élevé'),
        ('urgent', 'Urgent')
    ], string='Priorité', default='normal')
    
    # Options d'envoi
    request_delivery_report = fields.Boolean(
        string='Rapport de livraison',
        default=True,
        help="Demander un rapport de livraison"
    )
    
    # Statistiques simplifiées
    total_recipients = fields.Integer(
        string='Total destinataires',
        compute='_compute_delivery_stats',
        help="Nombre total de destinataires"
    )
    
    delivered_count = fields.Integer(
        string='Livrés',
        default=0,
        help="Nombre de messages livrés"
    )
    
    failed_count = fields.Integer(
        string='Échecs',
        default=0,
        help="Nombre d'échecs de livraison"
    )
    
    # Données techniques
    error_message = fields.Text(
        string='Message d\'erreur',
        help="Détails de l'erreur en cas d'échec"
    )
    
    @api.depends('recipient_ids')
    def _compute_delivery_stats(self):
        """Calcul des statistiques de livraison"""
        for record in self:
            record.total_recipients = len(record.recipient_ids)
    
    @api.model
    def _generate_reference(self):
        """Génère une référence unique"""
        return self.env['ir.sequence'].next_by_code('edu.message') or 'EDU-MSG-' + str(fields.Datetime.now().timestamp())
    
    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        """Vérifier que la date programmée est dans le futur"""
        for record in self:
            if record.scheduled_date and record.scheduled_date < fields.Datetime.now():
                raise ValidationError("La date programmée doit être dans le futur.")
    
    def action_send_now(self):
        """Envoyer le message immédiatement"""
        self.ensure_one()
        if self.state == 'draft':
            self.write({
                'state': 'sent',
                'sent_date': fields.Datetime.now()
            })
        return True
    
    def action_schedule(self):
        """Programmer l'envoi du message"""
        self.ensure_one()
        if not self.scheduled_date:
            raise UserError("Veuillez définir une date programmée.")
        self.write({'state': 'scheduled'})
        return True
    
    def action_cancel(self):
        """Annuler le message"""
        self.ensure_one()
        self.write({'state': 'cancelled'})
        return True

    @api.model
    def _cron_send_scheduled_messages(self):
        """Méthode cron pour envoyer les messages programmés"""
        _logger.info("Vérification des messages programmés...")
        
        # Rechercher les messages programmés dont l'heure d'envoi est arrivée
        scheduled_messages = self.search([
            ('state', '=', 'scheduled'),
            ('scheduled_date', '<=', fields.Datetime.now())
        ])
        
        for message in scheduled_messages:
            try:
                message.write({
                    'state': 'sent',
                    'sent_date': fields.Datetime.now()
                })
                _logger.info(f"Message {message.reference} envoyé avec succès")
            except Exception as e:
                message.write({
                    'state': 'failed',
                    'error_message': str(e)
                })
                _logger.error(f"Erreur lors de l'envoi du message {message.reference}: {e}")
        
        _logger.info(f"Traitement terminé : {len(scheduled_messages)} messages traités")
        return True
