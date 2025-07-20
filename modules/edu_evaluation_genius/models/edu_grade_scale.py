# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduGradeScale(models.Model):
    """Barème de notation (0-20, 0-100, A-F, etc.)"""
    _name = 'edu.grade.scale'
    _description = 'Barème de notation'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du barème',
        required=True,
        translate=True,
        help="Nom du barème (ex: Sur 20, Pourcentage, Lettres)"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=10,
        help="Code court du barème"
    )
    
    description = fields.Text(
        string='Description',
        translate=True
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    # Configuration du barème
    scale_type = fields.Selection([
        ('numeric', 'Numérique'),
        ('letter', 'Lettres'),
        ('percentage', 'Pourcentage'),
        ('pass_fail', 'Réussi/Échoué'),
        ('custom', 'Personnalisé')
    ], string='Type de barème', required=True, default='numeric')
    
    min_value = fields.Float(
        string='Valeur minimale',
        default=0.0,
        digits=(6, 2),
        help="Note minimale possible"
    )
    
    max_value = fields.Float(
        string='Valeur maximale',
        default=20.0,
        digits=(6, 2),
        help="Note maximale possible"
    )
    
    pass_mark = fields.Float(
        string='Note de passage',
        default=10.0,
        digits=(6, 2),
        help="Note minimum pour réussir"
    )
    
    decimal_places = fields.Integer(
        string='Nombre de décimales',
        default=2,
        help="Précision des notes"
    )
    
    # Niveaux de performance
    grade_level_ids = fields.One2many(
        'edu.grade.level',
        'grade_scale_id',
        string='Niveaux de performance'
    )
    
    # Statistiques
    evaluation_count = fields.Integer(
        string='Nombre d\'évaluations',
        compute='_compute_evaluation_count',
        store=True
    )
    
    @api.depends('name')
    def _compute_evaluation_count(self):
        """Calcule le nombre d'évaluations utilisant ce barème"""
        for record in self:
            record.evaluation_count = self.env['edu.evaluation'].search_count([
                ('grade_scale_id', '=', record.id)
            ])
    
    @api.constrains('min_value', 'max_value')
    def _check_min_max_values(self):
        """Vérifie que min < max"""
        for record in self:
            if record.min_value >= record.max_value:
                raise ValidationError(_("La valeur minimale doit être inférieure à la valeur maximale"))
    
    @api.constrains('pass_mark', 'min_value', 'max_value')
    def _check_pass_mark(self):
        """Vérifie que la note de passage est dans l'intervalle"""
        for record in self:
            if not (record.min_value <= record.pass_mark <= record.max_value):
                raise ValidationError(_("La note de passage doit être entre la valeur minimale et maximale"))
    
    @api.constrains('decimal_places')
    def _check_decimal_places(self):
        """Vérifie le nombre de décimales"""
        for record in self:
            if record.decimal_places < 0 or record.decimal_places > 4:
                raise ValidationError(_("Le nombre de décimales doit être entre 0 et 4"))
    
    @api.constrains('code')
    def _check_unique_code(self):
        """Vérifie l'unicité du code"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Le code '%s' existe déjà") % record.code)
    
    def format_grade(self, value):
        """Formate une note selon le barème"""
        self.ensure_one()
        if value is False or value is None:
            return ""
        
        if self.scale_type == 'numeric':
            return f"{value:.{self.decimal_places}f}"
        elif self.scale_type == 'percentage':
            percentage = (value / self.max_value) * 100
            return f"{percentage:.{self.decimal_places}f}%"
        elif self.scale_type == 'pass_fail':
            return "Réussi" if value >= self.pass_mark else "Échoué"
        elif self.scale_type == 'letter':
            return self._get_letter_grade(value)
        else:
            return str(value)
    
    def _get_letter_grade(self, value):
        """Convertit une note en lettre"""
        self.ensure_one()
        for level in self.grade_level_ids.sorted('min_value', reverse=True):
            if value >= level.min_value:
                return level.letter_grade
        return "F"
    
    def get_grade_color(self, value):
        """Retourne la couleur selon la performance"""
        self.ensure_one()
        if value is False or value is None:
            return 'muted'
        
        for level in self.grade_level_ids.sorted('min_value', reverse=True):
            if value >= level.min_value:
                return level.color_class
        return 'danger'
    
    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name} ({record.min_value}-{record.max_value})"
            result.append((record.id, name))
        return result
    
    def action_view_evaluations(self):
        """Action pour voir les évaluations utilisant ce barème"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Évaluations - %s') % self.name,
            'res_model': 'edu.evaluation',
            'view_mode': 'tree,form',
            'domain': [('grade_scale_id', '=', self.id)],
            'context': {'default_grade_scale_id': self.id},
        }


class EduGradeLevel(models.Model):
    """Niveaux de performance pour un barème"""
    _name = 'edu.grade.level'
    _description = 'Niveau de performance'
    _order = 'grade_scale_id, min_value desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du niveau',
        required=True,
        translate=True,
        help="Ex: Excellent, Bien, Passable"
    )
    
    grade_scale_id = fields.Many2one(
        'edu.grade.scale',
        string='Barème',
        required=True,
        ondelete='cascade'
    )
    
    min_value = fields.Float(
        string='Valeur minimale',
        required=True,
        digits=(6, 2)
    )
    
    max_value = fields.Float(
        string='Valeur maximale',
        required=True,
        digits=(6, 2)
    )
    
    letter_grade = fields.Char(
        string='Note lettre',
        size=3,
        help="Ex: A, B, C, D, F"
    )
    
    color_class = fields.Selection([
        ('success', 'Vert (Succès)'),
        ('info', 'Bleu (Info)'),
        ('warning', 'Orange (Attention)'),
        ('danger', 'Rouge (Danger)'),
        ('primary', 'Bleu foncé (Principal)'),
        ('secondary', 'Gris (Secondaire)'),
        ('muted', 'Gris clair (Neutre)')
    ], string='Classe de couleur', default='success')
    
    description = fields.Text(
        string='Description',
        translate=True
    )
    
    @api.constrains('min_value', 'max_value')
    def _check_min_max_values(self):
        """Vérifie que min <= max"""
        for record in self:
            if record.min_value > record.max_value:
                raise ValidationError(_("La valeur minimale doit être inférieure ou égale à la valeur maximale"))
    
    @api.constrains('min_value', 'max_value', 'grade_scale_id')
    def _check_values_in_scale_range(self):
        """Vérifie que les valeurs sont dans la plage du barème"""
        for record in self:
            scale = record.grade_scale_id
            if not (scale.min_value <= record.min_value <= scale.max_value):
                raise ValidationError(_("La valeur minimale doit être dans la plage du barème"))
            if not (scale.min_value <= record.max_value <= scale.max_value):
                raise ValidationError(_("La valeur maximale doit être dans la plage du barème"))
