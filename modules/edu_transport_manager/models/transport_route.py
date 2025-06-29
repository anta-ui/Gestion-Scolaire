# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class TransportRoute(models.Model):
    _name = 'transport.route'
    _description = 'Itinéraire de Transport'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char('Nom de l\'itinéraire', required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')
    
    # Informations de base
    start_location = fields.Char('Point de départ', required=True)
    end_location = fields.Char('Point d\'arrivée', required=True)
    total_distance = fields.Float('Distance totale (km)')
    estimated_duration = fields.Float('Durée estimée (min)')
    
    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('archived', 'Archivé')
    ], default='draft', string='Statut')
    
    # Relations
    stop_ids = fields.One2many('transport.route.stop', 'route_id', 'Arrêts')
    trip_ids = fields.One2many('transport.trip', 'route_id', 'Trajets')
    vehicle_ids = fields.Many2many('transport.vehicle', string='Véhicules assignés')
    
    # Horaires
    departure_time = fields.Float('Heure de départ')
    arrival_time = fields.Float('Heure d\'arrivée')
    
    # Tarification
    base_fare = fields.Float('Tarif de base')
    
    # Statistiques
    trip_count = fields.Integer('Nombre de trajets', compute='_compute_trip_count')
    student_count = fields.Integer('Nombre d\'étudiants', compute='_compute_student_count')
    
    @api.depends('trip_ids')
    def _compute_trip_count(self):
        for route in self:
            route.trip_count = len(route.trip_ids)
    
    @api.depends('stop_ids.student_ids')
    def _compute_student_count(self):
        for route in self:
            route.student_count = sum(len(stop.student_ids) for stop in route.stop_ids)
    
    def action_activate(self):
        self.state = 'active'
    
    def action_deactivate(self):
        self.state = 'inactive'


class TransportRouteStop(models.Model):
    _name = 'transport.route.stop'
    _description = 'Arrêt d\'itinéraire'
    _order = 'sequence'

    name = fields.Char('Nom de l\'arrêt', required=True)
    sequence = fields.Integer('Séquence', default=10)
    route_id = fields.Many2one('transport.route', 'Itinéraire', required=True, ondelete='cascade')
    
    # Géolocalisation
    latitude = fields.Float('Latitude', digits=(10, 7))
    longitude = fields.Float('Longitude', digits=(10, 7))
    address = fields.Text('Adresse')
    
    # Horaires
    arrival_time = fields.Float('Heure d\'arrivée')
    departure_time = fields.Float('Heure de départ')
    stop_duration = fields.Float('Durée d\'arrêt (min)', default=2.0)
    
    # Relations
    student_ids = fields.Many2many('op.student', string='Étudiants')
    
    # Distance depuis le départ
    distance_from_start = fields.Float('Distance depuis le départ (km)')
    
    student_count = fields.Integer('Nombre d\'étudiants', compute='_compute_student_count')
    
    @api.depends('student_ids')
    def _compute_student_count(self):
        for stop in self:
            stop.student_count = len(stop.student_ids)
