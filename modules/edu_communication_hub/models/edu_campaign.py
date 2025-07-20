# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta


class EduCampaign(models.Model):
    _name = 'edu.campaign'
    _description = 'Campagne de communication'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char('Nom de la campagne', required=True, tracking=True)
    description = fields.Text('Description')
    
    # Statut de la campagne
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('scheduled', 'Programmée'),
        ('running', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
    ], string='Statut', default='draft', tracking=True)
    
    # Configuration de la campagne
    campaign_type = fields.Selection([
        ('one_time', 'Unique'),
        ('recurring', 'Récurrente'),
        ('automated', 'Automatisée'),
    ], string='Type', default='one_time', required=True)
    
    # Dates et planification
    start_date = fields.Datetime('Date de début', required=True)
    end_date = fields.Datetime('Date de fin')
    send_date = fields.Datetime('Date d\'envoi')
    
    # Récurrence (pour les campagnes récurrentes)
    recurrence_type = fields.Selection([
        ('daily', 'Quotidienne'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuelle'),
        ('yearly', 'Annuelle'),
    ], string='Type de récurrence')
    
    recurrence_interval = fields.Integer('Intervalle', default=1,
                                       help="Tous les X jours/semaines/mois/années")
    
    # Contenu de la campagne
    template_id = fields.Many2one('edu.message.template', 'Template de message')
    subject = fields.Char('Sujet')
    body = fields.Html('Corps du message')
    
    # Configuration d'envoi
    message_type = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Notification Push'),
        ('mixed', 'Mixte'),
    ], string='Type de message', default='email')
    
    # Destinataires
    target_audience = fields.Selection([
        ('all', 'Tous'),
        ('students', 'Étudiants'),
        ('parents', 'Parents'),
        ('faculty', 'Enseignants'),
        ('staff', 'Personnel'),
        ('custom', 'Personnalisé'),
    ], string='Audience cible', default='all')
    
    recipient_ids = fields.Many2many('res.partner', 'campaign_recipient_rel',
                                   'campaign_id', 'partner_id',
                                   string='Destinataires')
    
    # Filtres avancés
    student_course_ids = fields.Many2many('op.course', 'campaign_course_rel',
                                        'campaign_id', 'course_id',
                                        string='Cours d\'étudiants')
    
    student_batch_ids = fields.Many2many('op.batch', 'campaign_batch_rel',
                                       'campaign_id', 'batch_id',
                                       string='Groupes d\'étudiants')
    
    # Statistiques
    total_recipients = fields.Integer('Total destinataires', compute='_compute_stats')
    messages_sent = fields.Integer('Messages envoyés', default=0)
    messages_delivered = fields.Integer('Messages délivrés', default=0)
    messages_opened = fields.Integer('Messages ouverts', default=0)
    messages_clicked = fields.Integer('Messages cliqués', default=0)
    
    # Taux de succès
    delivery_rate = fields.Float('Taux de livraison (%)', compute='_compute_rates')
    open_rate = fields.Float('Taux d\'ouverture (%)', compute='_compute_rates')
    click_rate = fields.Float('Taux de clic (%)', compute='_compute_rates')
    
    # Messages liés
    message_ids = fields.One2many('edu.message', 'campaign_id', 'Messages')
    
    @api.depends('recipient_ids', 'target_audience')
    def _compute_stats(self):
        """Calculer les statistiques de la campagne"""
        for campaign in self:
            if campaign.target_audience == 'custom':
                campaign.total_recipients = len(campaign.recipient_ids)
            else:
                recipients = campaign._get_target_recipients()
                campaign.total_recipients = len(recipients)
    
    @api.depends('messages_sent', 'messages_delivered', 'messages_opened', 'messages_clicked')
    def _compute_rates(self):
        """Calculer les taux de succès"""
        for campaign in self:
            if campaign.messages_sent > 0:
                campaign.delivery_rate = (campaign.messages_delivered / campaign.messages_sent) * 100
                campaign.open_rate = (campaign.messages_opened / campaign.messages_sent) * 100
                campaign.click_rate = (campaign.messages_clicked / campaign.messages_sent) * 100
            else:
                campaign.delivery_rate = 0
                campaign.open_rate = 0
                campaign.click_rate = 0
    
    def _get_target_recipients(self):
        """Obtenir les destinataires selon l'audience cible"""
        recipients = self.env['res.partner']
        
        if self.target_audience == 'students':
            if 'op.student' in self.env:
                students = self.env['op.student'].search([])
                if self.student_course_ids:
                    students = students.filtered(lambda s: s.course_detail_ids.course_id in self.student_course_ids)
                if self.student_batch_ids:
                    students = students.filtered(lambda s: s.course_detail_ids.batch_id in self.student_batch_ids)
                recipients = students.mapped('partner_id')
        elif self.target_audience == 'parents':
            if 'op.parent' in self.env:
                parents = self.env['op.parent'].search([])
                recipients = parents.mapped('partner_id')
        elif self.target_audience == 'faculty':
            if 'op.faculty' in self.env:
                faculty = self.env['op.faculty'].search([])
                recipients = faculty.mapped('partner_id')
        elif self.target_audience == 'staff':
            # Personnel administratif
            staff_group = self.env.ref('base.group_user', False)
            if staff_group:
                recipients = staff_group.users.mapped('partner_id')
        elif self.target_audience == 'all':
            recipients = self.env['res.users'].search([('active', '=', True)]).mapped('partner_id')
        elif self.target_audience == 'custom':
            recipients = self.recipient_ids
        
        return recipients
    
    def action_schedule(self):
        """Programmer la campagne"""
        self.ensure_one()
        self.write({'state': 'scheduled'})
        
        # Créer une tâche cron pour la campagne si nécessaire
        if self.campaign_type == 'recurring':
            self._create_recurring_cron()
    
    def action_start(self):
        """Démarrer la campagne"""
        self.ensure_one()
        self.write({'state': 'running'})
        
        # Envoyer les messages
        self._send_campaign_messages()
    
    def action_cancel(self):
        """Annuler la campagne"""
        self.ensure_one()
        self.write({'state': 'cancelled'})
    
    def _send_campaign_messages(self):
        """Envoyer les messages de la campagne"""
        self.ensure_one()
        
        recipients = self._get_target_recipients()
        
        if not recipients:
            return
        
        # Préparer le contenu du message
        subject = self.subject
        body = self.body
        
        # Utiliser le template si défini
        if self.template_id:
            template_data = self.template_id.use_template()
            subject = template_data.get('subject', subject)
            body = template_data.get('body_html', body)
        
        # Créer le message
        message_vals = {
            'subject': subject,
            'body': body,
            'message_type': self.message_type,
            'campaign_id': self.id,
            'recipient_ids': [(6, 0, recipients.ids)],
        }
        
        message = self.env['edu.message'].create(message_vals)
        message.send_message()
        
        # Mettre à jour les statistiques
        self.write({
            'messages_sent': len(recipients),
            'state': 'completed' if self.campaign_type == 'one_time' else 'running',
        })
    
    def _create_recurring_cron(self):
        """Créer une tâche cron pour les campagnes récurrentes"""
        # Implémentation de la tâche cron récurrente
        pass
