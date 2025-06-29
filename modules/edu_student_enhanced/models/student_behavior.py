# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class StudentBehaviorRecord(models.Model):
    """Enregistrements comportementaux des élèves"""
    _name = 'student.behavior.record'
    _description = 'Historique Comportemental'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char('Référence', compute='_compute_name', store=True)
    student_id = fields.Many2one('op.student', string='Élève', required=True, ondelete='cascade')
    date = fields.Date('Date', default=fields.Date.context_today, required=True)
    type = fields.Selection([
        ('reward', '🌟 Récompense'),
        ('sanction', '⚠️ Sanction')
    ], string='Type', required=True)
    
    category_id = fields.Many2one('student.behavior.category', string='Catégorie')
    points = fields.Integer('Points', default=0)
    description = fields.Text('Description', required=True)
    
    teacher_id = fields.Many2one('op.faculty', string='Enseignant')
    location = fields.Char('Lieu')
    witnesses = fields.Char('Témoins')
    
    actions_taken = fields.Text('Actions Prises')
    followup_notes = fields.Text('Notes de Suivi')
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('done', 'Terminé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    
    @api.depends('student_id', 'date', 'type')
    def _compute_name(self):
        for record in self:
            if record.student_id and record.date:
                record.name = f"{record.type.title()} - {record.student_id.name} - {record.date}"
            else:
                record.name = "Nouveau"
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_done(self):
        self.write({'state': 'done'})
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
    
    def action_draft(self):
        self.write({'state': 'draft'})

class StudentBehaviorCategory(models.Model):
    """Catégories de comportements"""
    _name = 'student.behavior.category'
    _description = 'Catégorie de Comportement'
    _order = 'sequence, name'
    
    name = fields.Char('Nom', required=True)
    code = fields.Char('Code')
    type = fields.Selection([
        ('reward', 'Récompense'),
        ('sanction', 'Sanction')
    ], string='Type', required=True)
    points = fields.Integer('Points par Défaut')
    sequence = fields.Integer('Séquence', default=10)
    description = fields.Text('Description')
    active = fields.Boolean('Actif', default=True)
    
    # Statistiques
    record_count = fields.Integer('Nombre d\'Enregistrements', compute='_compute_record_count')
    
    @api.depends()
    def _compute_record_count(self):
        """Calculer le nombre d'enregistrements dans cette catégorie"""
        for category in self:
            category.record_count = self.env['student.behavior.record'].search_count([
                ('category_id', '=', category.id)
            ])
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Le code de la catégorie doit être unique.'),
    ]

class StudentReward(models.Model):
    """Système de récompenses et badges"""
    _name = 'student.reward'
    _description = 'Récompense Élève'
    _rec_name = 'title'
    
    student_id = fields.Many2one('op.student', string='Élève', required=True, ondelete='cascade')
    reward_type_id = fields.Many2one('student.reward.type', string='Type de Récompense', required=True)
    
    title = fields.Char('Titre', required=True)
    description = fields.Text('Description')
    points_earned = fields.Integer('Points Gagnés', required=True)
    
    date_earned = fields.Date('Date d\'Obtention', default=fields.Date.today)
    awarded_by = fields.Many2one('res.users', string='Attribué par', default=lambda self: self.env.user)
    
    badge_image = fields.Binary('Image du Badge', related='reward_type_id.badge_image')
    certificate = fields.Binary('Certificat', attachment=True)
    
    is_public = fields.Boolean('Public', default=True, help="Visible par les autres élèves")
    level = fields.Selection([
        ('bronze', '🥉 Bronze'),
        ('silver', '🥈 Argent'),
        ('gold', '🥇 Or'),
        ('platinum', '💎 Platine')
    ], string='Niveau', default='bronze')

class StudentRewardType(models.Model):
    """Types de récompenses"""
    _name = 'student.reward.type'
    _description = 'Type de Récompense'
    
    name = fields.Char('Nom', required=True)
    description = fields.Text('Description')
    badge_image = fields.Binary('Image du Badge', attachment=True)
    icon = fields.Char('Icône')
    
    points_required = fields.Integer('Points Requis', help="Points minimum pour obtenir cette récompense")
    is_automatic = fields.Boolean('Attribution Automatique', help="Attribué automatiquement quand les conditions sont remplies")
    
    criteria = fields.Text('Critères d\'Attribution')
    color = fields.Integer('Couleur', default=5)
    active = fields.Boolean('Actif', default=True)

class BehaviorFollowupWizard(models.TransientModel):
    """Assistant pour programmer un suivi comportemental"""
    _name = 'behavior.followup.wizard'
    _description = 'Assistant Suivi Comportemental'
    
    behavior_record_id = fields.Many2one('student.behavior.record', string='Enregistrement')
    followup_date = fields.Date('Date de Suivi', required=True, default=lambda self: fields.Date.today() + timedelta(days=7))
    followup_type = fields.Selection([
        ('meeting', 'Réunion'),
        ('observation', 'Observation'),
        ('evaluation', 'Évaluation'),
        ('counseling', 'Accompagnement')
    ], string='Type de Suivi', required=True)
    
    notes = fields.Text('Notes')
    assign_to = fields.Many2one('res.users', string='Assigné à')
    
    def action_schedule(self):
        """Programmer le suivi"""
        if self.behavior_record_id:
            self.behavior_record_id.write({
                'follow_up_required': True,
                'follow_up_date': self.followup_date,
                'follow_up_notes': self.notes
            })
        
        # Créer une activité de suivi
        self.env['mail.activity'].create({
            'activity_type_id': self.env.ref('mail.mail_activity_data_meeting').id,
            'summary': f'Suivi comportemental - {self.behavior_record_id.student_name}',
            'note': self.notes,
            'date_deadline': self.followup_date,
            'user_id': self.assign_to.id or self.env.user.id,
            'res_model_id': self.env.ref('edu_student_enhanced.model_student_behavior_record').id,
            'res_id': self.behavior_record_id.id,
        })
        
        return {'type': 'ir.actions.act_window_close'}
