# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduAttendanceConfig(models.Model):
    """Configuration globale du système de présences"""
    _name = 'edu.attendance.config'
    _description = 'Configuration Présences'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom de la configuration',
        required=True,
        help="Nom de la configuration"
    )
    
    active = fields.Boolean(
        string='Configuration active',
        default=True,
        help="Configuration actuellement utilisée"
    )
    
    # Paramètres de temps
    auto_mark_absent_delay = fields.Integer(
        string='Délai absence auto (min)',
        default=30,
        help="Délai en minutes avant de marquer automatiquement absent"
    )
    
    late_threshold = fields.Integer(
        string='Seuil de retard (min)',
        default=15,
        help="Nombre de minutes de tolérance avant retard"
    )
    
    early_departure_threshold = fields.Integer(
        string='Seuil départ anticipé (min)',
        default=15,
        help="Nombre de minutes avant la fin pour considérer un départ anticipé"
    )
    
    grace_period = fields.Integer(
        string='Période de grâce (min)',
        default=5,
        help="Période de grâce pour les pointages"
    )
    
    # Gestion des excuses
    require_excuse_for_absence = fields.Boolean(
        string='Excuse obligatoire',
        default=True,
        help="Exiger une excuse pour les absences"
    )
    
    allow_self_excuse = fields.Boolean(
        string='Auto-excuse autorisée',
        default=False,
        help="Permettre aux élèves de s'excuser eux-mêmes"
    )
    
    max_excuse_days = fields.Integer(
        string='Délai max excuse (jours)',
        default=3,
        help="Délai maximum pour fournir une excuse"
    )
    
    require_excuse_document = fields.Boolean(
        string='Document obligatoire',
        default=False,
        help="Exiger un document justificatif"
    )
    
    # Notifications
    notify_parents_absence = fields.Boolean(
        string='Notifier parents',
        default=True,
        help="Envoyer des notifications aux parents"
    )
    
    notification_delay = fields.Integer(
        string='Délai notification (min)',
        default=30,
        help="Délai avant envoi de notification d'absence"
    )
    
    notify_late_arrival = fields.Boolean(
        string='Notifier retards',
        default=True,
        help="Notifier les arrivées en retard"
    )
    
    notify_early_departure = fields.Boolean(
        string='Notifier départs anticipés',
        default=True,
        help="Notifier les départs anticipés"
    )
    
    # Jours ouvrables
    working_days_only = fields.Boolean(
        string='Jours ouvrables seulement',
        default=True,
        help="Prendre en compte uniquement les jours ouvrables"
    )
    
    weekend_notification = fields.Boolean(
        string='Notifications weekend',
        default=False,
        help="Envoyer des notifications le weekend"
    )
    
    holiday_notification = fields.Boolean(
        string='Notifications vacances',
        default=False,
        help="Envoyer des notifications pendant les vacances"
    )
    
    # Sécurité et validation
    require_photo_verification = fields.Boolean(
        string='Photo obligatoire',
        default=False,
        help="Exiger une photo pour la vérification"
    )
    
    require_gps_verification = fields.Boolean(
        string='GPS obligatoire',
        default=False,
        help="Exiger la géolocalisation"
    )
    
    allow_manual_override = fields.Boolean(
        string='Modification manuelle',
        default=True,
        help="Permettre les modifications manuelles par les enseignants"
    )
    
    require_validation = fields.Boolean(
        string='Validation obligatoire',
        default=False,
        help="Exiger la validation des présences par un responsable"
    )
    
    # Rapports et statistiques
    generate_daily_reports = fields.Boolean(
        string='Rapports quotidiens',
        default=True,
        help="Générer automatiquement les rapports quotidiens"
    )
    
    generate_weekly_reports = fields.Boolean(
        string='Rapports hebdomadaires',
        default=True,
        help="Générer automatiquement les rapports hebdomadaires"
    )
    
    attendance_rate_threshold = fields.Float(
        string='Seuil taux présence (%)',
        default=80.0,
        digits=(5, 2),
        help="Seuil en dessous duquel alerter"
    )
    
    # Archivage
    auto_archive_delay = fields.Integer(
        string='Délai archivage (jours)',
        default=365,
        help="Délai avant archivage automatique des données"
    )
    
    keep_logs_duration = fields.Integer(
        string='Conservation logs (jours)',
        default=90,
        help="Durée de conservation des logs"
    )
    
    @api.constrains('auto_mark_absent_delay', 'late_threshold', 'early_departure_threshold')
    def _check_positive_delays(self):
        """Vérifie que les délais sont positifs"""
        for record in self:
            if record.auto_mark_absent_delay < 0:
                raise ValidationError(_("Le délai d'absence automatique doit être positif"))
            if record.late_threshold < 0:
                raise ValidationError(_("Le seuil de retard doit être positif"))
            if record.early_departure_threshold < 0:
                raise ValidationError(_("Le seuil de départ anticipé doit être positif"))
    
    @api.constrains('attendance_rate_threshold')
    def _check_attendance_rate(self):
        """Vérifie le seuil de taux de présence"""
        for record in self:
            if not (0 <= record.attendance_rate_threshold <= 100):
                raise ValidationError(_("Le taux de présence doit être entre 0 et 100%"))
    
    @api.model
    def get_active_config(self):
        """Retourne la configuration active"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            # Créer une configuration par défaut si aucune n'existe
            config = self.create({
                'name': 'Configuration par défaut',
                'active': True,
            })
        return config
