# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EduPaymentMethodNew(models.Model):
    _name = 'edu.payment.method.new'
    _description = 'Méthode de paiement éducative nouvelle'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom',
        required=True,
        help='Nom de la méthode de paiement'
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        help='Code unique de la méthode'
    )
    
    method_type = fields.Selection([
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement bancaire'),
        ('card', 'Carte bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('check', 'Chèque'),
        ('online', 'Paiement en ligne'),
        ('other', 'Autre')
    ], string='Type de méthode', required=True, default='cash')
    
    description = fields.Text(
        string='Description',
        help='Description détaillée de la méthode'
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True,
        help='Cochez pour activer cette méthode de paiement'
    )