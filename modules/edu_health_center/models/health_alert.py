# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class HealthAlert(models.Model):
    """Modèle pour les alertes de santé"""
    _name = 'health.alert'
    _description = 'Alerte de Santé'
    _order = 'create_date desc'
    
    name = fields.Char(
        string='Titre de l\'alerte',
        required=True
    )
    
    description = fields.Text(
        string='Description',
        required=True
    )
    
    alert_type = fields.Selection([
        ('medical', 'Médical'),
        ('emergency', 'Urgence'),
        ('vaccination', 'Vaccination'),
        ('epidemic', 'Épidémie'),
        ('maintenance', 'Maintenance'),
        ('other', 'Autre')
    ], string='Type d\'alerte', default='medical', required=True)
    
    severity = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé'),
        ('critical', 'Critique')
    ], string='Gravité', default='medium', required=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Active'),
        ('resolved', 'Résolue'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', required=True)
    
    student_id = fields.Many2one(
        'res.partner',
        string='Étudiant concerné',
        domain=[('is_company', '=', False)]
    )
    
    health_record_id = fields.Many2one(
        'edu.health.record',
        string='Dossier médical'
    )
    
    created_by = fields.Many2one(
        'res.users',
        string='Créé par',
        default=lambda self: self.env.user,
        required=True
    )
    
    resolved_by = fields.Many2one(
        'res.users',
        string='Résolu par'
    )
    
    resolved_date = fields.Datetime(
        string='Date de résolution'
    )
    
    due_date = fields.Datetime(
        string='Date d\'échéance'
    )
    
    notes = fields.Text(
        string='Notes'
    )
    
    # Remplacer le champ active par un champ personnalisé
    is_archived = fields.Boolean(
        string='Archivé',
        default=False,
        help="Cocher pour archiver l'alerte"
    )
    
    def action_activate(self):
        """Activer l'alerte"""
        self.state = 'active'
        return True
    
    def action_resolve(self):
        """Résoudre l'alerte"""
        self.state = 'resolved'
        self.resolved_by = self.env.user
        self.resolved_date = fields.Datetime.now()
        return True
    
    def action_cancel(self):
        """Annuler l'alerte"""
        self.state = 'cancelled'
        return True
    
    def action_archive(self):
        """Archiver l'alerte"""
        self.is_archived = True
        return True
    
    def action_unarchive(self):
        """Désarchiver l'alerte"""
        self.is_archived = False
        return True
    
    @api.model
    def create_epidemic_alert(self, disease_name, affected_count):
        """Créer une alerte épidémique"""
        return self.create({
            'name': f'Alerte épidémique - {disease_name}',
            'description': f'Détection de {affected_count} cas de {disease_name}',
            'alert_type': 'epidemic',
            'severity': 'high' if affected_count > 5 else 'medium',
            'state': 'active'
        })
