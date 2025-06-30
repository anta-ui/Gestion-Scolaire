# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class TransportTrip(models.Model):
    _name = 'transport.trip'
    _description = 'Trajet de Transport'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, scheduled_time desc'

    name = fields.Char('Référence', required=True, default=lambda self: _('Nouveau'))
    
    # Informations de base
    route_id = fields.Many2one('transport.route', 'Itinéraire', required=True, tracking=True)
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', required=True, tracking=True)
    driver_id = fields.Many2one('transport.driver', 'Chauffeur', required=True, tracking=True)
    
    # Planification
    scheduled_date = fields.Date('Date prévue', required=True, default=fields.Date.today, tracking=True)
    scheduled_time = fields.Float('Heure prévue', required=True, tracking=True)
    
    # Exécution
    actual_start_time = fields.Datetime('Heure de départ réelle', tracking=True)
    actual_end_time = fields.Datetime('Heure d\'arrivée réelle', tracking=True)
    
    # Statut
    state = fields.Selection([
        ('planned', 'Planifié'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
        ('delayed', 'Retardé')
    ], default='planned', string='Statut', tracking=True)
    
    # Type de trajet
    trip_type = fields.Selection([
        ('pickup', 'Ramassage'),
        ('dropoff', 'Dépose'),
        ('round_trip', 'Aller-retour'),
        ('special', 'Spécial')
    ], default='pickup', string='Type de trajet', required=True)
    
    # Passagers
    student_ids = fields.Many2many('op.student', string='Étudiants')
    passenger_count = fields.Integer('Nombre de passagers', compute='_compute_passenger_count')
    max_capacity = fields.Integer('Capacité max', related='vehicle_id.total_capacity')
    
    # Distance et durée
    distance = fields.Float('Distance (km)')
    duration = fields.Float('Durée (min)')
    
    # Coûts
    fuel_cost = fields.Float('Coût carburant')
    total_cost = fields.Float('Coût total', compute='_compute_total_cost')
    
    # Incidents
    has_incident = fields.Boolean('Incident signalé')
    incident_description = fields.Text('Description incident')
    
    # Suivi GPS
    gps_tracking_ids = fields.One2many('transport.gps.tracking', 'trip_id', 'Suivi GPS')
    
    # Commentaires
    notes = fields.Text('Notes')
    
    @api.depends('student_ids')
    def _compute_passenger_count(self):
        for trip in self:
            trip.passenger_count = len(trip.student_ids)
    
    @api.depends('fuel_cost', 'distance')
    def _compute_total_cost(self):
        for trip in self:
            # Calcul basique du coût total
            base_cost = trip.distance * 0.5  # 0.5€ par km
            trip.total_cost = base_cost + trip.fuel_cost
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('transport.trip') or _('Nouveau')
        return super(TransportTrip, self).create(vals)
    
    def action_start_trip(self):
        self.write({
            'state': 'in_progress',
            'actual_start_time': fields.Datetime.now()
        })
    
    def action_complete_trip(self):
        self.write({
            'state': 'completed',
            'actual_end_time': fields.Datetime.now()
        })
    
    def action_cancel_trip(self):
        self.state = 'cancelled'
    
    def action_report_incident(self):
        self.has_incident = True
        # Ouvrir un wizard pour saisir les détails de l'incident
        return {
            'type': 'ir.actions.act_window',
            'name': 'Signaler un incident',
            'res_model': 'transport.incident.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_trip_id': self.id}
        }


class TransportGpsTracking(models.Model):
    _name = 'transport.gps.tracking'
    _description = 'Suivi GPS'
    _order = 'timestamp desc'

    trip_id = fields.Many2one('transport.trip', 'Trajet', required=True, ondelete='cascade')
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', required=True)
    
    # Position
    latitude = fields.Float('Latitude', digits=(10, 7), required=True)
    longitude = fields.Float('Longitude', digits=(10, 7), required=True)
    altitude = fields.Float('Altitude (m)')
    
    # Horodatage
    timestamp = fields.Datetime('Horodatage', required=True, default=fields.Datetime.now)
    
    # Vitesse et direction
    speed = fields.Float('Vitesse (km/h)')
    heading = fields.Float('Direction (degrés)')
    
    # Statut
    engine_on = fields.Boolean('Moteur allumé')
    doors_open = fields.Boolean('Portes ouvertes')
    
    # Alertes
    speeding_alert = fields.Boolean('Alerte vitesse')
    geofence_alert = fields.Boolean('Alerte géofence')


class TransportIncident(models.Model):
    _name = 'transport.incident'
    _description = 'Incident de Transport'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char('Référence', required=True, default=lambda self: _('Nouveau'))
    trip_id = fields.Many2one('transport.trip', 'Trajet', required=True)
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', related='trip_id.vehicle_id')
    driver_id = fields.Many2one('transport.driver', 'Chauffeur', related='trip_id.driver_id')
    
    # Détails de l'incident
    date = fields.Datetime('Date et heure', required=True, default=fields.Datetime.now)
    incident_type = fields.Selection([
        ('breakdown', 'Panne'),
        ('accident', 'Accident'),
        ('delay', 'Retard'),
        ('medical', 'Urgence médicale'),
        ('behavior', 'Problème comportemental'),
        ('other', 'Autre')
    ], string='Type d\'incident', required=True)
    
    severity = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
        ('critical', 'Critique')
    ], string='Gravité', required=True, default='medium')
    
    description = fields.Text('Description', required=True)
    actions_taken = fields.Text('Actions prises')
    
    # Personnes impliquées
    students_involved = fields.Many2many('op.student', string='Étudiants impliqués')
    witnesses = fields.Text('Témoins')
    
    # Suivi
    resolved = fields.Boolean('Résolu')
    resolution_date = fields.Datetime('Date de résolution')
    resolution_notes = fields.Text('Notes de résolution')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('transport.incident') or _('Nouveau')
        return super(TransportIncident, self).create(vals)
