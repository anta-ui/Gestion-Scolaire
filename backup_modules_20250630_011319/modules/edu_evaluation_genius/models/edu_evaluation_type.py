# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduEvaluationType(models.Model):
    """Types d'évaluations (Contrôle, Examen, TP, Oral, etc.)"""
    _name = 'edu.evaluation.type'
    _description = 'Type d\'évaluation'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du type',
        required=True,
        translate=True,
        help="Nom du type d'évaluation (ex: Contrôle, Examen, TP)"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=10,
        help="Code court pour identifier le type"
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help="Description détaillée du type d'évaluation"
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre d'affichage"
    )
    
    color = fields.Integer(
        string='Couleur',
        default=0,
        help="Couleur pour l'affichage"
    )
    
    coefficient = fields.Float(
        string='Coefficient par défaut',
        default=1.0,
        digits=(6, 2),
        help="Coefficient par défaut pour ce type d'évaluation"
    )
    
    duration = fields.Float(
        string='Durée standard (heures)',
        default=1.0,
        digits=(6, 2),
        help="Durée standard en heures"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True,
        help="Désactiver pour masquer sans supprimer"
    )
    
    # Configuration
    allow_retake = fields.Boolean(
        string='Rattrapage autorisé',
        default=False,
        help="Permet de refaire cette évaluation"
    )
    
    max_retakes = fields.Integer(
        string='Nombre max de rattrapages',
        default=1,
        help="Nombre maximum de tentatives"
    )
    
    is_continuous = fields.Boolean(
        string='Évaluation continue',
        default=False,
        help="Type évaluation continue (plusieurs notes)"
    )
    
    require_justification = fields.Boolean(
        string='Justification requise',
        default=False,
        help="Obligation de justifier la note"
    )
    
    # Statistiques
    evaluation_count = fields.Integer(
        string='Nombre d\'évaluations',
        compute='_compute_evaluation_count',
        store=True
    )
    
    @api.depends('name', 'code')
    def _compute_evaluation_count(self):
        """Calcule le nombre d'évaluations pour ce type"""
        for record in self:
            record.evaluation_count = self.env['edu.evaluation'].search_count([
                ('evaluation_type_id', '=', record.id)
            ])
    
    @api.constrains('coefficient')
    def _check_coefficient(self):
        """Vérifie que le coefficient est positif"""
        for record in self:
            if record.coefficient <= 0:
                raise ValidationError(_("Le coefficient doit être supérieur à 0"))
    
    @api.constrains('duration')
    def _check_duration(self):
        """Vérifie que la durée est positive"""
        for record in self:
            if record.duration <= 0:
                raise ValidationError(_("La durée doit être supérieure à 0"))
    
    @api.constrains('max_retakes')
    def _check_max_retakes(self):
        """Vérifie le nombre de rattrapages"""
        for record in self:
            if record.allow_retake and record.max_retakes <= 0:
                raise ValidationError(_("Le nombre de rattrapages doit être supérieur à 0"))
    
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
            name = f"[{record.code}] {record.name}"
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
        """Action pour voir les évaluations de ce type"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Évaluations - %s') % self.name,
            'res_model': 'edu.evaluation',
            'view_mode': 'tree,form',
            'domain': [('evaluation_type_id', '=', self.id)],
            'context': {'default_evaluation_type_id': self.id},
        }
