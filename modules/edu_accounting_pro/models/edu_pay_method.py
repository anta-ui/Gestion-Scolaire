# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class EduPayMethod(models.Model):
    _name = 'edu.pay.method'
    _description = 'Method de paiement'
    _order = 'name'
    
    name = fields.Char(
        string='Nom',
        required=True,
        help='Nom de la méthode de paiement'
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=10,
        help='Code unique de la méthode'
    )
    
    method_type = fields.Selection([
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement bancaire'),
        ('check', 'Chèque'),
        ('credit_card', 'Carte de crédit'),
        ('mobile_money', 'Argent mobile'),
        ('online', 'Paiement en ligne'),
        ('other', 'Autre')
    ], string='Type', required=True, default='cash')
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
