# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EduPaymentMethodFinal(models.Model):
    """Modèle final pour les méthodes de paiement éducatif"""
    _name = 'edu.payment.method.final'
    _description = 'Méthode de paiement éducatif - Version finale'
    _order = 'name'
    _rec_name = 'name'

    # Champs de base
    name = fields.Char(
        string='Nom',
        required=True,
        translate=True,
        help="Nom de la méthode de paiement"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=10,
        help="Code unique de la méthode"
    )
    
    method_type = fields.Selection([
        ('cash', 'Espèces'),
        ('check', 'Chèque'),
        ('bank_transfer', 'Virement bancaire'),
        ('credit_card', 'Carte de crédit'),
        ('mobile_money', 'Mobile Money'),
        ('online', 'Paiement en ligne'),
        ('other', 'Autre')
    ], string='Type', required=True, default='cash')
    
    active = fields.Boolean(
        string='Actif',
        default=True,
        help="Désactiver pour archiver sans supprimer"
    )

    # Contraintes
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Le code doit être unique !'),
        ('name_unique', 'UNIQUE(name)', 'Le nom doit être unique !'),
    ]

    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if not record.code or len(record.code.strip()) < 2:
                raise ValidationError("Le code doit contenir au moins 2 caractères")

    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result
