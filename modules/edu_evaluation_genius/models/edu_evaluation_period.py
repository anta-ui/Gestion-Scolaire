# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class EduEvaluationPeriod(models.Model):
    """Périodes d'évaluation (Trimestre, Semestre, etc.)"""
    _name = 'edu.evaluation.period'
    _description = 'Période d\'évaluation'
    _order = 'academic_year_id, sequence, start_date'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom de la période',
        required=True,
        translate=True,
        help="Ex: 1er Trimestre, 2ème Semestre"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=10,
        help="Code court de la période"
    )
    
    description = fields.Text(
        string='Description',
        translate=True
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre dans l'année scolaire"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    # Dates
    start_date = fields.Date(
        string='Date de début',
        required=True,
        help="Date de début de la période"
    )
    
    end_date = fields.Date(
        string='Date de fin',
        required=True,
        help="Date de fin de la période"
    )
    
    # Dates limites pour les évaluations
    evaluation_start_date = fields.Date(
        string='Début des évaluations',
        help="Date à partir de laquelle les évaluations peuvent être saisies"
    )
    
    evaluation_end_date = fields.Date(
        string='Fin des évaluations',
        help="Date limite pour saisir les évaluations"
    )
    
    # Dates pour les bulletins
    report_card_date = fields.Date(
        string='Date d\'édition des bulletins',
        help="Date prévue pour l'édition des bulletins"
    )
    
    report_card_deadline = fields.Date(
        string='Date limite bulletins',
        help="Date limite pour finaliser les bulletins"
    )
    
    # Configuration
    period_type = fields.Selection([
        ('trimester', 'Trimestre'),
        ('semester', 'Semestre'),
        ('quarter', 'Quadrimestre'),
        ('month', 'Mensuel'),
        ('week', 'Hebdomadaire'),
        ('custom', 'Personnalisé')
    ], string='Type de période', required=True, default='trimester')
    
    academic_year_id = fields.Many2one(
        'op.academic.year',
        string='Année scolaire',
        required=True,
        help="Année scolaire de rattachement"
    )
    
    academic_term_id = fields.Many2one(
        'op.academic.term',
        string='Terme académique',
        help="Terme académique si applicable"
    )
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('open', 'Ouvert'),
        ('evaluation', 'Évaluations en cours'),
        ('closed', 'Fermé'),
        ('archived', 'Archivé')
    ], string='État', default='draft', tracking=True)
    
    # Configuration des coefficients
    coefficient = fields.Float(
        string='Coefficient',
        default=1.0,
        digits=(6, 2),
        help="Coefficient de la période dans l'année"
    )
    
    include_in_annual_average = fields.Boolean(
        string='Inclure dans la moyenne annuelle',
        default=True,
        help="Cette période compte pour la moyenne annuelle"
    )
    
    # Paramètres d'évaluation
    allow_late_evaluations = fields.Boolean(
        string='Évaluations tardives autorisées',
        default=False,
        help="Permet de saisir des évaluations après la date limite"
    )
    
    auto_close_evaluations = fields.Boolean(
        string='Fermeture automatique',
        default=True,
        help="Ferme automatiquement les évaluations à la date limite"
    )
    
    # Statistiques
    evaluation_count = fields.Integer(
        string='Nombre d\'évaluations',
        compute='_compute_evaluation_count'
    )
    
    student_count = fields.Integer(
        string='Nombre d\'élèves évalués',
        compute='_compute_student_count'
    )
    
    completion_rate = fields.Float(
        string='Taux de completion (%)',
        compute='_compute_completion_rate',
        digits=(5, 2)
    )
    
    # Calculs
    def _compute_evaluation_count(self):
        """Calcule le nombre d'évaluations dans cette période"""
        for record in self:
            record.evaluation_count = self.env['edu.evaluation'].search_count([
                ('period_id', '=', record.id)
            ])
    
    def _compute_student_count(self):
        """Calcule le nombre d'élèves ayant des évaluations"""
        for record in self:
            evaluations = self.env['edu.evaluation'].search([
                ('period_id', '=', record.id)
            ])
            students = evaluations.mapped('student_id')
            record.student_count = len(students)
    
    def _compute_completion_rate(self):
        """Calcule le taux de completion des évaluations"""
        for record in self:
            total_evaluations = record.evaluation_count
            if total_evaluations == 0:
                record.completion_rate = 0.0
            else:
                completed_evaluations = self.env['edu.evaluation'].search_count([
                    ('period_id', '=', record.id),
                    ('state', '=', 'confirmed')
                ])
                record.completion_rate = (completed_evaluations / total_evaluations) * 100
    
    # Contraintes
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Vérifie la cohérence des dates"""
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date >= record.end_date:
                    raise ValidationError(_("La date de début doit être antérieure à la date de fin"))
    
    @api.constrains('evaluation_start_date', 'evaluation_end_date', 'start_date', 'end_date')
    def _check_evaluation_dates(self):
        """Vérifie les dates d'évaluation"""
        for record in self:
            if record.evaluation_start_date and record.start_date:
                if record.evaluation_start_date < record.start_date:
                    raise ValidationError(_("La date de début des évaluations ne peut pas être antérieure au début de la période"))
            
            if record.evaluation_end_date and record.end_date:
                if record.evaluation_end_date > record.end_date:
                    raise ValidationError(_("La date de fin des évaluations ne peut pas être postérieure à la fin de la période"))
            
            if record.evaluation_start_date and record.evaluation_end_date:
                if record.evaluation_start_date >= record.evaluation_end_date:
                    raise ValidationError(_("La date de début des évaluations doit être antérieure à la date de fin"))
    
    @api.constrains('coefficient')
    def _check_coefficient(self):
        """Vérifie que le coefficient est positif"""
        for record in self:
            if record.coefficient <= 0:
                raise ValidationError(_("Le coefficient doit être supérieur à 0"))
    
    @api.constrains('code', 'academic_year_id')
    def _check_unique_code_per_year(self):
        """Vérifie l'unicité du code par année scolaire"""
        for record in self:
            existing = self.search([
                ('code', '=', record.code),
                ('academic_year_id', '=', record.academic_year_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_("Le code '%s' existe déjà pour cette année scolaire") % record.code)
    
    # Actions
    def action_open(self):
        """Ouvre la période pour les évaluations"""
        self.ensure_one()
        if self.state == 'draft':
            self.state = 'open'
    
    def action_start_evaluations(self):
        """Démarre les évaluations"""
        self.ensure_one()
        if self.state == 'open':
            self.state = 'evaluation'
    
    def action_close(self):
        """Ferme la période"""
        self.ensure_one()
        if self.state in ['open', 'evaluation']:
            self.state = 'closed'
    
    def action_archive(self):
        """Archive la période"""
        self.ensure_one()
        if self.state == 'closed':
            self.state = 'archived'
    
    def action_reopen(self):
        """Réouvre la période"""
        self.ensure_one()
        if self.state in ['closed', 'archived']:
            self.state = 'evaluation'
    
    # Méthodes utilitaires
    @api.model
    def get_current_period(self, academic_year_id=None):
        """Retourne la période courante"""
        today = date.today()
        domain = [
            ('start_date', '<=', today),
            ('end_date', '>=', today),
            ('state', 'in', ['open', 'evaluation'])
        ]
        if academic_year_id:
            domain.append(('academic_year_id', '=', academic_year_id))
        
        return self.search(domain, limit=1)
    
    def is_evaluation_allowed(self):
        """Vérifie si les évaluations sont autorisées"""
        self.ensure_one()
        today = date.today()
        
        if self.state not in ['open', 'evaluation']:
            return False
        
        if self.evaluation_start_date and today < self.evaluation_start_date:
            return False
        
        if self.evaluation_end_date and today > self.evaluation_end_date:
            return self.allow_late_evaluations
        
        return True
    
    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            if record.academic_year_id:
                name += f" ({record.academic_year_id.name})"
            result.append((record.id, name))
        return result
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Recherche par nom ou code"""
        args = args or []
        if name:
            args = ['|', ('name', operator, name), ('code', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
    
    def action_view_evaluations(self):
        """Action pour voir les évaluations de cette période"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Évaluations - %s') % self.name,
            'res_model': 'edu.evaluation',
            'view_mode': 'tree,form',
            'domain': [('period_id', '=', self.id)],
            'context': {'default_period_id': self.id},
        }
    
    def action_view_students(self):
        """Action pour voir les étudiants évalués dans cette période"""
        self.ensure_one()
        evaluations = self.env['edu.evaluation'].search([('period_id', '=', self.id)])
        student_ids = evaluations.mapped('student_id').ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Étudiants évalués - %s') % self.name,
            'res_model': 'op.student',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', student_ids)],
        }
