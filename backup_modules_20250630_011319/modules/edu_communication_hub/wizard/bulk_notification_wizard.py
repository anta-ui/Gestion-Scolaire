# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class BulkNotificationWizard(models.TransientModel):
    """Assistant d'envoi de notifications en masse"""
    _name = 'edu.bulk.notification.wizard'
    _description = 'Assistant de notifications en masse'

    # Configuration de base
    title = fields.Char(
        string='Titre de la notification',
        required=True,
        help="Titre de la notification"
    )
    
    message = fields.Text(
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
    ], string='Type de notification', default='info', required=True)
    
    # Canaux de diffusion
    send_email = fields.Boolean(
        string='Envoyer par email',
        default=True,
        help="Envoyer la notification par email"
    )
    
    send_sms = fields.Boolean(
        string='Envoyer par SMS',
        default=False,
        help="Envoyer la notification par SMS"
    )
    
    send_push = fields.Boolean(
        string='Notification push',
        default=True,
        help="Envoyer une notification push"
    )
    
    send_in_app = fields.Boolean(
        string='Notification dans l\'app',
        default=True,
        help="Afficher la notification dans l'application"
    )
    
    # Ciblage des destinataires
    target_type = fields.Selection([
        ('all_students', 'Tous les étudiants'),
        ('all_parents', 'Tous les parents'),
        ('all_faculty', 'Tout le personnel'),
        ('all_users', 'Tous les utilisateurs'),
        ('by_class', 'Par classe'),
        ('by_course', 'Par cours'),
        ('by_group', 'Par groupe'),
        ('custom', 'Sélection personnalisée')
    ], string='Ciblage', default='all_students', required=True)
    
    # Filtres par classe/cours
    class_ids = fields.Many2many(
        'op.batch',
        string='Classes',
        help="Sélectionner les classes"
    )
    
    course_ids = fields.Many2many(
        'op.course',
        string='Cours',
        help="Sélectionner les cours"
    )
    
    # Sélection personnalisée
    student_ids = fields.Many2many(
        'op.student',
        'bulk_notif_student_rel',
        string='Étudiants',
        help="Sélectionner les étudiants"
    )
    
    parent_ids = fields.Many2many(
        'op.parent',
        'bulk_notif_parent_rel',
        string='Parents',
        help="Sélectionner les parents"
    )
    
    faculty_ids = fields.Many2many(
        'op.faculty',
        'bulk_notif_faculty_rel',
        string='Personnel',
        help="Sélectionner le personnel"
    )
    
    # Options avancées
    priority = fields.Selection([
        ('low', 'Basse'),
        ('normal', 'Normale'),
        ('high', 'Haute'),
        ('urgent', 'Urgente')
    ], string='Priorité', default='normal')
    
    expires_at = fields.Datetime(
        string='Expire le',
        help="Date d'expiration de la notification"
    )
    
    require_acknowledgment = fields.Boolean(
        string='Accusé de réception requis',
        default=False,
        help="Demander un accusé de réception"
    )
    
    # Programmation
    send_now = fields.Boolean(
        string='Envoyer maintenant',
        default=True,
        help="Envoyer immédiatement"
    )
    
    scheduled_date = fields.Datetime(
        string='Programmer pour',
        help="Date et heure d'envoi"
    )
    
    # Statistiques (calculées)
    recipient_count = fields.Integer(
        string='Nombre de destinataires',
        compute='_compute_recipient_count',
        help="Nombre total de destinataires"
    )
    
    @api.depends('target_type', 'class_ids', 'course_ids', 'student_ids', 'parent_ids', 'faculty_ids')
    def _compute_recipient_count(self):
        """Calcule le nombre de destinataires"""
        for record in self:
            count = 0
            recipients = record._get_recipients()
            count = len(recipients)
            record.recipient_count = count
    
    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        """Vérifie que la date programmée est dans le futur"""
        for record in self:
            if not record.send_now and record.scheduled_date:
                if record.scheduled_date <= fields.Datetime.now():
                    raise ValidationError(_("La date programmée doit être dans le futur"))
    
    def action_send_notifications(self):
        """Envoie les notifications en masse"""
        self.ensure_one()
        
        # Validation
        if not self.send_now and not self.scheduled_date:
            raise UserError(_("Veuillez spécifier une date d'envoi ou cocher 'Envoyer maintenant'"))
        
        if not any([self.send_email, self.send_sms, self.send_push, self.send_in_app]):
            raise UserError(_("Veuillez sélectionner au moins un canal de diffusion"))
        
        # Récupérer les destinataires
        recipients = self._get_recipients()
        
        if not recipients:
            raise UserError(_("Aucun destinataire trouvé"))
        
        # Créer la notification en masse
        notification_vals = {
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'priority': self.priority,
            'expires_at': self.expires_at,
            'require_acknowledgment': self.require_acknowledgment,
            'send_email': self.send_email,
            'send_sms': self.send_sms,
            'send_push': self.send_push,
            'send_in_app': self.send_in_app,
            'scheduled_date': self.scheduled_date if not self.send_now else False,
            'state': 'sending' if self.send_now else 'scheduled',
            'recipient_count': len(recipients),
        }
        
        notification = self.env['edu.bulk.notification'].create(notification_vals)
        
        # Créer les enregistrements individuels pour chaque destinataire
        for recipient in recipients:
            self.env['edu.notification.recipient'].create({
                'notification_id': notification.id,
                'partner_id': recipient.partner_id.id if hasattr(recipient, 'partner_id') else recipient.id,
                'recipient_type': self._get_recipient_type(recipient),
                'state': 'pending',
            })
        
        # Envoyer immédiatement si demandé
        if self.send_now:
            notification.action_send()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Notification créée'),
            'res_model': 'edu.bulk.notification',
            'res_id': notification.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _get_recipients(self):
        """Récupère la liste des destinataires selon le ciblage"""
        recipients = []
        
        if self.target_type == 'all_students':
            recipients = self.env['op.student'].search([])
        elif self.target_type == 'all_parents':
            recipients = self.env['op.parent'].search([])
        elif self.target_type == 'all_faculty':
            recipients = self.env['op.faculty'].search([])
        elif self.target_type == 'all_users':
            recipients = (
                self.env['op.student'].search([]) +
                self.env['op.parent'].search([]) +
                self.env['op.faculty'].search([])
            )
        elif self.target_type == 'by_class':
            if self.class_ids:
                students = self.env['op.student'].search([('batch_id', 'in', self.class_ids.ids)])
                recipients = students
        elif self.target_type == 'by_course':
            if self.course_ids:
                students = self.env['op.student'].search([('course_detail_ids.course_id', 'in', self.course_ids.ids)])
                recipients = students
        elif self.target_type == 'custom':
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
    
    def action_preview_recipients(self):
        """Prévisualise la liste des destinataires"""
        self.ensure_one()
        
        recipients = self._get_recipients()
        recipient_names = [r.name for r in recipients]
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Aperçu des destinataires (%d)') % len(recipients),
            'res_model': 'edu.recipient.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_recipient_names': '\n'.join(recipient_names),
                'default_count': len(recipients),
            }
        }
    
    def action_test_notification(self):
        """Envoie une notification de test à l'utilisateur actuel"""
        self.ensure_one()
        
        # Créer une notification de test
        test_vals = {
            'title': '[TEST] ' + self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'priority': self.priority,
            'send_in_app': True,
            'send_email': False,
            'send_sms': False,
            'send_push': False,
            'state': 'sending',
            'recipient_count': 1,
        }
        
        test_notification = self.env['edu.bulk.notification'].create(test_vals)
        
        # Ajouter l'utilisateur actuel comme destinataire
        self.env['edu.notification.recipient'].create({
            'notification_id': test_notification.id,
            'partner_id': self.env.user.partner_id.id,
            'recipient_type': 'user',
            'state': 'pending',
        })
        
        # Envoyer le test
        test_notification.action_send()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test envoyé'),
                'message': _('La notification de test a été envoyée'),
                'type': 'success',
            }
        } 