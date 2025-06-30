# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduBiometricData(models.Model):
    """Données biométriques pour l'authentification"""
    _name = 'edu.biometric.data'
    _description = 'Données biométriques'
    _rec_name = 'name'

    name = fields.Char('Nom', required=True)
    partner_id = fields.Many2one('res.partner', 'Personne', required=True, ondelete='cascade')
    
    biometric_type = fields.Selection([
        ('fingerprint', 'Empreinte digitale'),
        ('face', 'Reconnaissance faciale'),
        ('iris', 'Reconnaissance iris')
    ], string='Type biométrique', required=True, default='fingerprint')
    
    biometric_data = fields.Binary('Données biométriques', required=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('inactive', 'Inactif')
    ], string='État', default='draft', required=True)
    
    active = fields.Boolean('Actif', default=True) 