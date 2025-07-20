# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduEvaluationCriteria(models.Model):
    """Critères d'évaluation détaillés"""
    _name = 'edu.evaluation.criteria'
    _description = 'Critère d\'évaluation'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du critère',
        required=True,
        translate=True,
        help="Nom du critère d'évaluation"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=15,
        help="Code unique du critère"
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help="Description détaillée du critère"
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre d'affichage"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    # Configuration
    criteria_type = fields.Selection([
        ('knowledge', 'Connaissance'),
        ('comprehension', 'Compréhension'),
        ('application', 'Application'),
        ('analysis', 'Analyse'),
        ('synthesis', 'Synthèse'),
        ('evaluation', 'Évaluation'),
        ('presentation', 'Présentation'),
        ('participation', 'Participation'),
        ('behavior', 'Comportement'),
        ('effort', 'Effort'),
        ('creativity', 'Créativité'),
        ('collaboration', 'Collaboration'),
        ('autonomy', 'Autonomie'),
        ('other', 'Autre')
    ], string='Type de critère', required=True, default='knowledge')
    
    weight = fields.Float(
        string='Poids (%)',
        default=25.0,
        digits=(5, 2),
        help="Poids du critère dans l'évaluation (en %)"
    )
    
    max_points = fields.Float(
        string='Points maximum',
        default=5.0,
        digits=(6, 2),
        help="Nombre maximum de points pour ce critère"
    )
    
    # Rubrique d'évaluation
    rubric_level_ids = fields.One2many(
        'edu.criteria.rubric.level',
        'criteria_id',
        string='Niveaux de la rubrique'
    )
    
    # Liens
    competency_ids = fields.Many2many(
        'edu.competency',
        'criteria_competency_rel',
        'criteria_id',
        'competency_id',
        string='Compétences liées'
    )
    
    course_ids = fields.Many2many(
        'op.course',
        'criteria_course_rel',
        'criteria_id',
        'course_id',
        string='Matières'
    )
    
    # Statistiques
    usage_count = fields.Integer(
        string='Nombre d\'utilisations',
        compute='_compute_usage_count'
    )
    
    def _compute_usage_count(self):
        """Calcule le nombre d'utilisations du critère"""
        for record in self:
            record.usage_count = self.env['edu.evaluation.line'].search_count([
                ('criteria_id', '=', record.id)
            ])
    
    @api.constrains('weight')
    def _check_weight(self):
        """Vérifie que le poids est entre 0 et 100"""
        for record in self:
            if not (0 <= record.weight <= 100):
                raise ValidationError(_("Le poids doit être entre 0 et 100%"))
    
    @api.constrains('max_points')
    def _check_max_points(self):
        """Vérifie que les points max sont positifs"""
        for record in self:
            if record.max_points <= 0:
                raise ValidationError(_("Le nombre de points maximum doit être supérieur à 0"))
    
    @api.constrains('code')
    def _check_unique_code(self):
        """Vérifie l'unicité du code"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Le code '%s' existe déjà") % record.code)
    
    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name} ({record.weight}%)"
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
        """Action pour voir les évaluations utilisant ce critère"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Évaluations - %s') % self.name,
            'res_model': 'edu.evaluation.line',
            'view_mode': 'tree,form',
            'domain': [('criteria_id', '=', self.id)],
            'context': {'default_criteria_id': self.id},
        }


class EduCriteriaRubricLevel(models.Model):
    """Niveaux de la rubrique d'évaluation pour un critère"""
    _name = 'edu.criteria.rubric.level'
    _description = 'Niveau de rubrique'
    _order = 'criteria_id, points desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du niveau',
        required=True,
        translate=True,
        help="Ex: Excellent, Satisfaisant, À améliorer, Insuffisant"
    )
    
    criteria_id = fields.Many2one(
        'edu.evaluation.criteria',
        string='Critère',
        required=True,
        ondelete='cascade'
    )
    
    points = fields.Float(
        string='Points',
        required=True,
        digits=(6, 2),
        help="Nombre de points pour ce niveau"
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help="Description détaillée des attendus pour ce niveau"
    )
    
    indicators = fields.Text(
        string='Indicateurs',
        translate=True,
        help="Indicateurs observables pour ce niveau"
    )
    
    color_class = fields.Selection([
        ('success', 'Vert (Excellent)'),
        ('info', 'Bleu (Satisfaisant)'),
        ('warning', 'Orange (À améliorer)'),
        ('danger', 'Rouge (Insuffisant)'),
        ('primary', 'Bleu foncé'),
        ('secondary', 'Gris')
    ], string='Couleur', default='success')
    
    sequence = fields.Integer(
        string='Séquence',
        default=10
    )
    
    @api.constrains('points', 'criteria_id')
    def _check_points_range(self):
        """Vérifie que les points sont dans la plage du critère"""
        for record in self:
            if record.points < 0 or record.points > record.criteria_id.max_points:
                raise ValidationError(_(
                    "Les points doivent être entre 0 et %s (maximum du critère)"
                ) % record.criteria_id.max_points)
    
    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = f"{record.name} ({record.points} pts)"
            result.append((record.id, name))
        return result
