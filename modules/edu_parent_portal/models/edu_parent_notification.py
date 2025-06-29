# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class EduParentNotification(models.Model):
    """Notifications pour les parents"""
    _name = 'edu.parent.notification'
    _description = 'Notification parent'
    _order = 'create_date desc'
    _rec_name = 'title'

    title = fields.Char(
        string='Titre',
        required=True,
        help="Titre de la notification"
    )
    
    message = fields.Html(
        string='Message',
        required=True,
        help="Contenu de la notification"
    )
    
    notification_type = fields.Selection([
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('success', 'Succès'),
        ('error', 'Erreur'),
        ('urgent', 'Urgent')
    ], string='Type', default='info', required=True, help="Type de notification")
    
    category = fields.Selection([
        ('grade', 'Notes'),
        ('attendance', 'Présence'),
        ('homework', 'Devoirs'),
        ('announcement', 'Annonce'),
        ('meeting', 'Réunion'),
        ('payment', 'Paiement'),
        ('document', 'Document'),
        ('disciplinary', 'Disciplinaire'),
        ('medical', 'Médical'),
        ('transport', 'Transport'),
        ('other', 'Autre')
    ], string='Catégorie', required=True, help="Catégorie de notification")
    
    recipient_ids = fields.Many2many(
        'res.users',
        string='Destinataires',
        help="Utilisateurs destinataires"
    )
    
    student_ids = fields.Many2many(
        'op.student',
        string='Élèves concernés',
        help="Élèves concernés par la notification"
    )
    
    sender_id = fields.Many2one(
        'res.users',
        string='Expéditeur',
        default=lambda self: self.env.user,
        help="Utilisateur expéditeur"
    )
    
    # Statut de la notification
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('read', 'Lue'),
        ('archived', 'Archivée')
    ], string='État', default='draft', help="État de la notification")
    
    # Canaux d'envoi
    send_email = fields.Boolean(
        string='Envoyer par email',
        default=True,
        help="Envoyer par email"
    )
    
    send_sms = fields.Boolean(
        string='Envoyer par SMS',
        default=False,
        help="Envoyer par SMS"
    )
    
    send_push = fields.Boolean(
        string='Notification push',
        default=True,
        help="Envoyer une notification push"
    )
    
    # Dates importantes
    send_date = fields.Datetime(
        string='Date d\'envoi',
        help="Date d'envoi de la notification"
    )
    
    read_date = fields.Datetime(
        string='Date de lecture',
        help="Date de lecture de la notification"
    )
    
    expiry_date = fields.Datetime(
        string='Date d\'expiration',
        help="Date d'expiration de la notification"
    )
    
    # Pièces jointes
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Pièces jointes',
        help="Pièces jointes à la notification"
    )
    
    # Priorité
    priority = fields.Selection([
        ('0', 'Normale'),
        ('1', 'Importante'),
        ('2', 'Urgente')
    ], string='Priorité', default='0', help="Priorité de la notification")
    
    # Statistiques
    read_count = fields.Integer(
        string='Nombre de lectures',
        default=0,
        help="Nombre de fois lue"
    )
    
    click_count = fields.Integer(
        string='Nombre de clics',
        default=0,
        help="Nombre de clics sur la notification"
    )
    
    # Méthodes d'action
    def action_send(self):
        """Envoyer la notification"""
        for record in self:
            if record.state == 'draft':
                record._send_notification()
                record.write({
                    'state': 'sent',
                    'send_date': fields.Datetime.now()
                })
    
    def action_mark_read(self):
        """Marquer comme lue"""
        for record in self:
            if record.state == 'sent':
                record.write({
                    'state': 'read',
                    'read_date': fields.Datetime.now(),
                    'read_count': record.read_count + 1
                })
    
    def action_archive(self):
        """Archiver la notification"""
        self.write({'state': 'archived'})
    
    def _send_notification(self):
        """Méthode privée pour envoyer la notification"""
        # Logique d'envoi selon les canaux activés
        if self.send_email:
            self._send_email_notification()
        
        if self.send_sms:
            self._send_sms_notification()
        
        if self.send_push:
            self._send_push_notification()
    
    def _send_email_notification(self):
        """Envoyer par email"""
        # Logique d'envoi email
        pass
    
    def _send_sms_notification(self):
        """Envoyer par SMS"""
        # Logique d'envoi SMS
        pass
    
    def _send_push_notification(self):
        """Envoyer notification push"""
        # Logique d'envoi push
        pass
    
    @api.model
    def send_batch_notifications(self):
        """Envoyer les notifications en lot (appelé par cron)"""
        notifications = self.search([
            ('state', '=', 'draft'),
            ('send_date', '<=', fields.Datetime.now())
        ])
        notifications.action_send()
    
    @api.model
    def cleanup_old_notifications(self):
        """Nettoyer les anciennes notifications"""
        cutoff_date = datetime.now() - timedelta(days=90)
        old_notifications = self.search([
            ('create_date', '<', cutoff_date),
            ('state', 'in', ['read', 'archived'])
        ])
        old_notifications.unlink()
