# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class HealthEmergency(models.Model):
    """Gestion des urgences médicales"""
    _name = 'health.emergency'
    _description = 'Urgence Médicale'
    _order = 'emergency_date desc'

    # Informations de base
    name = fields.Char(
        string='Référence urgence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau')
    )

    emergency_date = fields.Datetime(
        string='Date de l\'urgence',
        required=True,
        default=fields.Datetime.now
    )

    # Patient concerné
    health_record_id = fields.Many2one(
        'edu.health.record',
        string='Dossier médical',
        required=True
    )

    student_id = fields.Many2one(
        related='health_record_id.student_id',
        string='Étudiant',
        readonly=True,
        store=True
    )

    # Type et gravité
    emergency_type = fields.Selection([
        ('medical', 'Urgence médicale'),
        ('accident', 'Accident'),
        ('allergy', 'Réaction allergique'),
        ('cardiac', 'Urgence cardiaque'),
        ('respiratory', 'Urgence respiratoire'),
        ('trauma', 'Traumatisme'),
        ('poisoning', 'Intoxication'),
        ('other', 'Autre'),
    ], string='Type d\'urgence', required=True, default='medical')

    severity_level = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Modérée'),
        ('high', 'Élevée'),
        ('critical', 'Critique'),
    ], string='Niveau de gravité', required=True, default='medium')

    # Description
    description = fields.Text(
        string='Description de l\'urgence',
        required=True
    )

    location = fields.Char(
        string='Lieu de l\'urgence'
    )

    # Personnes impliquées
    reported_by = fields.Many2one(
        'res.users',
        string='Signalé par',
        required=True,
        default=lambda self: self.env.user
    )

    first_responder = fields.Many2one(
        'res.users',
        string='Premier intervenant'
    )

    # Actions prises
    immediate_actions = fields.Text(
        string='Actions immédiates prises'
    )

    # Services d'urgence
    ambulance_called = fields.Boolean(
        string='Ambulance appelée'
    )

    ambulance_time = fields.Datetime(
        string='Heure d\'appel ambulance'
    )

    hospital_transport = fields.Boolean(
        string='Transport à l\'hôpital'
    )

    hospital_name = fields.Char(
        string='Nom de l\'hôpital'
    )

    # État de l'urgence
    state = fields.Selection([
        ('reported', 'Signalée'),
        ('in_progress', 'En cours'),
        ('resolved', 'Résolue'),
        ('transferred', 'Transférée'),
    ], string='État', default='reported', required=True)

    resolution_notes = fields.Text(
        string='Notes de résolution'
    )

    resolved_date = fields.Datetime(
        string='Date de résolution'
    )

    # Consultation associée
    consultation_id = fields.Many2one(
        'edu.medical.consultation',
        string='Consultation associée'
    )

    # Actions
    def action_start_response(self):
        """Commencer la réponse d'urgence"""
        self.write({
            'state': 'in_progress',
            'first_responder': self.env.user.id
        })
        return True

    def action_resolve(self):
        """Résoudre l'urgence"""
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Datetime.now()
        })
        return True

    def action_transfer(self):
        """Transférer l'urgence"""
        self.write({
            'state': 'transferred',
            'hospital_transport': True
        })
        return True

    @api.model
    def create(self, vals):
        """Génération automatique du numéro d'urgence"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('health.emergency') or _('Nouveau')
        return super().create(vals)


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
        ('allergic_reaction', 'Réaction allergique sévère'),
        ('injury', 'Blessure'),
        ('breathing', 'Problème respiratoire'),
        ('respiratory', 'Problème respiratoire'),
        ('cardiac', 'Problème cardiaque'),
        ('other', 'Autre')
    ], string='Type d\"urgence', required=True)
    
    severity = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Modérée'),
        ('high', 'Élevée'),
        ('critical', 'Critique')
    ], string='Gravité', required=True)
    
    response_time = fields.Integer(
        string='Temps de réponse (min)',
        help="Temps de réponse maximum en minutes"
    )
    
    steps = fields.Text(
        string='Étapes du protocole',
        required=True,
        help="Étapes détaillées à suivre pour ce type d'urgence"
    )
    
    protocol_steps = fields.Html(
        string='Étapes du protocole (détaillées)',
        help="Étapes détaillées formatées HTML"
    )
    
    required_equipment = fields.Text(
        string='Équipement requis',
        help="Équipement nécessaire pour ce protocole"
    )
    
    contact_emergency_services = fields.Boolean(
        string='Contacter les services d\'urgence',
        default=False,
        help="Indique s'il faut contacter les services d'urgence"
    )
    
    notify_parents = fields.Boolean(
        string='Notifier les parents',
        default=True,
        help="Indique s'il faut notifier les parents"
    )
    
    notify_administration = fields.Boolean(
        string='Notifier l\'administration',
        default=True,
        help="Indique s'il faut notifier l'administration"
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
