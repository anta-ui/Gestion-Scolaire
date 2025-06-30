# -*- coding: utf-8 -*-

from odoo import models, fields


class EduContactGroup(models.Model):
    _name = 'edu.contact.group'
    _description = 'Groupe de contacts'
    
    name = fields.Char('Nom du groupe', required=True)
    description = fields.Text('Description')
    
    contact_ids = fields.Many2many('res.partner', 'group_contact_rel',
                                  'group_id', 'partner_id',
                                  string='Contacts')
    
    active = fields.Boolean('Actif', default=True)
    color = fields.Integer('Couleur', default=1)
    
    # Statistiques
    contact_count = fields.Integer('Nombre de contacts', compute='_compute_contact_count')
    
    def _compute_contact_count(self):
        """Calculer le nombre de contacts"""
        for group in self:
            group.contact_count = len(group.contact_ids)
