# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class EduNotificationPreference(models.Model):
    """Préférences de notification pour les parents"""
    _name = 'edu.notification.preference'
    _description = 'Préférences de notification parent'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom de la préférence',
        required=True,
        help="Nom de la préférence de notification"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        help="Code unique de la préférence de notification"
    )
    
    description = fields.Text(
        string='Description',
        help="Description de la préférence de notification"
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Utilisateur',
        required=True,
        default=lambda self: self.env.user,
        help="Utilisateur concerné par ces préférences"
    )
    
    # Types de notifications
    notification_type = fields.Selection([
        ('grades', 'Notes et évaluations'),
        ('attendance', 'Présences/Absences'),
        ('homework', 'Devoirs et travaux'),
        ('schedule', 'Emploi du temps'),
        ('disciplinary', 'Sanctions disciplinaires'),
        ('medical', 'Informations médicales'),
        ('transport', 'Transport scolaire'),
        ('payments', 'Paiements et factures'),
        ('announcements', 'Annonces générales'),
        ('meetings', 'Réunions et rendez-vous'),
        ('documents', 'Documents scolaires'),
        ('emergency', 'Urgences'),
        ('system', 'Notifications système'),
    ], string='Type de notification', required=True, help="Type de notification concerné")
    
    # Canaux de notification
    email_enabled = fields.Boolean(
        string='Notification par email',
        default=True,
        help="Recevoir les notifications par email"
    )
    
    email_address = fields.Char(
        string='Adresse email',
        help="Adresse email pour les notifications (si différente du profil)"
    )
    
    sms_enabled = fields.Boolean(
        string='Notification par SMS',
        default=False,
        help="Recevoir les notifications par SMS"
    )
    
    phone_number = fields.Char(
        string='Numéro de téléphone',
        help="Numéro pour les notifications SMS"
    )
    
    push_enabled = fields.Boolean(
        string='Notifications push',
        default=True,
        help="Recevoir les notifications push sur l'application mobile"
    )
    
    portal_enabled = fields.Boolean(
        string='Notifications portail',
        default=True,
        help="Afficher les notifications dans le portail web"
    )
    
    # Paramètres de fréquence
    frequency = fields.Selection([
        ('immediate', 'Immédiat'),
        ('hourly', 'Toutes les heures'),
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('never', 'Jamais')
    ], string='Fréquence', default='immediate', help="Fréquence d'envoi des notifications")
    
    daily_digest_time = fields.Float(
        string='Heure du résumé quotidien',
        default=18.0,
        help="Heure d'envoi du résumé quotidien (format 24h)"
    )
    
    weekly_digest_day = fields.Selection([
        ('0', 'Lundi'),
        ('1', 'Mardi'),
        ('2', 'Mercredi'),
        ('3', 'Jeudi'),
        ('4', 'Vendredi'),
        ('5', 'Samedi'),
        ('6', 'Dimanche')
    ], string='Jour du résumé hebdomadaire', default='0', help="Jour d'envoi du résumé hebdomadaire")
    
    # Filtres et conditions
    priority_filter = fields.Selection([
        ('all', 'Toutes les priorités'),
        ('high', 'Haute priorité uniquement'),
        ('medium_high', 'Moyenne et haute priorité'),
        ('low_only', 'Basse priorité uniquement')
    ], string='Filtre de priorité', default='all', help="Filtrer par niveau de priorité")
    
    student_ids = fields.Many2many(
        'op.student',
        string='Étudiants concernés',
        help="Limiter aux étudiants sélectionnés (vide = tous les enfants)"
    )
    
    subject_filter = fields.Char(
        string='Filtre par matière',
        help="Filtrer par matière (expressions régulières supportées)"
    )
    
    teacher_ids = fields.Many2many(
        'res.partner',
        string='Enseignants concernés',
        domain=[('is_company', '=', False)],
        help="Limiter aux enseignants sélectionnés"
    )
    
    # Paramètres avancés
    active = fields.Boolean(
        string='Actif',
        default=True,
        help="Préférence active"
    )
    
    quiet_hours_start = fields.Float(
        string='Début heures silencieuses',
        default=22.0,
        help="Heure de début des heures silencieuses (pas de notifications)"
    )
    
    quiet_hours_end = fields.Float(
        string='Fin heures silencieuses',
        default=7.0,
        help="Heure de fin des heures silencieuses"
    )
    
    weekend_notifications = fields.Boolean(
        string='Notifications le weekend',
        default=False,
        help="Recevoir des notifications le weekend"
    )
    
    vacation_mode = fields.Boolean(
        string='Mode vacances',
        default=False,
        help="Suspendre temporairement toutes les notifications"
    )
    
    vacation_start = fields.Date(
        string='Début vacances',
        help="Date de début de suspension des notifications"
    )
    
    vacation_end = fields.Date(
        string='Fin vacances',
        help="Date de fin de suspension des notifications"
    )
    
    # Templates personnalisés
    custom_email_template = fields.Html(
        string='Template email personnalisé',
        help="Template personnalisé pour les emails (optionnel)"
    )
    
    custom_sms_template = fields.Text(
        string='Template SMS personnalisé',
        help="Template personnalisé pour les SMS (optionnel)"
    )
    
    # Statistiques
    last_notification_sent = fields.Datetime(
        string='Dernière notification envoyée',
        readonly=True,
        help="Date de la dernière notification envoyée"
    )
    
    total_notifications_sent = fields.Integer(
        string='Total notifications envoyées',
        default=0,
        readonly=True,
        help="Nombre total de notifications envoyées"
    )
    
    last_email_sent = fields.Datetime(
        string='Dernier email envoyé',
        readonly=True,
        help="Date du dernier email envoyé"
    )
    
    last_sms_sent = fields.Datetime(
        string='Dernier SMS envoyé',
        readonly=True,
        help="Date du dernier SMS envoyé"
    )
    
    # Méthodes
    @api.model
    def get_user_preferences(self, user_id=None, notification_type=None):
        """Récupère les préférences d'un utilisateur"""
        if not user_id:
            user_id = self.env.user.id
        
        domain = [('user_id', '=', user_id), ('active', '=', True)]
        if notification_type:
            domain.append(('notification_type', '=', notification_type))
        
        return self.search(domain)
    
    @api.model
    def create_default_preferences(self, user_id):
        """Crée les préférences par défaut pour un utilisateur"""
        default_types = [
            'grades', 'attendance', 'homework', 'schedule',
            'disciplinary', 'payments', 'announcements', 'emergency'
        ]
        
        preferences = []
        for notif_type in default_types:
            pref_name = dict(self._fields['notification_type'].selection)[notif_type]
            preferences.append({
                'name': f"Préférence {pref_name}",
                'user_id': user_id,
                'notification_type': notif_type,
                'email_enabled': True,
                'portal_enabled': True,
                'frequency': 'immediate' if notif_type == 'emergency' else 'daily',
            })
        
        return self.create(preferences)
    
    def should_send_notification(self, notification_data):
        """Vérifie si une notification doit être envoyée selon les préférences"""
        self.ensure_one()
        
        # Vérifier si la préférence est active
        if not self.active:
            return False
        
        # Vérifier le mode vacances
        if self.vacation_mode:
            today = fields.Date.context_today(self)
            if self.vacation_start and self.vacation_end:
                if self.vacation_start <= today <= self.vacation_end:
                    return False
        
        # Vérifier les heures silencieuses
        now = datetime.now()
        current_hour = now.hour + now.minute / 60.0
        
        if self.quiet_hours_start > self.quiet_hours_end:  # Traverse minuit
            if current_hour >= self.quiet_hours_start or current_hour <= self.quiet_hours_end:
                return False
        else:
            if self.quiet_hours_start <= current_hour <= self.quiet_hours_end:
                return False
        
        # Vérifier les notifications weekend
        if not self.weekend_notifications and now.weekday() >= 5:  # Samedi=5, Dimanche=6
            return False
        
        # Vérifier le filtre de priorité
        notification_priority = notification_data.get('priority', 'medium')
        if self.priority_filter == 'high' and notification_priority != 'high':
            return False
        elif self.priority_filter == 'medium_high' and notification_priority == 'low':
            return False
        elif self.priority_filter == 'low_only' and notification_priority != 'low':
            return False
        
        # Vérifier les filtres d'étudiants
        if self.student_ids and notification_data.get('student_id'):
            if notification_data['student_id'] not in self.student_ids.ids:
                return False
        
        return True
    
    def get_notification_channels(self):
        """Retourne les canaux de notification activés"""
        self.ensure_one()
        channels = []
        
        if self.email_enabled:
            channels.append('email')
        if self.sms_enabled:
            channels.append('sms')
        if self.push_enabled:
            channels.append('push')
        if self.portal_enabled:
            channels.append('portal')
        
        return channels
    
    def update_notification_stats(self, channel):
        """Met à jour les statistiques de notification"""
        self.ensure_one()
        now = fields.Datetime.now()
        
        values = {
            'last_notification_sent': now,
            'total_notifications_sent': self.total_notifications_sent + 1
        }
        
        if channel == 'email':
            values['last_email_sent'] = now
        elif channel == 'sms':
            values['last_sms_sent'] = now
        
        self.write(values)
    
    # Actions
    def action_test_notification(self):
        """Envoie une notification de test"""
        self.ensure_one()
        # Implémenter l'envoi de notification de test
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test envoyé'),
                'message': _('Une notification de test a été envoyée selon vos préférences.'),
                'type': 'success'
            }
        }
    
    def action_reset_to_default(self):
        """Remet les préférences par défaut"""
        self.ensure_one()
        self.write({
            'email_enabled': True,
            'sms_enabled': False,
            'push_enabled': True,
            'portal_enabled': True,
            'frequency': 'immediate' if self.notification_type == 'emergency' else 'daily',
            'priority_filter': 'all',
            'quiet_hours_start': 22.0,
            'quiet_hours_end': 7.0,
            'weekend_notifications': False,
            'vacation_mode': False,
        })
    
    @api.constrains('quiet_hours_start', 'quiet_hours_end')
    def _check_quiet_hours(self):
        """Valide les heures silencieuses"""
        for record in self:
            if not (0 <= record.quiet_hours_start <= 24 and 0 <= record.quiet_hours_end <= 24):
                raise models.ValidationError(_("Les heures silencieuses doivent être entre 0 et 24."))
    
    @api.constrains('vacation_start', 'vacation_end')
    def _check_vacation_dates(self):
        """Valide les dates de vacances"""
        for record in self:
            if record.vacation_start and record.vacation_end:
                if record.vacation_start > record.vacation_end:
                    raise models.ValidationError(_("La date de début des vacances doit être antérieure à la date de fin."))
