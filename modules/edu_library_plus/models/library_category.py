# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LibraryBookCategory(models.Model):
    _name = 'library.book.category'
    _description = 'Catégorie de Livre'
    _order = 'name'

    name = fields.Char(
        string='Nom de la Catégorie',
        required=True,
        translate=True
    )
    
    description = fields.Text(
        string='Description',
        translate=True
    )
    
    color = fields.Integer(
        string='Couleur',
        default=0
    )
    
    parent_id = fields.Many2one(
        'library.book.category',
        string='Catégorie Parent',
        ondelete='cascade'
    )
    
    child_ids = fields.One2many(
        'library.book.category',
        'parent_id',
        string='Sous-catégories'
    )
    
    book_count = fields.Integer(
        string='Nombre de livres',
        compute='_compute_book_count',
        recursive=True
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    @api.depends('child_ids.book_count')
    def _compute_book_count(self):
        for category in self:
            books = self.env['library.book'].search([
                ('category_id', 'child_of', category.id)
            ])
            category.book_count = len(books)
    
    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]
    
    def name_get(self):
        result = []
        for category in self:
            name = category.name
            if category.parent_id:
                name = f"{category.parent_id.name} / {name}"
            result.append((category.id, name))
        return result
