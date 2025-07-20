# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class TransportEmergency(models.Model):
    _name = 'transport.emergency'
    _description = 'Urgence Transport'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Référence', required=True, default=lambda self: _('Nouveau'))
    
    # Type d'urgence
    emergency_type = fields.Selection([
        ('medical', 'Urgence médicale'),
        ('accident', 'Accident'),
        ('breakdown', 'Panne véhicule'),
        ('weather', 'Conditions météo'),
        ('security', 'Problème sécurité'),
        ('behavioral', 'Problème comportemental'),
        ('other', 'Autre')
    ], string='Type d\'urgence', required=True, tracking=True)
    
    # Gravité
    severity = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
        ('critical', 'Critique')
    ], string='Gravité', required=True, default='medium', tracking=True)
    
    # Informations de base
    description = fields.Text('Description', required=True, tracking=True)
    location = fields.Char('Lieu', tracking=True)
    latitude = fields.Float('Latitude', digits=(10, 7))
    longitude = fields.Float('Longitude', digits=(10, 7))
    
    # Relations
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', tracking=True)
    driver_id = fields.Many2one('transport.driver', 'Chauffeur', tracking=True)
    trip_id = fields.Many2one('transport.trip', 'Trajet', tracking=True)
    
    # Personnes impliquées
    student_ids = fields.Many2many('op.student', string='Étudiants impliqués')
    injured_count = fields.Integer('Nombre de blessés')
    
    # Contacts d'urgence
    emergency_contact_ids = fields.One2many('transport.emergency.contact', 'emergency_id', 'Contacts alertés')
    
    # Statut
    state = fields.Selection([
        ('reported', 'Signalée'),
        ('acknowledged', 'Prise en compte'),
        ('in_progress', 'En cours de traitement'),
        ('resolved', 'Résolue'),
        ('closed', 'Fermée')
    ], default='reported', string='Statut', tracking=True)
    
    # Dates
    reported_date = fields.Datetime('Date de signalement', default=fields.Datetime.now, tracking=True)
    acknowledged_date = fields.Datetime('Date prise en compte', tracking=True)
    resolved_date = fields.Datetime('Date de résolution', tracking=True)
    
    # Personnel de traitement
    reported_by = fields.Many2one('res.users', 'Signalée par', default=lambda self: self.env.user, tracking=True)
    assigned_to = fields.Many2one('res.users', 'Assignée à', tracking=True)
    
    # Actions prises
    actions_taken = fields.Text('Actions prises', tracking=True)
    resolution_notes = fields.Text('Notes de résolution')
    
    # Services d'urgence
    police_called = fields.Boolean('Police contactée')
    ambulance_called = fields.Boolean('Ambulance contactée')
    fire_department_called = fields.Boolean('Pompiers contactés')
    
    # Suivi
    follow_up_required = fields.Boolean('Suivi requis')
    follow_up_date = fields.Date('Date de suivi')
    follow_up_notes = fields.Text('Notes de suivi')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('transport.emergency') or _('Nouveau')
        
        # Créer automatiquement une urgence critique déclenche des alertes
        emergency = super(TransportEmergency, self).create(vals)
        if emergency.severity == 'critical':
            emergency._trigger_critical_alerts()
        
        return emergency
    
    def _trigger_critical_alerts(self):
        """Déclencher les alertes pour une urgence critique"""
        # Alerter les responsables
        responsible_users = self.env['res.users'].search([
            ('groups_id', 'in', self.env.ref('edu_transport_manager.group_transport_manager').ids)
        ])
        
        for user in responsible_users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary=f'URGENCE CRITIQUE: {self.emergency_type}',
                note=f'Urgence critique signalée: {self.description}'
            )
        
        # Envoyer des notifications push (à implémenter)
        # self._send_push_notifications()
    
    def action_acknowledge(self):
        """Prendre en compte l'urgence"""
        self.write({
            'state': 'acknowledged',
            'acknowledged_date': fields.Datetime.now(),
            'assigned_to': self.env.user.id
        })
    
    def action_start_treatment(self):
        """Commencer le traitement"""
        self.state = 'in_progress'
    
    def action_resolve(self):
        """Marquer comme résolue"""
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Datetime.now()
        })
    
    def action_close(self):
        """Fermer l'urgence"""
        self.state = 'closed'
    
    def action_call_emergency_services(self):
        """Ouvrir un wizard pour contacter les services d'urgence"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contacter les services d\'urgence',
            'res_model': 'transport.emergency.services.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_emergency_id': self.id}
        }


class TransportEmergencyContact(models.Model):
    _name = 'transport.emergency.contact'
    _description = 'Contact d\'Urgence'

    emergency_id = fields.Many2one('transport.emergency', 'Urgence', required=True, ondelete='cascade')
    
    # Contact
    contact_type = fields.Selection([
        ('parent', 'Parent'),
        ('guardian', 'Tuteur'),
        ('school', 'École'),
        ('emergency_service', 'Service d\'urgence'),
        ('insurance', 'Assurance'),
        ('other', 'Autre')
    ], string='Type de contact', required=True)
    
    name = fields.Char('Nom', required=True)
    phone = fields.Char('Téléphone', required=True)
    email = fields.Char('Email')
    
    # Statut de contact
    contacted = fields.Boolean('Contacté')
    contact_date = fields.Datetime('Date de contact')
    contact_method = fields.Selection([
        ('phone', 'Téléphone'),
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('in_person', 'En personne')
    ], string='Méthode de contact')
    
    response = fields.Text('Réponse')
    notes = fields.Text('Notes')
    
    def action_mark_contacted(self):
        """Marquer comme contacté"""
        self.write({
            'contacted': True,
            'contact_date': fields.Datetime.now()
        })


class TransportEmergencyProtocol(models.Model):
    _name = 'transport.emergency.protocol'
    _description = 'Protocole d\'Urgence'

    name = fields.Char('Nom du protocole', required=True)
    emergency_type = fields.Selection([
        ('medical', 'Urgence médicale'),
        ('accident', 'Accident'),
        ('breakdown', 'Panne véhicule'),
        ('weather', 'Conditions météo'),
        ('security', 'Problème sécurité'),
        ('behavioral', 'Problème comportemental'),
        ('fire', 'Incendie'),
        ('evacuation', 'Évacuation')
    ], string='Type d\'urgence', required=True)
    
    # Contenu du protocole
    description = fields.Text('Description')
    steps = fields.Html('Étapes à suivre', required=True)
    
    # Contacts d'urgence par défaut
    default_contacts = fields.Text('Contacts par défaut')
    
    # Matériel requis
    required_equipment = fields.Text('Matériel requis')
    
    # Statut
    active = fields.Boolean('Actif', default=True)
    
    # Dernière révision
    last_review_date = fields.Date('Dernière révision')
    next_review_date = fields.Date('Prochaine révision')
    reviewed_by = fields.Many2one('res.users', 'Révisé par')


class TransportEvacuationPlan(models.Model):
    _name = 'transport.evacuation.plan'
    _description = 'Plan d\'Évacuation'

    name = fields.Char('Nom du plan', required=True)
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', required=True)
    
    # Points d'évacuation
    evacuation_point_ids = fields.One2many('transport.evacuation.point', 'plan_id', 'Points d\'évacuation')
    
    # Procédures
    evacuation_procedure = fields.Html('Procédure d\'évacuation')
    assembly_point = fields.Char('Point de rassemblement')
    
    # Responsabilités
    evacuation_leader = fields.Many2one('hr.employee', 'Responsable évacuation')
    assistant_ids = fields.Many2many('hr.employee', string='Assistants')
    
    # Équipement d'urgence
    emergency_equipment = fields.Text('Équipement d\'urgence disponible')
    
    # Statut
    active = fields.Boolean('Actif', default=True)
    last_drill_date = fields.Date('Dernier exercice')
    next_drill_date = fields.Date('Prochain exercice')


class TransportEvacuationPoint(models.Model):
    _name = 'transport.evacuation.point'
    _description = 'Point d\'Évacuation'

    plan_id = fields.Many2one('transport.evacuation.plan', 'Plan d\'évacuation', required=True, ondelete='cascade')
    name = fields.Char('Nom du point', required=True)
    sequence = fields.Integer('Séquence', default=10)
    
    # Localisation
    latitude = fields.Float('Latitude', digits=(10, 7))
    longitude = fields.Float('Longitude', digits=(10, 7))
    address = fields.Text('Adresse')
    
    # Capacité
    capacity = fields.Integer('Capacité d\'accueil')
    
    # Services disponibles
    medical_facilities = fields.Boolean('Installations médicales')
    shelter_available = fields.Boolean('Abri disponible')
    communication_equipment = fields.Boolean('Équipement de communication')
    
    # Contact
    contact_person = fields.Char('Personne de contact')
    contact_phone = fields.Char('Téléphone de contact')


class TransportFirstAidKit(models.Model):
    _name = 'transport.first.aid.kit'
    _description = 'Trousse de Premiers Secours'

    name = fields.Char('Nom de la trousse', required=True)
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', required=True)
    
    # Contenu
    item_ids = fields.One2many('transport.first.aid.item', 'kit_id', 'Articles')
    
    # Dates
    last_check_date = fields.Date('Dernière vérification')
    next_check_date = fields.Date('Prochaine vérification')
    expiry_date = fields.Date('Date d\'expiration')
    
    # Responsable
    responsible_person = fields.Many2one('hr.employee', 'Responsable')
    
    # Statut
    status = fields.Selection([
        ('complete', 'Complète'),
        ('incomplete', 'Incomplète'),
        ('expired', 'Expirée')
    ], string='Statut', compute='_compute_status')
    
    @api.depends('item_ids.status', 'expiry_date')
    def _compute_status(self):
        for kit in self:
            if kit.expiry_date and kit.expiry_date < fields.Date.today():
                kit.status = 'expired'
            elif any(item.status in ['missing', 'expired'] for item in kit.item_ids):
                kit.status = 'incomplete'
            else:
                kit.status = 'complete'


class TransportFirstAidItem(models.Model):
    _name = 'transport.first.aid.item'
    _description = 'Article Premiers Secours'

    kit_id = fields.Many2one('transport.first.aid.kit', 'Trousse', required=True, ondelete='cascade')
    name = fields.Char('Nom de l\'article', required=True)
    
    # Quantité
    required_quantity = fields.Integer('Quantité requise', default=1)
    current_quantity = fields.Integer('Quantité actuelle')
    
    # Dates
    expiry_date = fields.Date('Date d\'expiration')
    
    # Statut
    status = fields.Selection([
        ('ok', 'OK'),
        ('low', 'Stock faible'),
        ('missing', 'Manquant'),
        ('expired', 'Expiré')
    ], string='Statut', compute='_compute_status')
    
    @api.depends('current_quantity', 'required_quantity', 'expiry_date')
    def _compute_status(self):
        for item in self:
            if item.expiry_date and item.expiry_date < fields.Date.today():
                item.status = 'expired'
            elif item.current_quantity == 0:
                item.status = 'missing'
            elif item.current_quantity < item.required_quantity:
                item.status = 'low'
            else:
                item.status = 'ok'
