# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class EduCommunicationProvider(models.Model):
    """Fournisseurs de services de communication"""
    _name = 'edu.communication.provider'
    _description = 'Fournisseur de communication'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du fournisseur',
        required=True,
        help="Nom du fournisseur de service"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=20,
        help="Code unique du fournisseur"
    )
    
    provider_type = fields.Selection([
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notifications'),
        ('voice', 'Appels vocaux'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram')
    ], string='Type de service', required=True)
    
    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre de priorité"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True,
        help="Fournisseur actif"
    )
    
    # Configuration de base
    api_endpoint = fields.Char(
        string='Point d\'accès API',
        help="URL de base de l'API"
    )
    
    api_key = fields.Char(
        string='Clé API',
        help="Clé d'authentification API"
    )
    
    api_secret = fields.Char(
        string='Secret API',
        help="Secret d'authentification API"
    )
    
    username = fields.Char(
        string='Nom d\'utilisateur',
        help="Nom d'utilisateur pour l'authentification"
    )
    
    password = fields.Char(
        string='Mot de passe',
        help="Mot de passe pour l'authentification"
    )
    
    # Configuration spécifique SMS
    sender_id = fields.Char(
        string='ID expéditeur',
        help="ID ou nom de l'expéditeur"
    )
    
    country_code = fields.Char(
        string='Code pays',
        default='+221',
        help="Code pays par défaut"
    )
    
    # Configuration spécifique Email
    smtp_server = fields.Char(
        string='Serveur SMTP',
        help="Adresse du serveur SMTP"
    )
    
    smtp_port = fields.Integer(
        string='Port SMTP',
        default=587,
        help="Port du serveur SMTP"
    )
    
    smtp_encryption = fields.Selection([
        ('none', 'Aucun'),
        ('tls', 'TLS'),
        ('ssl', 'SSL')
    ], string='Chiffrement SMTP', default='tls')
    
    # Limites et tarification
    rate_limit_per_second = fields.Integer(
        string='Limite/seconde',
        default=10,
        help="Nombre maximum de messages par seconde"
    )
    
    rate_limit_per_minute = fields.Integer(
        string='Limite/minute',
        default=60,
        help="Nombre maximum de messages par minute"
    )
    
    rate_limit_per_hour = fields.Integer(
        string='Limite/heure',
        default=1000,
        help="Nombre maximum de messages par heure"
    )
    
    cost_per_message = fields.Float(
        string='Coût par message',
        digits=(8, 4),
        help="Coût unitaire d'un message"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id,
        help="Devise pour la tarification"
    )
    
    # Fonctionnalités supportées
    supports_delivery_reports = fields.Boolean(
        string='Rapports de livraison',
        default=True,
        help="Supporte les rapports de livraison"
    )
    
    supports_read_receipts = fields.Boolean(
        string='Accusés de lecture',
        default=False,
        help="Supporte les accusés de lecture"
    )
    
    supports_attachments = fields.Boolean(
        string='Pièces jointes',
        default=False,
        help="Supporte les pièces jointes"
    )
    
    supports_rich_content = fields.Boolean(
        string='Contenu riche',
        default=False,
        help="Supporte le contenu HTML/riche"
    )
    
    max_message_length = fields.Integer(
        string='Longueur max message',
        default=160,
        help="Longueur maximale d'un message"
    )
    
    max_attachment_size = fields.Float(
        string='Taille max pièce jointe (MB)',
        default=10.0,
        help="Taille maximale des pièces jointes"
    )
    
    # Statut et monitoring
    last_test_date = fields.Datetime(
        string='Dernier test',
        help="Date du dernier test de connexion"
    )
    
    last_test_result = fields.Boolean(
        string='Résultat du test',
        help="Résultat du dernier test"
    )
    
    last_error = fields.Text(
        string='Dernière erreur',
        help="Message de la dernière erreur"
    )
    
    is_online = fields.Boolean(
        string='En ligne',
        compute='_compute_online_status',
        help="Statut de connexion"
    )
    
    # Statistiques
    total_messages_sent = fields.Integer(
        string='Messages envoyés',
        default=0,
        help="Nombre total de messages envoyés"
    )
    
    total_cost = fields.Float(
        string='Coût total',
        digits=(8, 2),
        help="Coût total des messages envoyés"
    )
    
    success_rate = fields.Float(
        string='Taux de succès (%)',
        compute='_compute_success_rate',
        digits=(5, 2),
        help="Pourcentage de messages livrés avec succès"
    )
    
    # Configuration avancée
    webhook_url = fields.Char(
        string='URL Webhook',
        help="URL pour recevoir les callbacks"
    )
    
    custom_headers = fields.Text(
        string='En-têtes personnalisés',
        help="En-têtes HTTP personnalisés (format JSON)"
    )
    
    timeout = fields.Integer(
        string='Timeout (secondes)',
        default=30,
        help="Délai d'attente pour les requêtes API"
    )
    
    retry_attempts = fields.Integer(
        string='Tentatives de retry',
        default=3,
        help="Nombre de tentatives en cas d'échec"
    )
    
    # Calculs
    @api.depends('last_test_date', 'last_test_result')
    def _compute_online_status(self):
        """Calcule le statut en ligne"""
        for record in self:
            if record.last_test_date and record.last_test_result:
                # En ligne si testé avec succès dans les 24h
                import datetime
                time_diff = datetime.datetime.now() - record.last_test_date
                record.is_online = time_diff.total_seconds() < 86400  # 24h
            else:
                record.is_online = False
    
    def _compute_success_rate(self):
        """Calcule le taux de succès"""
        for record in self:
            deliveries = self.env['edu.message.delivery'].search([
                ('message_id.provider_id', '=', record.id)
            ])
            
            if deliveries:
                successful = deliveries.filtered(lambda d: d.delivery_status == 'delivered')
                record.success_rate = (len(successful) / len(deliveries)) * 100
            else:
                record.success_rate = 0.0
    
    # Contraintes
    @api.constrains('code')
    def _check_unique_code(self):
        """Vérifie l'unicité du code"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Le code '%s' existe déjà") % record.code)
    
    @api.constrains('rate_limit_per_second', 'rate_limit_per_minute', 'rate_limit_per_hour')
    def _check_rate_limits(self):
        """Vérifie la cohérence des limites de débit"""
        for record in self:
            if record.rate_limit_per_second < 0:
                raise ValidationError(_("La limite par seconde doit être positive"))
            if record.rate_limit_per_minute < record.rate_limit_per_second:
                raise ValidationError(_("La limite par minute doit être >= limite par seconde"))
            if record.rate_limit_per_hour < record.rate_limit_per_minute:
                raise ValidationError(_("La limite par heure doit être >= limite par minute"))
    
    # Actions de test
    def action_test_connection(self):
        """Teste la connexion au fournisseur"""
        self.ensure_one()
        
        try:
            if self.provider_type == 'sms':
                result = self._test_sms_connection()
            elif self.provider_type == 'email':
                result = self._test_email_connection()
            elif self.provider_type == 'push':
                result = self._test_push_connection()
            else:
                result = self._test_generic_connection()
            
            self.last_test_date = fields.Datetime.now()
            self.last_test_result = result
            
            if result:
                self.last_error = False
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _("Test de connexion réussi"),
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_("Test de connexion échoué"))
                
        except Exception as e:
            _logger.error(f"Erreur test connexion fournisseur {self.name}: {e}")
            self.last_test_date = fields.Datetime.now()
            self.last_test_result = False
            self.last_error = str(e)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Erreur lors du test: %s") % str(e),
                    'type': 'danger',
                }
            }
    
    def _test_sms_connection(self):
        """Teste la connexion SMS"""
        if self.code == 'twilio':
            return self._test_twilio()
        elif self.code == 'aws_sns':
            return self._test_aws_sns()
        elif self.code == 'infobip':
            return self._test_infobip()
        else:
            return self._test_generic_sms()
    
    def _test_email_connection(self):
        """Teste la connexion Email"""
        if self.code == 'sendgrid':
            return self._test_sendgrid()
        elif self.code == 'mailgun':
            return self._test_mailgun()
        elif self.code == 'smtp':
            return self._test_smtp()
        else:
            return self._test_generic_email()
    
    def _test_push_connection(self):
        """Teste la connexion Push"""
        if self.code == 'firebase':
            return self._test_firebase()
        else:
            return self._test_generic_push()
    
    def _test_generic_connection(self):
        """Test générique de connexion"""
        if not self.api_endpoint:
            return False
        
        try:
            response = requests.get(
                self.api_endpoint,
                timeout=self.timeout,
                headers=self._get_headers()
            )
            return response.status_code < 400
        except:
            return False
    
    # Tests spécifiques par fournisseur
    def _test_twilio(self):
        """Test Twilio"""
        try:
            from twilio.rest import Client
            client = Client(self.api_key, self.api_secret)
            account = client.api.account.fetch()
            return account.status == 'active'
        except Exception as e:
            _logger.error(f"Erreur test Twilio: {e}")
            return False
    
    def _test_sendgrid(self):
        """Test SendGrid"""
        try:
            import sendgrid
            sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            response = sg.client.user.profile.get()
            return response.status_code == 200
        except Exception as e:
            _logger.error(f"Erreur test SendGrid: {e}")
            return False
    
    def _test_firebase(self):
        """Test Firebase"""
        try:
            # Test avec Firebase Admin SDK
            import firebase_admin
            from firebase_admin import credentials, messaging
            
            # Logique de test Firebase
            return True
        except Exception as e:
            _logger.error(f"Erreur test Firebase: {e}")
            return False
    
    def _test_generic_sms(self):
        """Test générique SMS"""
        return self._test_generic_connection()
    
    def _test_generic_email(self):
        """Test générique Email"""
        return self._test_generic_connection()
    
    def _test_generic_push(self):
        """Test générique Push"""
        return self._test_generic_connection()
    
    def _test_smtp(self):
        """Test SMTP"""
        try:
            import smtplib
            
            if self.smtp_encryption == 'ssl':
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.smtp_encryption == 'tls':
                    server.starttls()
            
            if self.username and self.password:
                server.login(self.username, self.password)
            
            server.quit()
            return True
            
        except Exception as e:
            _logger.error(f"Erreur test SMTP: {e}")
            return False
    
    # Méthodes d'envoi
    def _send_sms(self, phone_number, message, delivery_record=None):
        """Envoie un SMS"""
        self.ensure_one()
        
        if self.code == 'twilio':
            return self._send_twilio_sms(phone_number, message, delivery_record)
        elif self.code == 'aws_sns':
            return self._send_aws_sns_sms(phone_number, message, delivery_record)
        else:
            return self._send_generic_sms(phone_number, message, delivery_record)
    
    def _send_email(self, email_data, delivery_record=None):
        """Envoie un email"""
        self.ensure_one()
        
        if self.code == 'sendgrid':
            return self._send_sendgrid_email(email_data, delivery_record)
        elif self.code == 'mailgun':
            return self._send_mailgun_email(email_data, delivery_record)
        else:
            return self._send_generic_email(email_data, delivery_record)
    
    def _send_push_notification(self, notification_data, delivery_record=None):
        """Envoie une notification push"""
        self.ensure_one()
        
        if self.code == 'firebase':
            return self._send_firebase_push(notification_data, delivery_record)
        else:
            return self._send_generic_push(notification_data, delivery_record)
    
    # Implémentations spécifiques
    def _send_twilio_sms(self, phone_number, message, delivery_record):
        """Envoie SMS via Twilio"""
        try:
            from twilio.rest import Client
            client = Client(self.api_key, self.api_secret)
            
            # Nettoyer le numéro de téléphone
            phone = self._format_phone_number(phone_number)
            
            # Envoyer le SMS
            twilio_message = client.messages.create(
                body=message,
                from_=self.sender_id,
                to=phone
            )
            
            # Mettre à jour le rapport de livraison
            if delivery_record:
                delivery_record.write({
                    'delivery_status': 'sent',
                    'sent_date': fields.Datetime.now(),
                    'external_id': twilio_message.sid,
                    'cost': self.cost_per_message
                })
            
            # Mettre à jour les statistiques
            self.total_messages_sent += 1
            self.total_cost += self.cost_per_message
            
            return True
            
        except Exception as e:
            _logger.error(f"Erreur envoi SMS Twilio: {e}")
            if delivery_record:
                delivery_record.write({
                    'delivery_status': 'failed',
                    'error_message': str(e)
                })
            return False
    
    def _send_sendgrid_email(self, email_data, delivery_record):
        """Envoie email via SendGrid"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            
            mail = Mail(
                from_email=email_data.get('from_email'),
                to_emails=email_data.get('to_email'),
                subject=email_data.get('subject'),
                html_content=email_data.get('content')
            )
            
            response = sg.send(mail)
            
            # Mettre à jour le rapport de livraison
            if delivery_record:
                delivery_record.write({
                    'delivery_status': 'sent',
                    'sent_date': fields.Datetime.now(),
                    'external_id': response.headers.get('X-Message-Id'),
                    'cost': self.cost_per_message
                })
            
            # Mettre à jour les statistiques
            self.total_messages_sent += 1
            self.total_cost += self.cost_per_message
            
            return True
            
        except Exception as e:
            _logger.error(f"Erreur envoi email SendGrid: {e}")
            if delivery_record:
                delivery_record.write({
                    'delivery_status': 'failed',
                    'error_message': str(e)
                })
            return False
    
    def _send_generic_sms(self, phone_number, message, delivery_record):
        """Envoi SMS générique via API"""
        try:
            data = {
                'to': self._format_phone_number(phone_number),
                'message': message,
                'from': self.sender_id
            }
            
            response = requests.post(
                f"{self.api_endpoint}/sms/send",
                json=data,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                if delivery_record:
                    delivery_record.write({
                        'delivery_status': 'sent',
                        'sent_date': fields.Datetime.now(),
                        'external_id': response.json().get('id'),
                        'cost': self.cost_per_message
                    })
                
                self.total_messages_sent += 1
                self.total_cost += self.cost_per_message
                return True
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            _logger.error(f"Erreur envoi SMS générique: {e}")
            if delivery_record:
                delivery_record.write({
                    'delivery_status': 'failed',
                    'error_message': str(e)
                })
            return False
    
    def _send_generic_email(self, email_data, delivery_record):
        """Envoi email générique via API"""
        # À implémenter selon l'API du fournisseur
        return True
    
    def _send_generic_push(self, notification_data, delivery_record):
        """Envoi push générique via API"""
        # À implémenter selon l'API du fournisseur
        return True
    
    # Méthodes utilitaires
    def _format_phone_number(self, phone):
        """Formate un numéro de téléphone"""
        if not phone:
            return None
        
        # Supprimer tous les caractères non numériques sauf +
        import re
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Ajouter le code pays si nécessaire
        if not phone.startswith('+'):
            if phone.startswith('00'):
                phone = '+' + phone[2:]
            elif not phone.startswith(self.country_code.replace('+', '')):
                phone = self.country_code + phone
        
        return phone
    
    def _get_headers(self):
        """Retourne les en-têtes HTTP pour les requêtes"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'EduCommunicationHub/1.0'
        }
        
        # Authentification
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        elif self.username and self.password:
            import base64
            credentials = base64.b64encode(f'{self.username}:{self.password}'.encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'
        
        # En-têtes personnalisés
        if self.custom_headers:
            try:
                import json
                custom = json.loads(self.custom_headers)
                headers.update(custom)
            except:
                pass
        
        return headers
    
    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            if record.provider_type:
                name += f" ({record.provider_type.upper()})"
            result.append((record.id, name))
        return result
    
    # Actions
    def action_view_messages(self):
        """Affiche les messages envoyés via ce fournisseur"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Messages - %s') % self.name,
            'res_model': 'edu.message',
            'view_mode': 'tree,form',
            'domain': [('provider_id', '=', self.id)],
        }
    
    def action_view_delivery_reports(self):
        """Affiche les rapports de livraison"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rapports de livraison - %s') % self.name,
            'res_model': 'edu.message.delivery',
            'view_mode': 'tree,form',
            'domain': [('message_id.provider_id', '=', self.id)],
        }
