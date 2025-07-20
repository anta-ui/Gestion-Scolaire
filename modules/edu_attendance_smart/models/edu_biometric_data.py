# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class EduBiometricData(models.Model):
    _name = 'edu.biometric.data'
    _description = 'Données biométriques'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Nom', required=True)
    partner_id = fields.Many2one('res.partner', 'Personne', required=True,
                                domain="[('is_student', '=', True)]")
    
    # Type de données biométriques
    biometric_type = fields.Selection([
        ('fingerprint', 'Empreinte digitale'),
        ('facial', 'Reconnaissance faciale'),
        ('iris', 'Iris'),
        ('voice', 'Voix'),
        ('palm', 'Empreinte palmaire'),
        ('other', 'Autre')
    ], string='Type biométrique', required=True, default='fingerprint')
    
    # Données
    biometric_data = fields.Binary('Données biométriques', attachment=True)
    biometric_data_filename = fields.Char('Nom fichier')
    data_hash = fields.Char('Hash des données', compute='_compute_data_hash', store=True)
    
    # Qualité et validation
    quality_score = fields.Float('Score de qualité', digits=(3, 2), help="Score de qualité de 0 à 1")
    is_verified = fields.Boolean('Vérifié', default=False)
    verification_date = fields.Datetime('Date de vérification')
    verified_by = fields.Many2one('res.users', 'Vérifié par')
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('expired', 'Expiré')
    ], string='État', default='draft', tracking=True)
    
    # Sécurité
    encryption_key = fields.Char('Clé de chiffrement')
    is_encrypted = fields.Boolean('Chiffré', default=True)
    access_level = fields.Selection([
        ('public', 'Public'),
        ('private', 'Privé'),
        ('restricted', 'Restreint')
    ], string='Niveau d\'accès', default='restricted')
    
    # Métadonnées
    capture_date = fields.Datetime('Date de capture', default=fields.Datetime.now)
    capture_device = fields.Char('Dispositif de capture')
    capture_location = fields.Char('Lieu de capture')
    
    # Expiration
    expiry_date = fields.Date('Date d\'expiration')
    is_expired = fields.Boolean('Expiré', compute='_compute_is_expired', store=True)
    
    # Relations
    device_ids = fields.Many2many('edu.attendance.device', 'biometric_device_rel',
                                 'biometric_id', 'device_id', string='Dispositifs compatibles')
    
    # Contraintes
    _sql_constraints = [
        ('unique_partner_biometric_type', 'unique(partner_id, biometric_type, state)',
         'Une personne ne peut avoir qu\'un seul enregistrement actif par type biométrique!')
    ]

    @api.depends('biometric_data')
    def _compute_data_hash(self):
        """Calcule le hash des données biométriques"""
        for record in self:
            if record.biometric_data:
                import hashlib
                data = base64.b64decode(record.biometric_data)
                record.data_hash = hashlib.sha256(data).hexdigest()
            else:
                record.data_hash = ""

    @api.depends('expiry_date')
    def _compute_is_expired(self):
        """Vérifie si les données sont expirées"""
        for record in self:
            if record.expiry_date:
                record.is_expired = fields.Date.today() > record.expiry_date
            else:
                record.is_expired = False

    @api.model
    def create(self, vals):
        """Création avec validation"""
        if not vals.get('name'):
            vals['name'] = f"Biométrie {vals.get('biometric_type', 'unknown')}"
        return super().create(vals)

    def action_activate(self):
        """Activer les données biométriques"""
        self.ensure_one()
        self.write({'state': 'active'})
        return True

    def action_deactivate(self):
        """Désactiver les données biométriques"""
        self.ensure_one()
        self.write({'state': 'inactive'})
        return True

    def action_verify(self):
        """Vérifier les données biométriques"""
        self.ensure_one()
        self.write({
            'is_verified': True,
            'verification_date': fields.Datetime.now(),
            'verified_by': self.env.user.id
        })
        return True

    def action_unverify(self):
        """Déverifier les données biométriques"""
        self.ensure_one()
        self.write({
            'is_verified': False,
            'verification_date': False,
            'verified_by': False
        })
        return True

    def validate_biometric(self, input_data, device_id=None):
        """Valider des données biométriques d'entrée"""
        self.ensure_one()
        
        if self.state != 'active':
            raise UserError(_('Les données biométriques ne sont pas actives'))
        
        if self.is_expired:
            raise UserError(_('Les données biométriques sont expirées'))
        
        # Logique de validation à implémenter selon le type
        # Pour l'instant, retourner True si les données existent
        return bool(self.biometric_data)

    def get_biometric_info(self):
        """Obtenir les informations biométriques"""
        return {
            'id': self.id,
            'type': dict(self._fields['biometric_type'].selection)[self.biometric_type],
            'state': dict(self._fields['state'].selection)[self.state],
            'is_verified': self.is_verified,
            'is_expired': self.is_expired,
            'quality_score': self.quality_score,
            'capture_date': self.capture_date,
            'expiry_date': self.expiry_date
        }

    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        """Vérifier la date d'expiration"""
        for record in self:
            if record.expiry_date and record.expiry_date < fields.Date.today():
                raise ValidationError(_('La date d\'expiration ne peut pas être dans le passé')) 