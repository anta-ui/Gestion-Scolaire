# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class EduCommunicationConfig(models.Model):
    """Configuration globale du système de communication"""
    _name = 'edu.communication.config'
    _description = 'Configuration Communication'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom de la configuration',
        required=True,
        help="Nom de la configuration"
    )
    
    active = fields.Boolean(
        string='Configuration active',
        default=True,
        help="Configuration actuellement utilisée"
    )
    
    # Configuration générale
    school_name = fields.Char(
        string='Nom de l\'établissement',
        required=True,
        help="Nom affiché dans les communications"
    )
    
    school_logo = fields.Binary(
        string='Logo',
        help="Logo pour les communications"
    )
    
    default_language = fields.Selection(
        '_get_languages',
        string='Langue par défaut',
        default='fr_FR',
        help="Langue par défaut des communications"
    )
    
    timezone = fields.Selection(
        '_get_timezone_list',
        string='Fuseau horaire',
        default='Africa/Dakar',
        help="Fuseau horaire pour la programmation"
    )
    
    # Configuration SMS
    enable_sms = fields.Boolean(
        string='Activer SMS',
        default=True,
        help="Activer l'envoi de SMS"
    )
    
    default_sms_provider = fields.Selection([
        ('twilio', 'Twilio'),
        ('aws_sns', 'AWS SNS'),
        ('infobip', 'Infobip'),
        ('orange', 'Orange SMS'),
        ('custom', 'Personnalisé')
    ], string='Fournisseur SMS', default='twilio')
    
    sms_sender_name = fields.Char(
        string='Nom expéditeur SMS',
        size=11,
        help="Nom affiché comme expéditeur (max 11 caractères)"
    )
    
    max_sms_length = fields.Integer(
        string='Longueur max SMS',
        default=160,
        help="Longueur maximale d'un SMS"
    )
    
    sms_rate_limit = fields.Integer(
        string='Limite SMS/heure',
        default=100,
        help="Nombre maximum de SMS par heure"
    )
    
    # Configuration Email
    enable_email = fields.Boolean(
        string='Activer Email',
        default=True,
        help="Activer l'envoi d'emails"
    )
    
    default_email_provider = fields.Selection([
        ('sendgrid', 'SendGrid'),
        ('mailgun', 'Mailgun'),
        ('amazon_ses', 'Amazon SES'),
        ('smtp', 'SMTP personnalisé'),
        ('odoo', 'Serveur Odoo')
    ], string='Fournisseur Email', default='sendgrid')
    
    email_from_name = fields.Char(
        string='Nom expéditeur Email',
        help="Nom affiché comme expéditeur des emails"
    )
    
    email_from_address = fields.Char(
        string='Adresse expéditeur',
        help="Adresse email expéditrice"
    )
    
    email_reply_to = fields.Char(
        string='Répondre à',
        help="Adresse de réponse par défaut"
    )
    
    # Configuration Push Notifications
    enable_push_notifications = fields.Boolean(
        string='Notifications Push',
        default=True,
        help="Activer les notifications push"
    )
    
    firebase_project_id = fields.Char(
        string='Firebase Project ID',
        help="ID du projet Firebase"
    )
    
    firebase_server_key = fields.Text(
        string='Clé serveur Firebase',
        help="Clé serveur Firebase pour les notifications push"
    )
    
    # Configuration Chat
    enable_chat = fields.Boolean(
        string='Activer Chat',
        default=True,
        help="Activer le système de chat"
    )
    
    chat_auto_assign = fields.Boolean(
        string='Attribution automatique',
        default=True,
        help="Attribuer automatiquement les chats aux enseignants"
    )
    
    chat_business_hours_only = fields.Boolean(
        string='Heures ouvrables seulement',
        default=False,
        help="Limiter le chat aux heures ouvrables"
    )
    
    chat_max_file_size = fields.Float(
        string='Taille max fichier (MB)',
        default=10.0,
        help="Taille maximale des fichiers en chat"
    )
    
    # Automatisation
    auto_send_attendance_notifications = fields.Boolean(
        string='Notifications présence auto',
        default=True,
        help="Envoyer automatiquement les notifications de présence"
    )
    
    auto_send_grade_notifications = fields.Boolean(
        string='Notifications notes auto',
        default=True,
        help="Envoyer automatiquement les notifications de notes"
    )
    
    auto_send_homework_reminders = fields.Boolean(
        string='Rappels devoirs auto',
        default=True,
        help="Envoyer automatiquement les rappels de devoirs"
    )
    
    notification_delay_minutes = fields.Integer(
        string='Délai notifications (min)',
        default=15,
        help="Délai avant envoi automatique des notifications"
    )
    
    # Restrictions et limites
    daily_sms_limit = fields.Integer(
        string='Limite SMS/jour',
        default=1000,
        help="Nombre maximum de SMS par jour"
    )
    
    daily_email_limit = fields.Integer(
        string='Limite Email/jour',
        default=5000,
        help="Nombre maximum d'emails par jour"
    )
    
    user_daily_message_limit = fields.Integer(
        string='Messages/jour par utilisateur',
        default=50,
        help="Nombre maximum de messages par utilisateur par jour"
    )
    
    # Heures d'envoi
    send_time_start = fields.Float(
        string='Heure début envoi',
        default=7.0,
        help="Heure de début d'envoi des messages (24h)"
    )
    
    send_time_end = fields.Float(
        string='Heure fin envoi',
        default=20.0,
        help="Heure de fin d'envoi des messages (24h)"
    )
    
    weekend_sending = fields.Boolean(
        string='Envoi weekend',
        default=False,
        help="Autoriser l'envoi de messages le weekend"
    )
    
    holiday_sending = fields.Boolean(
        string='Envoi vacances',
        default=False,
        help="Autoriser l'envoi pendant les vacances"
    )
    
    # Options avancées
    enable_message_encryption = fields.Boolean(
        string='Chiffrement messages',
        default=False,
        help="Chiffrer les messages sensibles"
    )
    
    enable_delivery_reports = fields.Boolean(
        string='Rapports de livraison',
        default=True,
        help="Activer les rapports de livraison"
    )
    
    enable_read_receipts = fields.Boolean(
        string='Accusés de lecture',
        default=True,
        help="Activer les accusés de lecture"
    )
    
    archive_messages_after_days = fields.Integer(
        string='Archivage après (jours)',
        default=365,
        help="Archiver les messages après X jours"
    )
    
    # Intégrations externes
    enable_whatsapp = fields.Boolean(
        string='WhatsApp Business',
        default=False,
        help="Activer l'intégration WhatsApp Business"
    )
    
    whatsapp_business_id = fields.Char(
        string='WhatsApp Business ID',
        help="ID du compte WhatsApp Business"
    )
    
    enable_telegram = fields.Boolean(
        string='Telegram Bot',
        default=False,
        help="Activer l'intégration Telegram"
    )
    
    telegram_bot_token = fields.Char(
        string='Token Bot Telegram',
        help="Token du bot Telegram"
    )
    
    # Statistiques (calculées)
    total_messages_sent = fields.Integer(
        string='Messages envoyés',
        compute='_compute_stats',
        help="Nombre total de messages envoyés"
    )
    
    total_sms_sent = fields.Integer(
        string='SMS envoyés',
        compute='_compute_stats',
        help="Nombre total de SMS envoyés"
    )
    
    total_emails_sent = fields.Integer(
        string='Emails envoyés',
        compute='_compute_stats',
        help="Nombre total d'emails envoyés"
    )
    
    delivery_rate = fields.Float(
        string='Taux de livraison (%)',
        compute='_compute_stats',
        digits=(5, 2),
        help="Taux de livraison des messages"
    )
    
    # Calculs
    def _compute_stats(self):
        """Calcule les statistiques de communication"""
        for record in self:
            messages = self.env['edu.message'].search([])
            record.total_messages_sent = len(messages)
            record.total_sms_sent = len(messages.filtered(lambda m: m.message_type == 'sms'))
            record.total_emails_sent = len(messages.filtered(lambda m: m.message_type == 'email'))
            
            delivered = messages.filtered(lambda m: m.delivery_status == 'delivered')
            if messages:
                record.delivery_rate = (len(delivered) / len(messages)) * 100
            else:
                record.delivery_rate = 0.0
    
    @api.model
    def _get_languages(self):
        """Retourne les langues disponibles"""
        return self.env['res.lang'].get_installed()
    
    @api.model
    def _get_timezone_list(self):
        """Retourne la liste des fuseaux horaires"""
        import pytz
        return [(tz, tz) for tz in sorted(pytz.common_timezones)]
    
    # Contraintes
    @api.constrains('sms_sender_name')
    def _check_sms_sender_name(self):
        """Vérifie la longueur du nom expéditeur SMS"""
        for record in self:
            if record.sms_sender_name and len(record.sms_sender_name) > 11:
                raise ValidationError(_("Le nom expéditeur SMS ne peut pas dépasser 11 caractères"))
    
    @api.constrains('send_time_start', 'send_time_end')
    def _check_send_times(self):
        """Vérifie les heures d'envoi"""
        for record in self:
            if record.send_time_start >= record.send_time_end:
                raise ValidationError(_("L'heure de début doit être antérieure à l'heure de fin"))
            if not (0 <= record.send_time_start <= 24):
                raise ValidationError(_("L'heure de début doit être entre 0 et 24"))
            if not (0 <= record.send_time_end <= 24):
                raise ValidationError(_("L'heure de fin doit être entre 0 et 24"))
    
    @api.constrains('daily_sms_limit', 'daily_email_limit')
    def _check_daily_limits(self):
        """Vérifie les limites quotidiennes"""
        for record in self:
            if record.daily_sms_limit < 0:
                raise ValidationError(_("La limite SMS quotidienne doit être positive"))
            if record.daily_email_limit < 0:
                raise ValidationError(_("La limite email quotidienne doit être positive"))
    
    # Actions
    def action_test_sms_connection(self):
        """Teste la connexion SMS"""
        self.ensure_one()
        try:
            # Test selon le fournisseur
            if self.default_sms_provider == 'twilio':
                success = self._test_twilio_connection()
            elif self.default_sms_provider == 'aws_sns':
                success = self._test_aws_sns_connection()
            else:
                success = True  # Pour les autres fournisseurs
            
            if success:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _("Connexion SMS testée avec succès"),
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_("Échec du test de connexion SMS"))
                
        except Exception as e:
            _logger.error(f"Erreur test connexion SMS: {e}")
            raise UserError(_("Erreur lors du test de connexion SMS: %s") % str(e))
    
    def action_test_email_connection(self):
        """Teste la connexion Email"""
        self.ensure_one()
        try:
            # Test selon le fournisseur
            if self.default_email_provider == 'sendgrid':
                success = self._test_sendgrid_connection()
            elif self.default_email_provider == 'mailgun':
                success = self._test_mailgun_connection()
            else:
                success = True  # Pour les autres fournisseurs
            
            if success:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _("Connexion Email testée avec succès"),
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_("Échec du test de connexion Email"))
                
        except Exception as e:
            _logger.error(f"Erreur test connexion Email: {e}")
            raise UserError(_("Erreur lors du test de connexion Email: %s") % str(e))
    
    def action_reset_daily_counters(self):
        """Remet à zéro les compteurs quotidiens"""
        self.env['edu.message'].search([
            ('create_date', '>=', fields.Date.context_today(self))
        ]).write({'daily_count_reset': True})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("Compteurs quotidiens remis à zéro"),
                'type': 'success',
            }
        }
    
    # Méthodes de test des connexions
    def _test_twilio_connection(self):
        """Teste la connexion Twilio"""
        try:
            provider = self.env['edu.communication.provider'].search([
                ('provider_type', '=', 'sms'),
                ('name', '=', 'twilio')
            ], limit=1)
            
            if not provider:
                return False
            
            from twilio.rest import Client
            client = Client(provider.api_key, provider.api_secret)
            
            # Test simple : récupérer le compte
            account = client.api.account.fetch()
            return account.status == 'active'
            
        except Exception as e:
            _logger.error(f"Erreur test Twilio: {e}")
            return False
    
    def _test_sendgrid_connection(self):
        """Teste la connexion SendGrid"""
        try:
            provider = self.env['edu.communication.provider'].search([
                ('provider_type', '=', 'email'),
                ('name', '=', 'sendgrid')
            ], limit=1)
            
            if not provider:
                return False
            
            import sendgrid
            sg = sendgrid.SendGridAPIClient(api_key=provider.api_key)
            
            # Test simple : vérifier l'API key
            response = sg.client.user.profile.get()
            return response.status_code == 200
            
        except Exception as e:
            _logger.error(f"Erreur test SendGrid: {e}")
            return False
    
    def _test_aws_sns_connection(self):
        """Teste la connexion AWS SNS"""
        # À implémenter selon les besoins
        return True
    
    def _test_mailgun_connection(self):
        """Teste la connexion Mailgun"""
        # À implémenter selon les besoins
        return True
    
    # Méthodes utilitaires
    def is_sending_allowed(self):
        """Vérifie si l'envoi de messages est autorisé maintenant"""
        self.ensure_one()
        
        import datetime
        now = datetime.datetime.now()
        current_hour = now.hour + now.minute / 60.0
        
        # Vérifier les heures d'envoi
        if not (self.send_time_start <= current_hour <= self.send_time_end):
            return False
        
        # Vérifier le weekend
        if not self.weekend_sending and now.weekday() >= 5:  # Samedi=5, Dimanche=6
            return False
        
        # Vérifier les vacances (à implémenter avec le calendrier scolaire)
        if not self.holiday_sending:
            # Logique à ajouter pour vérifier les périodes de vacances
            pass
        
        return True
    
    def get_daily_message_count(self, message_type=None):
        """Retourne le nombre de messages envoyés aujourd'hui"""
        self.ensure_one()
        domain = [('create_date', '>=', fields.Date.context_today(self))]
        
        if message_type:
            domain.append(('message_type', '=', message_type))
        
        return self.env['edu.message'].search_count(domain)
    
    def check_daily_limits(self, message_type):
        """Vérifie si les limites quotidiennes sont respectées"""
        self.ensure_one()
        
        if message_type == 'sms':
            current_count = self.get_daily_message_count('sms')
            return current_count < self.daily_sms_limit
        elif message_type == 'email':
            current_count = self.get_daily_message_count('email')
            return current_count < self.daily_email_limit
        
        return True
    
    @api.model
    def get_active_config(self):
        """Retourne la configuration active"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            # Créer une configuration par défaut
            config = self.create({
                'name': 'Configuration par défaut',
                'school_name': 'École Extraordinaire',
                'active': True,
            })
        return config


class EduCommunicationProvider(models.Model):
    """Fournisseurs de services de communication"""
    _name = 'edu.communication.provider'
    _description = 'Fournisseur Communication'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom',
        required=True
    )
    
    provider_type = fields.Selection([
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification')
    ], string='Type', required=True)
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    api_key = fields.Char(
        string='Clé API'
    )
    
    api_secret = fields.Char(
        string='Secret API'
    )
    
    endpoint_url = fields.Char(
        string='URL du service'
    )
    
    configuration = fields.Text(
        string='Configuration JSON'
    )
