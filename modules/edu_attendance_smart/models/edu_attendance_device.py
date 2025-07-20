# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class EduAttendanceDevice(models.Model):
    _name = 'edu.attendance.device'
    _description = 'Dispositif de pointage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Nom', required=True, tracking=True)
    code = fields.Char('Code', required=True, copy=False, tracking=True)
    description = fields.Text('Description')

    # Type de dispositif
    device_type = fields.Selection([
        ('qr_scanner', 'Scanner QR Code'),
        ('biometric', 'Lecteur biométrique'),
        ('rfid', 'Lecteur RFID/NFC'),
        ('mobile', 'Application mobile'),
        ('web', 'Interface web'),
        ('kiosk', 'Kiosque'),
        ('other', 'Autre')
    ], string='Type de dispositif', required=True, default='qr_scanner')
    
    # État
    state = fields.Selection([
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('maintenance', 'En maintenance'),
        ('offline', 'Hors ligne')
    ], string='État', default='active', tracking=True)
    
    # Localisation
    location_id = fields.Many2one('edu.location', 'Lieu')
    classroom_name = fields.Char('Salle')
    ip_address = fields.Char('Adresse IP')
    mac_address = fields.Char('Adresse MAC')
    
    # Configuration
    allow_qr_scan = fields.Boolean('Autoriser scan QR', default=True)
    allow_biometric = fields.Boolean('Autoriser biométrie', default=False)
    allow_rfid = fields.Boolean('Autoriser RFID', default=False)
    require_photo = fields.Boolean('Photo obligatoire', default=False)
    require_location = fields.Boolean('Géolocalisation obligatoire', default=False)
    
    # Restrictions
    allowed_qr_types = fields.Many2many(
        'edu.qr.code',
        'device_qr_type_rel',
        'device_id', 'qr_code_id',
        string='Types QR autorisés',
        domain="[('qr_type', 'in', ['student', 'faculty', 'session'])]"
    )
    
    # Statistiques
    total_scans = fields.Integer('Total scans', default=0)
    successful_scans = fields.Integer('Scans réussis', default=0)
    failed_scans = fields.Integer('Scans échoués', default=0)
    last_scan_date = fields.Datetime('Dernier scan')
    
    # Relations
    session_ids = fields.Many2many(
        'edu.attendance.session',
        'device_session_rel',
        'device_id', 'session_id',
        string='Sessions autorisées'
    )
    
    # Contraintes
    _sql_constraints = [
        ('unique_device_code', 'unique(code)', 'Le code du dispositif doit être unique!')
    ]

    @api.model
    def create(self, vals):
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('edu.attendance.device') or 'DEV'
        return super().create(vals)

    def action_activate(self):
        """Activer le dispositif"""
        self.write({'state': 'active'})
        return True

    def action_deactivate(self):
        """Désactiver le dispositif"""
        self.write({'state': 'inactive'})
        return True

    def action_maintenance(self):
        """Mettre en maintenance"""
        self.write({'state': 'maintenance'})
        return True

    def scan_qr_code(self, qr_content, user_id=None, ip_address=None):
        """Scanner un QR code"""
        self.ensure_one()
        
        if self.state != 'active':
            raise UserError(_('Le dispositif n\'est pas actif'))
        
        # Logique de scan à implémenter selon le type de QR
        self.total_scans += 1
        self.last_scan_date = fields.Datetime.now()
        
        # Rechercher le QR code
        qr_code = self.env['edu.qr.code'].search([('content', '=', qr_content)], limit=1)
        if qr_code:
            self.successful_scans += 1
            return qr_code.validate_scan(device_id=self.id, ip_address=ip_address)
        else:
            self.failed_scans += 1
            raise UserError(_('QR code non reconnu'))

    def get_device_status(self):
        """Obtenir le statut du dispositif"""
        return {
            'device_id': self.id,
            'name': self.name,
            'state': self.state,
            'total_scans': self.total_scans,
            'successful_scans': self.successful_scans,
            'failed_scans': self.failed_scans,
            'last_scan': self.last_scan_date
        }
