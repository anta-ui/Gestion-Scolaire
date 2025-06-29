# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class EduCompetencyEvaluation(models.Model):
    """Évaluation des compétences"""
    _name = 'edu.competency.evaluation'
    _description = 'Évaluation de compétence'
    _order = 'evaluation_id, competency_id'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Nom',
        compute='_compute_display_name',
        store=True
    )
    
    # Relations principales
    evaluation_id = fields.Many2one(
        'edu.evaluation',
        string='Évaluation',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    competency_id = fields.Many2one(
        'edu.competency',
        string='Compétence',
        required=True,
        index=True
    )
    
    # Informations dérivées de l'évaluation
    student_id = fields.Many2one(
        'op.student',
        string='Élève',
        related='evaluation_id.student_id',
        store=True,
        readonly=True
    )
    
    course_id = fields.Many2one(
        'op.course',
        string='Matière',
        related='evaluation_id.course_id',
        store=True,
        readonly=True
    )
    
    period_id = fields.Many2one(
        'edu.evaluation.period',
        string='Période',
        related='evaluation_id.period_id',
        store=True,
        readonly=True
    )
    
    evaluation_date = fields.Date(
        string='Date d\'évaluation',
        related='evaluation_id.date',
        store=True,
        readonly=True
    )
    
    # Évaluation de la compétence
    mastery_level_id = fields.Many2one(
        'edu.competency.mastery.level',
        string='Niveau de maîtrise',
        domain="[('competency_id', '=', competency_id)]",
        help="Niveau de maîtrise atteint pour cette compétence"
    )
    
    score = fields.Float(
        string='Score',
        digits=(6, 2),
        help="Score obtenu pour cette compétence"
    )
    
    max_score = fields.Float(
        string='Score maximum',
        digits=(6, 2),
        help="Score maximum possible pour cette compétence"
    )
    
    percentage = fields.Float(
        string='Pourcentage',
        compute='_compute_percentage',
        store=True,
        digits=(5, 2)
    )
    
    # Pondération
    weight = fields.Float(
        string='Poids',
        default=1.0,
        digits=(6, 2),
        help="Poids de cette compétence dans l'évaluation"
    )
    
    coefficient = fields.Float(
        string='Coefficient',
        related='competency_id.coefficient',
        store=True,
        readonly=True
    )
    
    # Évaluation qualitative
    mastery_level_text = fields.Selection([
        ('insufficient', 'Insuffisant'),
        ('beginner', 'Débutant'),
        ('developing', 'En cours d\'acquisition'),
        ('proficient', 'Maîtrisé'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert')
    ], string='Niveau de maîtrise', compute='_compute_mastery_level_text', store=True)
    
    # Commentaires
    comment = fields.Text(
        string='Commentaire',
        help="Commentaire spécifique à cette compétence"
    )
    
    teacher_observation = fields.Text(
        string='Observation de l\'enseignant',
        help="Observation détaillée de l'enseignant"
    )
    
    # Indicateurs de performance
    is_key_competency = fields.Boolean(
        string='Compétence clé',
        related='competency_id.is_key_competency',
        store=True,
        readonly=True
    )
    
    is_acquired = fields.Boolean(
        string='Acquise',
        compute='_compute_acquisition_status',
        store=True,
        help="La compétence est-elle considérée comme acquise ?"
    )
    
    needs_reinforcement = fields.Boolean(
        string='À renforcer',
        default=False,
        help="Cette compétence nécessite-t-elle un renforcement ?"
    )
    
    # Progression
    previous_evaluation_id = fields.Many2one(
        'edu.competency.evaluation',
        string='Évaluation précédente',
        compute='_compute_previous_evaluation',
        store=True
    )
    
    progress = fields.Float(
        string='Progression',
        compute='_compute_progress',
        store=True,
        digits=(5, 2),
        help="Progression depuis la dernière évaluation"
    )
    
    # Métadonnées
    sequence = fields.Integer(
        string='Séquence',
        default=10
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    @api.depends('evaluation_id', 'competency_id')
    def _compute_display_name(self):
        """Calcule le nom d'affichage"""
        for record in self:
            if record.evaluation_id and record.competency_id:
                record.display_name = f"{record.evaluation_id.name} - {record.competency_id.name}"
            else:
                record.display_name = "Évaluation de compétence"
    
    @api.depends('score', 'max_score')
    def _compute_percentage(self):
        """Calcule le pourcentage"""
        for record in self:
            if record.max_score and record.max_score > 0:
                record.percentage = (record.score / record.max_score) * 100
            else:
                record.percentage = 0
    
    @api.depends('percentage', 'mastery_level_id')
    def _compute_mastery_level_text(self):
        """Détermine le niveau de maîtrise textuel"""
        for record in self:
            if record.mastery_level_id:
                # Utiliser le niveau défini manuellement
                if record.mastery_level_id.name:
                    if 'expert' in record.mastery_level_id.name.lower():
                        record.mastery_level_text = 'expert'
                    elif 'avancé' in record.mastery_level_id.name.lower():
                        record.mastery_level_text = 'advanced'
                    elif 'maîtrisé' in record.mastery_level_id.name.lower():
                        record.mastery_level_text = 'proficient'
                    elif 'cours' in record.mastery_level_id.name.lower():
                        record.mastery_level_text = 'developing'
                    elif 'débutant' in record.mastery_level_id.name.lower():
                        record.mastery_level_text = 'beginner'
                    else:
                        record.mastery_level_text = 'insufficient'
                else:
                    record.mastery_level_text = 'insufficient'
            else:
                # Calculer automatiquement basé sur le pourcentage
                percentage = record.percentage
                if percentage >= 90:
                    record.mastery_level_text = 'expert'
                elif percentage >= 80:
                    record.mastery_level_text = 'advanced'
                elif percentage >= 70:
                    record.mastery_level_text = 'proficient'
                elif percentage >= 60:
                    record.mastery_level_text = 'developing'
                elif percentage >= 40:
                    record.mastery_level_text = 'beginner'
                else:
                    record.mastery_level_text = 'insufficient'
    
    @api.depends('percentage', 'mastery_level_text')
    def _compute_acquisition_status(self):
        """Détermine si la compétence est acquise"""
        for record in self:
            # Seuil d'acquisition : 70% ou niveau "Maîtrisé" ou plus
            record.is_acquired = (
                record.percentage >= 70 or 
                record.mastery_level_text in ['proficient', 'advanced', 'expert']
            )
    
    @api.depends('student_id', 'competency_id', 'evaluation_date')
    def _compute_previous_evaluation(self):
        """Trouve l'évaluation précédente de cette compétence pour cet élève"""
        for record in self:
            if record.student_id and record.competency_id and record.evaluation_date:
                previous = self.search([
                    ('student_id', '=', record.student_id.id),
                    ('competency_id', '=', record.competency_id.id),
                    ('evaluation_date', '<', record.evaluation_date),
                    ('id', '!=', record.id)
                ], order='evaluation_date desc', limit=1)
                record.previous_evaluation_id = previous.id if previous else False
            else:
                record.previous_evaluation_id = False
    
    @api.depends('percentage', 'previous_evaluation_id')
    def _compute_progress(self):
        """Calcule la progression"""
        for record in self:
            if record.previous_evaluation_id:
                record.progress = record.percentage - record.previous_evaluation_id.percentage
            else:
                record.progress = 0
    
    @api.constrains('score', 'max_score')
    def _check_score_range(self):
        """Vérifie que le score est dans la plage valide"""
        for record in self:
            if record.max_score and record.score > record.max_score:
                raise ValidationError(_("Le score ne peut pas être supérieur au score maximum"))
            if record.score < 0:
                raise ValidationError(_("Le score ne peut pas être négatif"))
    
    @api.constrains('weight')
    def _check_weight(self):
        """Vérifie que le poids est positif"""
        for record in self:
            if record.weight <= 0:
                raise ValidationError(_("Le poids doit être supérieur à 0"))
    
    @api.onchange('competency_id')
    def _onchange_competency(self):
        """Met à jour les niveaux de maîtrise disponibles"""
        if self.competency_id:
            return {
                'domain': {
                    'mastery_level_id': [('competency_id', '=', self.competency_id.id)]
                }
            }
        else:
            return {
                'domain': {
                    'mastery_level_id': [('id', '=', False)]
                }
            }
    
    @api.onchange('mastery_level_id')
    def _onchange_mastery_level(self):
        """Met à jour le score basé sur le niveau de maîtrise"""
        if self.mastery_level_id:
            # Utiliser le score moyen du niveau de maîtrise
            avg_score = (self.mastery_level_id.min_score + self.mastery_level_id.max_score) / 2
            self.score = avg_score
            self.max_score = self.mastery_level_id.max_score
    
    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = f"{record.competency_id.name or 'Compétence'}"
            if record.student_id:
                name = f"{record.student_id.name} - {name}"
            if record.percentage:
                name = f"{name} ({record.percentage:.1f}%)"
            result.append((record.id, name))
        return result
    
    def action_view_competency_history(self):
        """Affiche l'historique des évaluations de cette compétence"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Historique - %s') % self.competency_id.name,
            'res_model': 'edu.competency.evaluation',
            'view_mode': 'tree,form',
            'domain': [
                ('student_id', '=', self.student_id.id),
                ('competency_id', '=', self.competency_id.id)
            ],
            'context': {
                'default_student_id': self.student_id.id,
                'default_competency_id': self.competency_id.id
            },
            'target': 'current',
        }
    
    def action_mark_for_reinforcement(self):
        """Marque la compétence comme nécessitant un renforcement"""
        self.ensure_one()
        self.needs_reinforcement = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Marqué pour renforcement'),
                'message': _('Cette compétence est marquée comme nécessitant un renforcement'),
                'type': 'warning'
            }
        }
    
    @api.model
    def get_competency_statistics(self, competency_id, period_id=None, standard_id=None):
        """Obtient les statistiques d'une compétence"""
        domain = [('competency_id', '=', competency_id)]
        
        if period_id:
            domain.append(('period_id', '=', period_id))
        if standard_id:
            domain.append(('student_id.standard_id', '=', standard_id))
        
        evaluations = self.search(domain)
        
        if not evaluations:
            return {
                'total_evaluations': 0,
                'average_score': 0,
                'acquisition_rate': 0,
                'needs_reinforcement_count': 0
            }
        
        total = len(evaluations)
        acquired_count = len(evaluations.filtered('is_acquired'))
        reinforcement_count = len(evaluations.filtered('needs_reinforcement'))
        average_score = sum(evaluations.mapped('percentage')) / total
        
        return {
            'total_evaluations': total,
            'average_score': average_score,
            'acquisition_rate': (acquired_count / total) * 100,
            'needs_reinforcement_count': reinforcement_count
        }


class EduCompetencyEvaluationReport(models.Model):
    """Rapport d'évaluation des compétences"""
    _name = 'edu.competency.evaluation.report'
    _description = 'Rapport d\'évaluation des compétences'
    _auto = False
    _rec_name = 'student_name'

    # Dimensions
    student_id = fields.Many2one('op.student', string='Élève', readonly=True)
    student_name = fields.Char(string='Nom de l\'élève', readonly=True)
    competency_id = fields.Many2one('edu.competency', string='Compétence', readonly=True)
    competency_name = fields.Char(string='Nom de la compétence', readonly=True)
    competency_category = fields.Char(string='Catégorie de compétence', readonly=True)
    course_id = fields.Many2one('op.course', string='Matière', readonly=True)
    course_name = fields.Char(string='Nom de la matière', readonly=True)
    period_id = fields.Many2one('edu.evaluation.period', string='Période', readonly=True)
    period_name = fields.Char(string='Période', readonly=True)
    
    # Métriques
    evaluation_count = fields.Integer(string='Nombre d\'évaluations', readonly=True)
    average_score = fields.Float(string='Score moyen', readonly=True, digits=(6, 2))
    average_percentage = fields.Float(string='Pourcentage moyen', readonly=True, digits=(5, 2))
    acquisition_rate = fields.Float(string='Taux d\'acquisition (%)', readonly=True, digits=(5, 2))
    last_evaluation_date = fields.Date(string='Dernière évaluation', readonly=True)
    
    # Statuts
    is_acquired = fields.Boolean(string='Acquise', readonly=True)
    needs_reinforcement = fields.Boolean(string='À renforcer', readonly=True)
    is_key_competency = fields.Boolean(string='Compétence clé', readonly=True)
    
    def init(self):
        """Initialise la vue SQL pour le rapport"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    ce.student_id,
                    rp.name AS student_name,
                    ce.competency_id,
                    c.name AS competency_name,
                    cc.name AS competency_category,
                    ce.course_id,
                    cr.name AS course_name,
                    ce.period_id,
                    p.name AS period_name,
                    COUNT(ce.id) AS evaluation_count,
                    AVG(ce.score) AS average_score,
                    AVG(ce.percentage) AS average_percentage,
                    (COUNT(CASE WHEN ce.is_acquired THEN 1 END) * 100.0 / COUNT(ce.id)) AS acquisition_rate,
                    MAX(ce.evaluation_date) AS last_evaluation_date,
                    BOOL_OR(ce.is_acquired) AS is_acquired,
                    BOOL_OR(ce.needs_reinforcement) AS needs_reinforcement,
                    c.is_key_competency
                FROM edu_competency_evaluation ce
                LEFT JOIN op_student s ON ce.student_id = s.id
                LEFT JOIN res_partner rp ON s.partner_id = rp.id
                LEFT JOIN edu_competency c ON ce.competency_id = c.id
                LEFT JOIN edu_competency_category cc ON c.category_id = cc.id
                LEFT JOIN op_course cr ON ce.course_id = cr.id
                LEFT JOIN edu_evaluation_period p ON ce.period_id = p.id
                WHERE ce.active = true
                GROUP BY
                    ce.student_id, rp.name,
                    ce.competency_id, c.name, c.is_key_competency,
                    cc.name,
                    ce.course_id, cr.name,
                    ce.period_id, p.name
            )
        """ % self._table)
