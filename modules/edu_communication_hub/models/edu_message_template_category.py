# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EduMessageTemplateCategory(models.Model):
    """Catégories de templates de messages"""
    _name = 'edu.message.template.category'
    _description = 'Catégorie de template de message'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Nom',
        required=True,
        help="Nom de la catégorie"
    )
    
    description = fields.Text(
        string='Description',
        help="Description de la catégorie"
    )
    
    color = fields.Integer(
        string='Couleur',
        help="Index de couleur pour l'affichage"
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre d'affichage"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True,
        help="Si décoché, la catégorie sera masquée"
    )
    
    # Relation avec les templates
    template_ids = fields.One2many(
        'edu.message.template',
        'category_id',
        string='Templates',
        help="Templates de cette catégorie"
    )
    
    template_count = fields.Integer(
        string='Nombre de templates',
        compute='_compute_template_count',
        help="Nombre de templates dans cette catégorie"
    )
    
    @api.depends('template_ids')
    def _compute_template_count(self):
        """Calcule le nombre de templates par catégorie"""
        for category in self:
            category.template_count = len(category.template_ids)
