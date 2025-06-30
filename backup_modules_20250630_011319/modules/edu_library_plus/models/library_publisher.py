# -*- coding: utf-8 -*-

from odoo import models, fields, api


class LibraryBookPublisher(models.Model):
    _name = 'library.book.publisher'
    _description = 'Éditeur de Livre'
    _order = 'name'

    name = fields.Char(
        string='Nom de l\'Éditeur',
        required=True
    )
    
    code = fields.Char(
        string='Code',
        size=10
    )
    
    address = fields.Text(
        string='Adresse'
    )
    
    city = fields.Char(
        string='Ville'
    )
    
    state_id = fields.Many2one(
        'res.country.state',
        string='État/Province'
    )
    
    country_id = fields.Many2one(
        'res.country',
        string='Pays'
    )
    
    zip = fields.Char(
        string='Code postal'
    )
    
    phone = fields.Char(
        string='Téléphone'
    )
    
    email = fields.Char(
        string='Email'
    )
    
    website = fields.Char(
        string='Site web'
    )
    
    contact_person = fields.Char(
        string='Personne de contact'
    )
    
    founded_year = fields.Integer(
        string='Année de fondation'
    )
    
    description = fields.Html(
        string='Description'
    )
    
    logo = fields.Binary(
        string='Logo',
        attachment=True
    )
    
    book_ids = fields.One2many(
        'library.book',
        'publisher_id',
        string='Livres publiés'
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
        for publisher in self:
            publisher.book_count = len(publisher.book_ids)
    
    @api.model
    def create(self, vals):
        if 'code' not in vals or not vals['code']:
            vals['code'] = self.env['ir.sequence'].next_by_code('library.publisher') or '/'
        return super().create(vals)
    
    def name_get(self):
        result = []
        for publisher in self:
            name = publisher.name
            if publisher.code:
                name = f"[{publisher.code}] {name}"
            result.append((publisher.id, name))
        return result
