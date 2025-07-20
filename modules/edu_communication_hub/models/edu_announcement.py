# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _


class EduAnnouncement(models.Model):
    _name = 'edu.announcement'
    _description = 'Annonce éducative'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Titre', required=True, tracking=True)
    content = fields.Html('Contenu', required=True)
    summary = fields.Text('Résumé')
    
    # Statut et visibilité
    active = fields.Boolean('Actif', default=True)
    is_public = fields.Boolean('Public', default=False, 
                              help="Visible sur le portail public")
    is_urgent = fields.Boolean('Urgent', default=False)
    
    # Dates
    start_date = fields.Datetime('Date de début', default=fields.Datetime.now)
    end_date = fields.Datetime('Date de fin')
    
    # Relations
    author_id = fields.Many2one('res.users', 'Auteur', 
                               default=lambda self: self.env.user)
    category_id = fields.Many2one('edu.announcement.category', 'Catégorie')
    
    # Ciblage
    target_groups = fields.Selection([
        ('all', 'Tous'),
        ('students', 'Étudiants'),
        ('parents', 'Parents'),
        ('faculty', 'Enseignants'),
        ('staff', 'Personnel'),
    ], string='Groupes cibles', default='all')
    
    recipient_ids = fields.Many2many('res.partner', 'announcement_recipient_rel',
                                   'announcement_id', 'partner_id', 
                                   string='Destinataires spécifiques')
    
    # Pièces jointes
    attachment_ids = fields.Many2many('ir.attachment', 'announcement_attachment_rel',
                                     'announcement_id', 'attachment_id',
                                     string='Pièces jointes')
    
    # Statistiques
    view_count = fields.Integer('Nombre de vues', default=0)
    
    # Notification
    send_notification = fields.Boolean('Envoyer notification', default=True)
    notification_sent = fields.Boolean('Notification envoyée', default=False)
    
    @api.model
    def create(self, vals):
        """Créer une annonce et envoyer des notifications si nécessaire"""
        announcement = super().create(vals)
        if announcement.send_notification and not announcement.notification_sent:
            announcement._send_notification()
        return announcement

    def _send_notification(self):
        """Envoyer des notifications pour l'annonce"""
        self.ensure_one()
        
        # Préparer le message de notification
        subject = f"Nouvelle annonce: {self.name}"
        body = f"""
        <p>Une nouvelle annonce a été publiée:</p>
        <h3>{self.name}</h3>
        {self.summary or self.content[:200] + '...'}
        """
        
        # Déterminer les destinataires
        recipients = self._get_announcement_recipients()
        
        if recipients:
            # Créer et envoyer le message
            message_vals = {
                'subject': subject,
                'body': body,
                'message_type': 'notification',
                'recipient_ids': [(6, 0, recipients.ids)],
                'announcement_id': self.id,
            }
            
            message = self.env['edu.message'].create(message_vals)
            message.send_message()
            
            self.write({'notification_sent': True})
    
    def _get_announcement_recipients(self):
        """Obtenir la liste des destinataires selon les groupes cibles"""
        recipients = self.env['res.partner']
        
        if self.target_groups == 'all':
            # Tous les utilisateurs actifs
            recipients = self.env['res.users'].search([
                ('active', '=', True)
            ]).mapped('partner_id')
        elif self.target_groups == 'students':
            # Rechercher les étudiants via openeducat_core
            if 'op.student' in self.env:
                students = self.env['op.student'].search([])
                recipients = students.mapped('partner_id')
        elif self.target_groups == 'parents':
            # Rechercher les parents via openeducat_parent
            if 'op.parent' in self.env:
                parents = self.env['op.parent'].search([])
                recipients = parents.mapped('partner_id')
        elif self.target_groups == 'faculty':
            # Rechercher les enseignants via openeducat_core
            if 'op.faculty' in self.env:
                faculty = self.env['op.faculty'].search([])
                recipients = faculty.mapped('partner_id')
        elif self.target_groups == 'staff':
            # Personnel administratif
            staff_group = self.env.ref('base.group_user', False)
            if staff_group:
                recipients = staff_group.users.mapped('partner_id')
        
        # Ajouter les destinataires spécifiques
        if self.recipient_ids:
            recipients |= self.recipient_ids
            
        return recipients


class EduAnnouncementCategory(models.Model):
    _name = 'edu.announcement.category'
    _description = 'Catégorie d\'annonce'
    
    name = fields.Char('Nom', required=True)
    description = fields.Text('Description')
    color = fields.Integer('Couleur', default=1)
    active = fields.Boolean('Actif', default=True)
