# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class EduAttendanceConfig(models.Model):
    _name = 'edu.attendance.config'
    _description = 'Configuration des présences'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nom', required=True)
    active = fields.Boolean('Actif', default=True)
    
    # Paramètres généraux
    default_late_threshold = fields.Integer('Seuil de retard par défaut (minutes)', default=15)
    require_check_out = fields.Boolean('Sortie obligatoire', default=False)
    require_photo = fields.Boolean('Photo obligatoire', default=False)
    require_location = fields.Boolean('Géolocalisation obligatoire', default=False)
    
    # Notifications
    notify_parents_absence = fields.Boolean('Notifier parents absence', default=True)
    notify_teachers_absence = fields.Boolean('Notifier enseignants absence', default=True)
    notification_delay = fields.Integer('Délai notification (minutes)', default=30)
    
    # QR Codes
    qr_code_expiry_days = fields.Integer('Expiration QR codes (jours)', default=365)
    qr_code_size = fields.Selection([
        ('small', 'Petit'),
        ('medium', 'Moyen'),
        ('large', 'Grand')
    ], string='Taille QR codes', default='medium')
    
    # Sécurité
    max_attempts_per_day = fields.Integer('Tentatives max par jour', default=5)
    lockout_duration = fields.Integer('Durée verrouillage (minutes)', default=30)
    
    # Interface
    show_attendance_rate = fields.Boolean('Afficher taux de présence', default=True)
    show_late_count = fields.Boolean('Afficher nombre de retards', default=True)
    show_absence_count = fields.Boolean('Afficher nombre d\'absences', default=True)
    
    # Rapports
    auto_generate_reports = fields.Boolean('Génération automatique rapports', default=False)
    report_frequency = fields.Selection([
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel')
    ], string='Fréquence rapports', default='weekly')
    
    # Sauvegarde
    backup_attendance_data = fields.Boolean('Sauvegarde données présences', default=True)
    backup_frequency = fields.Selection([
        ('daily', 'Quotidienne'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuelle')
    ], string='Fréquence sauvegarde', default='weekly')
    
    # Métadonnées
    created_by = fields.Many2one('res.users', 'Créé par', default=lambda self: self.env.user)
    last_modified = fields.Datetime('Dernière modification', default=fields.Datetime.now)

    @api.model
    def get_config(self):
        """Obtenir la configuration active"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            # Créer une configuration par défaut
            config = self.create({
                'name': 'Configuration par défaut',
                'active': True
            })
        return config

    def action_reset_to_defaults(self):
        """Remettre les paramètres par défaut"""
        self.ensure_one()
        self.write({
            'default_late_threshold': 15,
            'require_check_out': False,
            'require_photo': False,
            'require_location': False,
            'notify_parents_absence': True,
            'notify_teachers_absence': True,
            'notification_delay': 30,
            'qr_code_expiry_days': 365,
            'qr_code_size': 'medium',
            'max_attempts_per_day': 5,
            'lockout_duration': 30,
            'show_attendance_rate': True,
            'show_late_count': True,
            'show_absence_count': True,
            'auto_generate_reports': False,
            'report_frequency': 'weekly',
            'backup_attendance_data': True,
            'backup_frequency': 'weekly'
        })
        return True
