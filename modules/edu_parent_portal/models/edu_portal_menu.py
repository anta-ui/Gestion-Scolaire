# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EduPortalMenu(models.Model):
    """Gestion des menus du portail parent"""
    _name = 'edu.portal.menu'
    _description = 'Menu du portail parent'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nom du menu',
        required=True,
        help="Nom affiché du menu"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        help="Code unique du menu"
    )
    
    url = fields.Char(
        string='URL',
        help="URL du menu"
    )
    
    icon = fields.Char(
        string='Icône',
        default='fa-circle',
        help="Classe CSS de l'icône FontAwesome"
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre d'affichage"
    )
    
    visible = fields.Boolean(
        string='Visible',
        default=True,
        help="Menu visible dans le portail"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True,
        help="Menu actif"
    )
    
    target = fields.Selection([
        ('_self', 'Même fenêtre'),
        ('_blank', 'Nouvelle fenêtre'),
        ('_modal', 'Modal')
    ], string='Cible', default='_self', help="Cible du lien")
    
    description = fields.Text(
        string='Description',
        help="Description du menu"
    )
    
    parent_id = fields.Many2one(
        'edu.portal.menu',
        string='Menu parent',
        help="Menu parent pour les sous-menus"
    )
    
    child_ids = fields.One2many(
        'edu.portal.menu',
        'parent_id',
        string='Sous-menus',
        help="Sous-menus"
    )
    
    user_groups = fields.Many2many(
        'res.groups',
        string='Groupes autorisés',
        help="Groupes d'utilisateurs autorisés à voir ce menu"
    )
    
    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Le code du menu doit être unique."))
    
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.parent_id:
                name = f"{record.parent_id.name} / {name}"
            result.append((record.id, name))
        return result
