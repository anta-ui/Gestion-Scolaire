# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class HealthEmergency(models.Model):
    """Gestion des urgences de santé"""
    _name = 'health.emergency'
    _description = 'Urgence de Santé'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'emergency_date desc, severity desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Numéro d\'urgence',
        required=True,
        copy=False,
        default=lambda self: _('Nouveau'),
        help="Numéro unique de l'urgence"
    )
    
    # Informations de base
    student_id = fields.Many2one(
        'op.student',
        string='Étudiant',
        required=True,
        tracking=True,
        help="Étudiant concerné par l'urgence"
    )
    
    health_record_id = fields.Many2one(
        'edu.health.record',
        string='Dossier médical',
        help="Dossier médical de l'étudiant"
    )
    
    emergency_date = fields.Datetime(
        string='Date/Heure de l\'urgence',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help="Date et heure de l'urgence"
    )
    
    severity = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Modérée'),
        ('high', 'Élevée'),
        ('critical', 'Critique')
    ], string='Gravité', required=True, default='medium', tracking=True)
    
    emergency_type = fields.Selection([
        ('accident', 'Accident'),
        ('illness', 'Maladie soudaine'),
        ('allergy', 'Réaction allergique'),
        ('injury', 'Blessure'),
        ('breathing', 'Problème respiratoire'),
        ('cardiac', 'Problème cardiaque'),
        ('other', 'Autre')
    ], string='Type d\'urgence', required=True)
    
    # Description de l'urgence
    description = fields.Text(
        string='Description de l\'urgence',
        required=True,
        help="Description détaillée de l'urgence"
    )
    
    location = fields.Char(
        string='Lieu de l\'urgence',
        help="Lieu où s'est produite l'urgence"
    )
    
    # Personnel impliqué
    reported_by = fields.Many2one(
        'res.users',
        string='Signalé par',
        default=lambda self: self.env.user,
        help="Personne qui a signalé l'urgence"
    )
    
    handled_by = fields.Many2one(
        'hr.employee',
        string='Pris en charge par',
        help="Personnel médical qui a pris en charge l'urgence"
    )
    
    # Actions prises
    actions_taken = fields.Text(
        string='Actions prises',
        help="Actions prises pour gérer l'urgence"
    )
    
    # Contacts d'urgence
    parents_contacted = fields.Boolean(
        string='Parents contactés',
        default=False,
        tracking=True
    )
    
    contact_time = fields.Datetime(
        string='Heure de contact',
        help="Heure à laquelle les parents ont été contactés"
    )
    
    emergency_services_called = fields.Boolean(
        string='Services d\'urgence appelés',
        default=False,
        tracking=True
    )
    
    service_type = fields.Selection([
        ('samu', 'SAMU'),
        ('pompiers', 'Pompiers'),
        ('police', 'Police'),
        ('hospital', 'Hôpital direct')
    ], string='Service contacté')
    
    # Suivi
    state = fields.Selection([
        ('open', 'En cours'),
        ('resolved', 'Résolue'),
        ('transferred', 'Transférée'),
        ('cancelled', 'Annulée')
    ], string='État', default='open', tracking=True)
    
    resolution_date = fields.Datetime(
        string='Date de résolution',
        help="Date et heure de résolution de l'urgence"
    )
    
    outcome = fields.Text(
        string='Issue/Résultat',
        help="Résultat final de la gestion de l'urgence"
    )
    
    # Métadonnées
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company
    )
    
    @api.model
    def create(self, vals):
        """Création d'une urgence"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('health.emergency') or _('Nouveau')
        return super().create(vals)
    
    def action_resolve(self):
        """Marquer l'urgence comme résolue"""
        self.write({
            'state': 'resolved',
            'resolution_date': fields.Datetime.now()
        })
    
    def action_transfer(self):
        """Marquer l'urgence comme transférée"""
        self.write({
            'state': 'transferred',
            'resolution_date': fields.Datetime.now()
        })


class HealthEmergencyProtocol(models.Model):
    """Protocoles d'urgence"""
    _name = 'health.emergency.protocol'
    _description = 'Protocole d\'Urgence'
    _order = 'emergency_type, severity'

    name = fields.Char(
        string='Nom du protocole',
        required=True,
        help="Nom du protocole d'urgence"
    )
    
    emergency_type = fields.Selection([
        ('accident', 'Accident'),
        ('illness', 'Maladie soudaine'),
        ('allergy', 'Réaction allergique'),
        ('injury', 'Blessure'),
        ('breathing', 'Problème respiratoire'),
        ('cardiac', 'Problème cardiaque'),
        ('other', 'Autre')
    ], string='Type d\'urgence', required=True)
    
    severity = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Modérée'),
        ('high', 'Élevée'),
        ('critical', 'Critique')
    ], string='Gravité', required=True)
    
    steps = fields.Text(
        string='Étapes du protocole',
        required=True,
        help="Étapes détaillées à suivre pour ce type d'urgence"
    )
    
    contacts = fields.Text(
        string='Contacts d\'urgence',
        help="Numéros et contacts à appeler pour ce type d'urgence"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True,
        help="Protocole actif ou archivé"
    )
