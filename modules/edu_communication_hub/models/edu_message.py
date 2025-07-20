# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import html2text
import re
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
        tracking=True,
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
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('chat', 'Message Chat')
    ], string='Type de message', required=True, default='sms')
    
    content = fields.Html(
        string='Contenu HTML',
        help="Contenu du message en HTML (pour emails)"
    )
    
    content_text = fields.Text(
        string='Contenu texte',
        required=True,
        help="Contenu du message en texte brut"
    )
    
    content_sms = fields.Text(
        string='Contenu SMS',
        compute='_compute_content_sms',
        store=True,
        help="Version raccourcie pour SMS"
    )
    
    # Destinataires
    recipient_type = fields.Selection([
        ('individual', 'Individuel'),
        ('group', 'Groupe'),
        ('class', 'Classe'),
        ('all_students', 'Tous les élèves'),
        ('all_parents', 'Tous les parents'),
        ('all_faculty', 'Tout le personnel'),
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
    
    student_ids = fields.Many2many(
        'op.student',
        'message_student_rel',
        'message_id',
        'student_id',
        string='Élèves concernés',
        help="Élèves concernés par le message"
    )
    
    standard_ids = fields.Many2many(
        'op.batch',
        'message_batch_rel',
        'message_id',
        'batch_id',
        string='Classes',
        help="Classes concernées"
    )
    
    contact_group_ids = fields.Many2many(
        'edu.contact.group',
        'message_contact_group_rel',
        'message_id',
        'group_id',
        string='Groupes de contacts',
        help="Groupes de contacts"
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
    
    sender_email = fields.Char(
        string='Email expéditeur',
        help="Adresse email expéditrice"
    )
    
    # État et planification
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('scheduled', 'Programmé'),
        ('sending', 'En cours d\'envoi'),
        ('sent', 'Envoyé'),
        ('failed', 'Échec'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    
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
    
    notification_type_id = fields.Many2one(
        'edu.notification.type',
        string='Type de notification',
        help="Type de notification pour la catégorisation"
    )
    
    # Configuration d'envoi
    provider_id = fields.Many2one(
        'edu.communication.provider',
        string='Fournisseur',
        help="Fournisseur de communication utilisé"
    )
    
    template_id = fields.Many2one(
        'edu.message.template',
        string='Modèle',
        help="Modèle de message utilisé"
    )
    
    language = fields.Selection(
        '_get_languages',
        string='Langue',
        default='fr_FR',
        help="Langue du message"
    )
    
    # Options d'envoi
    request_delivery_report = fields.Boolean(
        string='Rapport de livraison',
        default=True,
        help="Demander un rapport de livraison"
    )
    
    request_read_receipt = fields.Boolean(
        string='Accusé de lecture',
        default=False,
        help="Demander un accusé de lecture"
    )
    
    auto_retry = fields.Boolean(
        string='Nouvel essai automatique',
        default=True,
        help="Réessayer automatiquement en cas d'échec"
    )
    
    max_retries = fields.Integer(
        string='Essais maximum',
        default=3,
        help="Nombre maximum de tentatives"
    )
    
    # Pièces jointes (pour emails)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'edu_message_attachment_rel',
        'message_id',
        'attachment_id',
        string='Pièces jointes',
        help="Fichiers joints au message"
    )
    
    # Statistiques de livraison
    total_recipients = fields.Integer(
        string='Total destinataires',
        compute='_compute_delivery_stats',
        store=True,
        help="Nombre total de destinataires"
    )
    
    delivered_count = fields.Integer(
        string='Livrés',
        compute='_compute_delivery_stats',
        store=True,
        help="Nombre de messages livrés"
    )
    
    failed_count = fields.Integer(
        string='Échecs',
        compute='_compute_delivery_stats',
        store=True,
        help="Nombre d'échecs de livraison"
    )
    
    read_count = fields.Integer(
        string='Lus',
        compute='_compute_delivery_stats',
        store=True,
        help="Nombre de messages lus"
    )
    
    delivery_rate = fields.Float(
        string='Taux de livraison (%)',
        compute='_compute_delivery_stats',
        store=True,
        digits=(5, 2),
        help="Pourcentage de livraison"
    )
    
    read_rate = fields.Float(
        string='Taux de lecture (%)',
        compute='_compute_delivery_stats',
        store=True,
        digits=(5, 2),
        help="Pourcentage de lecture"
    )
    
    # Rapport de livraison détaillé
    delivery_report_ids = fields.One2many(
        'edu.message.delivery',
        'message_id',
        string='Rapports de livraison'
    )
    
    # Métadonnées
    campaign_id = fields.Many2one(
        'edu.campaign',
        string='Campagne',
        help="Campagne de communication associée"
    )
    
    parent_message_id = fields.Many2one(
        'edu.message',
        string='Message parent',
        help="Message parent en cas de réponse"
    )
    
    reply_to_message_id = fields.Many2one(
        'edu.message',
        string='Réponse à',
        help="Message auquel celui-ci répond"
    )
    
    # Données techniques
    external_id = fields.Char(
        string='ID externe',
        help="ID du message chez le fournisseur"
    )
    
    cost = fields.Float(
        string='Coût',
        digits=(8, 4),
        help="Coût d'envoi du message"
    )
    
    error_message = fields.Text(
        string='Message d\'erreur',
        help="Détails de l'erreur en cas d'échec"
    )
    
    retry_count = fields.Integer(
        string='Nombre de tentatives',
        default=0,
        help="Nombre de tentatives d'envoi"
    )
    
    # Calculs automatiques
    @api.depends('content')
    def _compute_content_sms(self):
        """Génère la version SMS du contenu"""
        for record in self:
            if record.content:
                # Convertir HTML en texte
                h = html2text.HTML2Text()
                h.ignore_links = True
                h.ignore_images = True
                text = h.handle(record.content)
                
                # Nettoyer et raccourcir
                text = re.sub(r'\s+', ' ', text.strip())
                
                # Limiter à 160 caractères pour SMS
                if len(text) > 160:
                    text = text[:157] + '...'
                
                record.content_sms = text
            else:
                record.content_sms = record.content_text[:160] if record.content_text else ''
    
    @api.depends('delivery_report_ids')
    def _compute_delivery_stats(self):
        """Calcule les statistiques de livraison"""
        for record in self:
            reports = record.delivery_report_ids
            record.total_recipients = len(reports)
            
            if reports:
                record.delivered_count = len(reports.filtered(lambda r: r.delivery_status == 'delivered'))
                record.failed_count = len(reports.filtered(lambda r: r.delivery_status == 'failed'))
                record.read_count = len(reports.filtered(lambda r: r.read_date))
                
                record.delivery_rate = (record.delivered_count / record.total_recipients) * 100
                record.read_rate = (record.read_count / record.total_recipients) * 100 if record.total_recipients > 0 else 0
            else:
                record.delivered_count = 0
                record.failed_count = 0
                record.read_count = 0
                record.delivery_rate = 0.0
                record.read_rate = 0.0
    
    @api.model
    def _get_languages(self):
        """Retourne les langues disponibles"""
        return self.env['res.lang'].get_installed()
    
    # Méthodes de génération
    @api.model
    def _generate_reference(self):
        """Génère une référence unique"""
        return self.env['ir.sequence'].next_by_code('edu.message') or '/'
    
    # Contraintes
    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        """Vérifie que la date programmée est dans le futur"""
        for record in self:
            if record.scheduled_date and record.scheduled_date <= fields.Datetime.now():
                raise ValidationError(_("La date programmée doit être dans le futur"))
    
    @api.constrains('content_text')
    def _check_content_length(self):
        """Vérifie la longueur du contenu selon le type"""
        for record in self:
            if record.message_type == 'sms' and record.content_text:
                if len(record.content_text) > 1600:  # 10 SMS max
                    raise ValidationError(_("Le contenu SMS ne peut pas dépasser 1600 caractères"))
    
    # Actions du workflow
    def action_send_now(self):
        """Envoie le message immédiatement"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Seuls les messages en brouillon peuvent être envoyés"))
            
            record._prepare_recipients()
            record._send_message()
    
    def action_schedule(self):
        """Programme le message pour envoi différé"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Seuls les messages en brouillon peuvent être programmés"))
            
            if not record.scheduled_date:
                raise UserError(_("Veuillez spécifier une date d'envoi"))
            
            record.state = 'scheduled'
            record._prepare_recipients()
    
    def action_cancel(self):
        """Annule le message"""
        for record in self:
            if record.state in ['draft', 'scheduled']:
                record.state = 'cancelled'
            else:
                raise UserError(_("Impossible d'annuler un message déjà envoyé"))
    
    def action_retry(self):
        """Retente l'envoi du message"""
        for record in self:
            if record.state == 'failed':
                record.retry_count += 1
                if record.retry_count <= record.max_retries:
                    record._send_message()
                else:
                    raise UserError(_("Nombre maximum de tentatives atteint"))
    
    def action_duplicate(self):
        """Duplique le message"""
        self.ensure_one()
        new_message = self.copy({
            'subject': f"{self.subject} (Copie)",
            'state': 'draft',
            'sent_date': False,
            'reference': self._generate_reference(),
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Message dupliqué'),
            'res_model': 'edu.message',
            'res_id': new_message.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    # Méthodes d'envoi
    def _prepare_recipients(self):
        """Prépare la liste des destinataires"""
        self.ensure_one()
        
        recipients = self.env['res.partner']
        
        # Selon le type de destinataire
        if self.recipient_type == 'individual':
            recipients = self.recipient_ids
        
        elif self.recipient_type == 'group':
            for group in self.contact_group_ids:
                recipients |= group.partner_ids
        
        elif self.recipient_type == 'class':
            for batch in self.standard_ids:
                # Récupérer les élèves de la classe
                students = self.env['op.student'].search([
                    ('batch_id', '=', batch.id)
                ])
                # Ajouter les parents
                for student in students:
                    if hasattr(student, 'parent_ids'):
                        recipients |= student.parent_ids
                    elif hasattr(student, 'partner_id'):
                        recipients |= student.partner_id
        
        elif self.recipient_type == 'all_students':
            students = self.env['op.student'].search([('active', '=', True)])
            for student in students:
                recipients |= student.parent_ids
        
        elif self.recipient_type == 'all_parents':
            students = self.env['op.student'].search([('active', '=', True)])
            for student in students:
                recipients |= student.parent_ids
        
        elif self.recipient_type == 'all_faculty':
            faculty = self.env['op.faculty'].search([('active', '=', True)])
            recipients = faculty.mapped('partner_id')
        
        # Créer les rapports de livraison
        self._create_delivery_reports(recipients)
    
    def _create_delivery_reports(self, recipients):
        """Crée les rapports de livraison pour chaque destinataire"""
        self.ensure_one()
        
        # Supprimer les anciens rapports
        self.delivery_report_ids.unlink()
        
        # Créer un rapport par destinataire
        for recipient in recipients:
            # Vérifier le canal de communication préféré
            channel = self._get_preferred_channel(recipient)
            
            if channel:
                self.env['edu.message.delivery'].create({
                    'message_id': self.id,
                    'recipient_id': recipient.id,
                    'channel': channel,
                    'delivery_status': 'pending',
                })
    
    def _get_preferred_channel(self, recipient):
        """Détermine le canal de communication préféré pour un destinataire"""
        # Logique pour déterminer le meilleur canal selon le type de message
        if self.message_type == 'sms':
            return 'sms' if recipient.mobile else None
        elif self.message_type == 'email':
            return 'email' if recipient.email else None
        elif self.message_type == 'push':
            return 'push'  # Toujours disponible
        
        return None
    
    def _send_message(self):
        """Envoie effectivement le message"""
        self.ensure_one()
        
        try:
            self.state = 'sending'
            
            # Vérifier les limites quotidiennes
            config = self.env['edu.communication.config'].get_active_config()
            if not config.check_daily_limits(self.message_type):
                raise UserError(_("Limite quotidienne de messages atteinte"))
            
            # Vérifier les heures d'envoi
            if not config.is_sending_allowed():
                raise UserError(_("Envoi de messages non autorisé à cette heure"))
            
            # Envoyer selon le type
            if self.message_type == 'sms':
                self._send_sms()
            elif self.message_type == 'email':
                self._send_email()
            elif self.message_type == 'push':
                self._send_push_notification()
            
            self.state = 'sent'
            self.sent_date = fields.Datetime.now()
            
        except Exception as e:
            _logger.error(f"Erreur envoi message {self.reference}: {e}")
            self.state = 'failed'
            self.error_message = str(e)
    
    def _send_sms(self):
        """Envoie les SMS"""
        # Récupérer le provider SMS
        provider = self.provider_id or self.env['edu.communication.provider'].search([
            ('provider_type', '=', 'sms'),
            ('active', '=', True)
        ], limit=1)
        
        if not provider:
            raise UserError(_("Aucun fournisseur SMS configuré"))
        
        # Envoyer à chaque destinataire
        for delivery in self.delivery_report_ids.filtered(lambda d: d.channel == 'sms'):
            try:
                provider._send_sms(
                    delivery.recipient_id.mobile,
                    self.content_sms or self.content_text,
                    delivery
                )
            except Exception as e:
                delivery.write({
                    'delivery_status': 'failed',
                    'error_message': str(e)
                })
    
    def _send_email(self):
        """Envoie les emails"""
        # Utiliser le système d'email d'Odoo
        mail_values = {
            'subject': self.subject,
            'body_html': self.content,
            'email_from': self.sender_email or self.env.user.email,
            'reply_to': self.sender_email or self.env.user.email,
        }
        
        for delivery in self.delivery_report_ids.filtered(lambda d: d.channel == 'email'):
            try:
                mail_values['email_to'] = delivery.recipient_id.email
                mail_values['recipient_ids'] = [(4, delivery.recipient_id.id)]
                
                mail = self.env['mail.mail'].create(mail_values)
                mail.send()
                
                delivery.write({
                    'delivery_status': 'delivered',
                    'sent_date': fields.Datetime.now(),
                    'external_id': str(mail.id)
                })
                
            except Exception as e:
                delivery.write({
                    'delivery_status': 'failed',
                    'error_message': str(e)
                })
    
    def _send_push_notification(self):
        """Envoie les notifications push"""
        # À implémenter avec Firebase
        for delivery in self.delivery_report_ids.filtered(lambda d: d.channel == 'push'):
            try:
                # Logique d'envoi push avec Firebase
                delivery.write({
                    'delivery_status': 'delivered',
                    'sent_date': fields.Datetime.now()
                })
            except Exception as e:
                delivery.write({
                    'delivery_status': 'failed',
                    'error_message': str(e)
                })
    
    # Méthodes automatiques
    @api.model
    def _cron_send_scheduled_messages(self):
        """Envoie les messages programmés"""
        now = fields.Datetime.now()
        scheduled_messages = self.search([
            ('state', '=', 'scheduled'),
            ('scheduled_date', '<=', now)
        ])
        
        for message in scheduled_messages:
            try:
                message._send_message()
            except Exception as e:
                _logger.error(f"Erreur envoi message programmé {message.reference}: {e}")
    
    @api.model
    def _cron_retry_failed_messages(self):
        """Retente l'envoi des messages échoués"""
        failed_messages = self.search([
            ('state', '=', 'failed'),
            ('auto_retry', '=', True),
            ('retry_count', '<', 'max_retries')
        ])
        
        for message in failed_messages:
            try:
                message.action_retry()
            except Exception as e:
                _logger.error(f"Erreur retry message {message.reference}: {e}")


class EduMessageDelivery(models.Model):
    """Rapport de livraison individuel"""
    _name = 'edu.message.delivery'
    _description = 'Rapport de livraison'
    _order = 'sent_date desc'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Nom',
        compute='_compute_display_name',
        store=True
    )
    
    message_id = fields.Many2one(
        'edu.message',
        string='Message',
        required=True,
        ondelete='cascade'
    )
    
    recipient_id = fields.Many2one(
        'res.partner',
        string='Destinataire',
        required=True
    )
    
    channel = fields.Selection([
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram')
    ], string='Canal', required=True)
    
    delivery_status = fields.Selection([
        ('pending', 'En attente'),
        ('sent', 'Envoyé'),
        ('delivered', 'Livré'),
        ('failed', 'Échec'),
        ('bounced', 'Rejeté'),
        ('unsubscribed', 'Désabonné')
    ], string='Statut', default='pending')
    
    sent_date = fields.Datetime(
        string='Date d\'envoi'
    )
    
    delivered_date = fields.Datetime(
        string='Date de livraison'
    )
    
    read_date = fields.Datetime(
        string='Date de lecture'
    )
    
    external_id = fields.Char(
        string='ID externe',
        help="ID chez le fournisseur"
    )
    
    error_message = fields.Text(
        string='Message d\'erreur'
    )
    
    cost = fields.Float(
        string='Coût',
        digits=(8, 4)
    )
    
    @api.depends('message_id', 'recipient_id', 'channel')
    def _compute_display_name(self):
        """Calcule le nom d'affichage"""
        for record in self:
            if record.message_id and record.recipient_id:
                record.display_name = f"{record.message_id.subject} → {record.recipient_id.name} ({record.channel})"
            else:
                record.display_name = "Rapport de livraison"
