# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduCompetency(models.Model):
    """Compétences évaluables"""
    _name = 'edu.competency'
    _description = 'Compétence'
    _order = 'sequence, name'
    _rec_name = 'name'
    _parent_name = 'parent_id'
    _parent_store = True

    name = fields.Char(
        string='Nom de la compétence',
        required=True,
        translate=True
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=20,
        help="Code unique de la compétence"
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help="Description détaillée de la compétence"
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    # Hiérarchie
    parent_id = fields.Many2one(
        'edu.competency',
        string='Compétence parent',
        index=True,
        ondelete='cascade'
    )
    
    parent_path = fields.Char(
        index=True
    )
    
    child_ids = fields.One2many(
        'edu.competency',
        'parent_id',
        string='Sous-compétences'
    )
    
    level = fields.Integer(
        string='Niveau',
        compute='_compute_level',
        store=True
    )
    
    # Classification
    category_id = fields.Many2one(
        'edu.competency.category',
        string='Catégorie',
        help="Catégorie de la compétence"
    )
    
    competency_type = fields.Selection([
        ('knowledge', 'Savoir (Connaissances)'),
        ('skill', 'Savoir-faire (Compétences)'),
        ('attitude', 'Savoir-être (Attitudes)'),
        ('transversal', 'Transversale')
    ], string='Type de compétence', required=True, default='knowledge')
    
    # Configuration
    is_key_competency = fields.Boolean(
        string='Compétence clé',
        default=False,
        help="Compétence essentielle à valider"
    )
    
    coefficient = fields.Float(
        string='Coefficient',
        default=1.0,
        digits=(6, 2),
        help="Poids de la compétence dans l'évaluation"
    )
    
    # Liens académiques
    course_ids = fields.Many2many(
        'op.course',
        'competency_course_rel',
        'competency_id',
        'course_id',
        string='Matières liées'
    )
    
    batch_ids = fields.Many2many(
        'op.batch',
        string='Groupes',
        help="Groupes concernés par cette compétence"
    )
    
    # Niveaux de maîtrise
    mastery_level_ids = fields.One2many(
        'edu.competency.mastery.level',
        'competency_id',
        string='Niveaux de maîtrise'
    )
    
    # Statistiques
    evaluation_count = fields.Integer(
        string='Nombre d\'évaluations',
        compute='_compute_evaluation_count'
    )
    
    @api.depends('parent_id')
    def _compute_level(self):
        """Calcule le niveau dans la hiérarchie"""
        for record in self:
            level = 0
            parent = record.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            record.level = level
    
    def _compute_evaluation_count(self):
        """Calcule le nombre d'évaluations pour cette compétence"""
        for record in self:
            record.evaluation_count = self.env['edu.competency.evaluation'].search_count([
                ('competency_id', '=', record.id)
            ])
    
    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        """Évite la récursion dans la hiérarchie"""
        if not self._check_recursion():
            raise ValidationError(_("Erreur! Vous ne pouvez pas créer de compétences récursives."))
    
    @api.constrains('coefficient')
    def _check_coefficient(self):
        """Vérifie que le coefficient est positif"""
        for record in self:
            if record.coefficient <= 0:
                raise ValidationError(_("Le coefficient doit être supérieur à 0"))
    
    @api.constrains('code')
    def _check_unique_code(self):
        """Vérifie l'unicité du code"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Le code '%s' existe déjà") % record.code)
    
    def name_get(self):
        """Affichage avec hiérarchie"""
        result = []
        for record in self:
            name = record.name
            if record.parent_id:
                name = f"{record.parent_id.name} / {name}"
            name = f"[{record.code}] {name}"
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
        """Action pour voir les évaluations de cette compétence"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Évaluations - %s') % self.name,
            'res_model': 'edu.competency.evaluation',
            'view_mode': 'tree,form',
            'domain': [('competency_id', '=', self.id)],
            'context': {'default_competency_id': self.id},
        }


class EduCompetencyCategory(models.Model):
    """Catégories de compétences"""
    _name = 'edu.competency.category'
    _description = 'Catégorie de compétence'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom de la catégorie',
        required=True,
        translate=True
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=10
    )
    
    description = fields.Text(
        string='Description',
        translate=True
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10
    )
    
    color = fields.Integer(
        string='Couleur',
        default=0
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    competency_ids = fields.One2many(
        'edu.competency',
        'category_id',
        string='Compétences'
    )
    
    competency_count = fields.Integer(
        string='Nombre de compétences',
        compute='_compute_competency_count'
    )
    
    def _compute_competency_count(self):
        """Calcule le nombre de compétences"""
        for record in self:
            record.competency_count = len(record.competency_ids)
    
    @api.constrains('code')
    def _check_unique_code(self):
        """Vérifie l'unicité du code"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Le code '%s' existe déjà") % record.code)
    
    def action_view_competencies(self):
        """Action pour voir les compétences de cette catégorie"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Compétences - %s') % self.name,
            'res_model': 'edu.competency',
            'view_mode': 'tree,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
        }


class EduCompetencyMasteryLevel(models.Model):
    """Niveaux de maîtrise d'une compétence"""
    _name = 'edu.competency.mastery.level'
    _description = 'Niveau de maîtrise'
    _order = 'competency_id, sequence'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du niveau',
        required=True,
        translate=True,
        help="Ex: Débutant, Intermédiaire, Avancé, Expert"
    )
    
    competency_id = fields.Many2one(
        'edu.competency',
        string='Compétence',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre de progression"
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help="Critères et attendus pour ce niveau"
    )
    
    min_score = fields.Float(
        string='Score minimum',
        default=0.0,
        digits=(6, 2),
        help="Score minimum pour atteindre ce niveau"
    )
    
    max_score = fields.Float(
        string='Score maximum',
        default=20.0,
        digits=(6, 2),
        help="Score maximum pour ce niveau"
    )
    
    color_class = fields.Selection([
        ('success', 'Vert (Maîtrisé)'),
        ('info', 'Bleu (En cours)'),
        ('warning', 'Orange (À améliorer)'),
        ('danger', 'Rouge (Non maîtrisé)'),
        ('primary', 'Bleu foncé (Excellent)'),
        ('secondary', 'Gris (En attente)')
    ], string='Classe de couleur', default='info')

