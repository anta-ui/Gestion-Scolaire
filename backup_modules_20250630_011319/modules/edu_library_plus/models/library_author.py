# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LibraryBookAuthor(models.Model):
    _name = 'library.book.author'
    _description = 'Auteur de Livre'
    _order = 'name'

    name = fields.Char(
        string='Nom de l\'Auteur',
        required=True
    )
    
    first_name = fields.Char(
        string='Prénom'
    )
    
    last_name = fields.Char(
        string='Nom de famille'
    )
    
    biography = fields.Html(
        string='Biographie'
    )
    
    birth_date = fields.Date(
        string='Date de naissance'
    )
    
    death_date = fields.Date(
        string='Date de décès'
    )
    
    nationality = fields.Many2one(
        'res.country',
        string='Nationalité'
    )
    
    website = fields.Char(
        string='Site web'
    )
    
    email = fields.Char(
        string='Email'
    )
    
    phone = fields.Char(
        string='Téléphone'
    )
    
    image = fields.Binary(
        string='Photo',
        attachment=True
    )
    
    book_ids = fields.Many2many(
        'library.book',
        'library_book_author_rel',
        'author_id',
        'book_id',
        string='Livres'
    )
    
    book_count = fields.Integer(
        string='Nombre de Livres',
        compute='_compute_book_count',
        store=True
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    @api.depends('book_ids')
    def _compute_book_count(self):
        for author in self:
            author.book_count = len(author.book_ids)
    
    @api.model
    def create(self, vals):
        if 'name' not in vals and 'first_name' in vals and 'last_name' in vals:
            vals['name'] = f"{vals.get('first_name', '')} {vals.get('last_name', '')}".strip()
        return super().create(vals)
    
    def write(self, vals):
        if ('first_name' in vals or 'last_name' in vals) and 'name' not in vals:
            for record in self:
                first_name = vals.get('first_name', record.first_name) or ''
                last_name = vals.get('last_name', record.last_name) or ''
                vals['name'] = f"{first_name} {last_name}".strip()
        return super().write(vals)
