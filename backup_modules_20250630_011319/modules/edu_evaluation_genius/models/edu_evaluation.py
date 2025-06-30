# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
import logging

_logger = logging.getLogger(__name__)


class EduEvaluation(models.Model):
    """Évaluation principale"""
    _name = 'edu.evaluation'
    _description = 'Évaluation'
    _order = 'date desc, name'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nom de l\'évaluation',
        required=True,
        tracking=True,
        help="Titre de l'évaluation"
    )
    
    code = fields.Char(
        string='Code',
        size=20,
        help="Code unique de l'évaluation"
    )
    
    description = fields.Text(
        string='Description',
        help="Description détaillée de l'évaluation"
    )
    
    # Informations de base
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Date de l'évaluation"
    )
    
    duration = fields.Float(
        string='Durée (heures)',
        digits=(6, 2),
        help="Durée de l'évaluation en heures"
    )
    
    # Relations principales
    student_id = fields.Many2one(
        'op.student',
        string='Élève',
        required=True,
        index=True
    )
    
    course_id = fields.Many2one(
        'op.course',
        string='Matière',
        required=True,
        index=True
    )
    
    faculty_id = fields.Many2one(
        'op.faculty',
        string='Enseignant',
        required=True,
        tracking=True,
        help="Enseignant évaluateur"
    )
    
    batch_id = fields.Many2one(
        'op.batch',
        string='Groupe',
        index=True,
        help="Groupe/Classe de l'élève"
    )
    
    # Configuration de l'évaluation
    evaluation_type_id = fields.Many2one(
        'edu.evaluation.type',
        string='Type d\'évaluation',
        required=True,
        help="Type d'évaluation (Contrôle, Examen, etc.)"
    )
    
    period_id = fields.Many2one(
        'edu.evaluation.period',
        string='Période',
        required=True,
        help="Période d'évaluation"
    )
    
    grade_scale_id = fields.Many2one(
        'edu.grade.scale',
        string='Barème',
        required=True,
        help="Barème de notation utilisé"
    )
    
    # Notes et évaluation
    grade = fields.Float(
        string='Note',
        digits=(6, 2),
        tracking=True,
        help="Note obtenue"
    )
    
    max_grade = fields.Float(
        string='Note maximale',
        digits=(6, 2),
        help="Note maximale possible"
    )
    
    coefficient = fields.Float(
        string='Coefficient',
        default=1.0,
        digits=(6, 2),
        required=True,
        help="Coefficient de l'évaluation"
    )
    
    grade_percentage = fields.Float(
        string='Pourcentage',
        compute='_compute_grade_percentage',
        store=True,
        digits=(5, 2),
        help="Note en pourcentage"
    )
    
    grade_letter = fields.Char(
        string='Note lettre',
        compute='_compute_grade_letter',
        store=True,
        help="Note convertie en lettre"
    )
    
    # Évaluation détaillée par critères
    evaluation_line_ids = fields.One2many(
        'edu.evaluation.line',
        'evaluation_id',
        string='Détail par critères'
    )
    
    # Commentaires et observations
    comment = fields.Text(
        string='Commentaire',
        help="Commentaire de l'enseignant"
    )
    
    private_comment = fields.Text(
        string='Commentaire privé',
        help="Commentaire privé (non visible par l'élève/parents)"
    )
    
    recommendations = fields.Text(
        string='Recommandations',
        help="Recommandations pour l'élève"
    )
    
    # État et workflow
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('published', 'Publié'),
        ('archived', 'Archivé')
    ], string='État', default='draft', tracking=True)
    
    # Flags
    is_absent = fields.Boolean(
        string='Absent',
        default=False,
        tracking=True,
        help="L'élève était absent"
    )
    
    is_excused = fields.Boolean(
        string='Excusé',
        default=False,
        help="Absence excusée"
    )
    
    is_retake = fields.Boolean(
        string='Rattrapage',
        default=False,
        help="Il s'agit d'un rattrapage"
    )
    
    original_evaluation_id = fields.Many2one(
        'edu.evaluation',
        string='Évaluation originale',
        help="Évaluation originale en cas de rattrapage"
    )
    
    retake_count = fields.Integer(
        string='Nombre de rattrapages',
        default=0,
        help="Nombre de fois que l'évaluation a été refaite"
    )
    
    # Métadonnées
    created_date = fields.Datetime(
        string='Date de création',
        default=fields.Datetime.now,
        readonly=True
    )
    
    confirmed_date = fields.Datetime(
        string='Date de confirmation',
        readonly=True
    )
    
    published_date = fields.Datetime(
        string='Date de publication',
        readonly=True
    )
    
    # Calculs et statistiques
    @api.depends('grade', 'max_grade')
    def _compute_grade_percentage(self):
        """Calcule le pourcentage"""
        for record in self:
            if record.max_grade and record.max_grade > 0:
                record.grade_percentage = (record.grade / record.max_grade) * 100
            else:
                record.grade_percentage = 0.0
    
    @api.depends('grade', 'grade_scale_id')
    def _compute_grade_letter(self):
        """Calcule la note lettre selon le barème"""
        for record in self:
            if record.grade_scale_id and record.grade is not False:
                record.grade_letter = record.grade_scale_id.format_grade(record.grade)
            else:
                record.grade_letter = ""
    
    # Contraintes
    @api.constrains('grade', 'max_grade')
    def _check_grade_range(self):
        """Vérifie que la note est dans la plage autorisée"""
        for record in self:
            if record.grade is not False and record.max_grade:
                if record.grade < 0 or record.grade > record.max_grade:
                    raise ValidationError(_("La note doit être entre 0 et %s") % record.max_grade)
    
    @api.constrains('coefficient')
    def _check_coefficient(self):
        """Vérifie que le coefficient est positif"""
        for record in self:
            if record.coefficient <= 0:
                raise ValidationError(_("Le coefficient doit être supérieur à 0"))
    
    @api.constrains('date', 'period_id')
    def _check_date_in_period(self):
        """Vérifie que la date est dans la période"""
        for record in self:
            if record.period_id and record.date:
                if not (record.period_id.start_date <= record.date <= record.period_id.end_date):
                    raise ValidationError(_(
                        "La date de l'évaluation doit être dans la période sélectionnée (%s - %s)"
                    ) % (record.period_id.start_date, record.period_id.end_date))
    
    @api.constrains('student_id', 'batch_id')
    def _check_student_in_batch(self):
        """Vérifie que l'élève appartient à la classe"""
        for record in self:
            if record.student_id and record.batch_id:
                if record.batch_id not in record.student_id.course_detail_ids.mapped('batch_id'):
                    raise ValidationError(_("L'élève n'appartient pas à cette classe"))
    
    # Méthodes onchange
    @api.onchange('evaluation_type_id')
    def _onchange_evaluation_type(self):
        """Met à jour les valeurs par défaut selon le type"""
        if self.evaluation_type_id:
            self.coefficient = self.evaluation_type_id.coefficient
            self.duration = self.evaluation_type_id.duration
    
    @api.onchange('grade_scale_id')
    def _onchange_grade_scale(self):
        """Met à jour la note max selon le barème"""
        if self.grade_scale_id:
            self.max_grade = self.grade_scale_id.max_value
    
    @api.onchange('student_id')
    def _onchange_student(self):
        """Met à jour la classe selon l'élève"""
        if self.student_id:
            course_detail = self.student_id.course_detail_ids.filtered(
                lambda x: x.state == 'running'
            )[:1]
            if course_detail:
                self.batch_id = course_detail.batch_id
    
    # Actions du workflow
    def action_confirm(self):
        """Confirme l'évaluation"""
        for record in self:
            if record.state == 'draft':
                record.state = 'confirmed'
                record.confirmed_date = fields.Datetime.now()
    
    def action_publish(self):
        """Publie l'évaluation (visible par élève/parents)"""
        for record in self:
            if record.state == 'confirmed':
                record.state = 'published'
                record.published_date = fields.Datetime.now()
                # TODO: Envoyer notification
    
    def action_archive(self):
        """Archive l'évaluation"""
        for record in self:
            if record.state in ['confirmed', 'published']:
                record.state = 'archived'
    
    def action_back_to_draft(self):
        """Remet en brouillon"""
        for record in self:
            if record.state in ['confirmed', 'published']:
                record.state = 'draft'
                record.confirmed_date = False
                record.published_date = False
    
    def action_create_retake(self):
        """Crée une évaluation de rattrapage"""
        self.ensure_one()
        if not self.evaluation_type_id.allow_retake:
            raise UserError(_("Le rattrapage n'est pas autorisé pour ce type d'évaluation"))
        
        if self.retake_count >= self.evaluation_type_id.max_retakes:
            raise UserError(_("Nombre maximum de rattrapages atteint"))
        
        retake = self.copy({
            'name': f"{self.name} - Rattrapage {self.retake_count + 1}",
            'is_retake': True,
            'original_evaluation_id': self.id,
            'state': 'draft',
            'grade': 0.0,
            'comment': '',
            'private_comment': '',
            'recommendations': ''
        })
        
        self.retake_count += 1
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rattrapage'),
            'res_model': 'edu.evaluation',
            'res_id': retake.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    # Méthodes utilitaires
    def get_grade_color(self):
        """Retourne la couleur selon la performance"""
        self.ensure_one()
        if self.grade_scale_id:
            return self.grade_scale_id.get_grade_color(self.grade)
        return 'muted'
    
    def is_passed(self):
        """Vérifie si l'évaluation est réussie"""
        self.ensure_one()
        if self.grade_scale_id and self.grade is not False:
            return self.grade >= self.grade_scale_id.pass_mark
        return False
    
    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = record.name
            if record.student_id and record.course_id:
                name = f"{record.name} - {record.student_id.name} ({record.course_id.name})"
            result.append((record.id, name))
        return result
    
    @api.model
    def create(self, vals):
        """Génère automatiquement un code si non fourni"""
        if not vals.get('code'):
            sequence = self.env['ir.sequence'].next_by_code('edu.evaluation') or '/'
            vals['code'] = sequence
        return super().create(vals)


class EduEvaluationLine(models.Model):
    """Lignes d'évaluation détaillée par critères"""
    _name = 'edu.evaluation.line'
    _description = 'Ligne d\'évaluation'
    _order = 'evaluation_id, sequence, criteria_id'
    _rec_name = 'criteria_id'

    evaluation_id = fields.Many2one(
        'edu.evaluation',
        string='Évaluation',
        required=True,
        ondelete='cascade'
    )
    
    criteria_id = fields.Many2one(
        'edu.evaluation.criteria',
        string='Critère',
        required=True,
        help="Critère d'évaluation"
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10
    )
    
    # Notes
    points = fields.Float(
        string='Points obtenus',
        digits=(6, 2),
        required=True,
        default=0.0,
        help="Points obtenus pour ce critère"
    )
    
    max_points = fields.Float(
        string='Points maximum',
        digits=(6, 2),
        related='criteria_id.max_points',
        store=True,
        help="Points maximum pour ce critère"
    )
    
    percentage = fields.Float(
        string='Pourcentage',
        compute='_compute_percentage',
        store=True,
        digits=(5, 2)
    )
    
    # Rubrique
    rubric_level_id = fields.Many2one(
        'edu.criteria.rubric.level',
        string='Niveau',
        domain="[('criteria_id', '=', criteria_id)]",
        help="Niveau de performance atteint"
    )
    
    # Commentaires
    comment = fields.Text(
        string='Commentaire',
        help="Commentaire spécifique à ce critère"
    )
    
    @api.depends('points', 'max_points')
    def _compute_percentage(self):
        """Calcule le pourcentage pour ce critère"""
        for record in self:
            if record.max_points and record.max_points > 0:
                record.percentage = (record.points / record.max_points) * 100
            else:
                record.percentage = 0.0
    
    @api.constrains('points', 'max_points')
    def _check_points_range(self):
        """Vérifie que les points sont dans la plage"""
        for record in self:
            if record.points < 0 or record.points > record.max_points:
                raise ValidationError(_(
                    "Les points doivent être entre 0 et %s"
                ) % record.max_points)
    
    @api.onchange('rubric_level_id')
    def _onchange_rubric_level(self):
        """Met à jour les points selon le niveau sélectionné"""
        if self.rubric_level_id:
            self.points = self.rubric_level_id.points
