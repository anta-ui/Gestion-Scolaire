# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging
import json

_logger = logging.getLogger(__name__)


class TransportTracking(models.Model):
    _name = 'transport.tracking'
    _description = 'Suivi Transport'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Référence', required=True, default=lambda self: _('Nouveau'))
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', required=True, tracking=True)
    trip_id = fields.Many2one('transport.trip', 'Trajet', tracking=True)
    
    # Position actuelle
    current_latitude = fields.Float('Latitude actuelle', digits=(10, 7))
    current_longitude = fields.Float('Longitude actuelle', digits=(10, 7))
    current_address = fields.Text('Adresse actuelle')
    
    # Statut de suivi
    tracking_active = fields.Boolean('Suivi actif', default=True)
    last_update = fields.Datetime('Dernière mise à jour', default=fields.Datetime.now)
    
    # Vitesse et direction
    current_speed = fields.Float('Vitesse actuelle (km/h)')
    current_heading = fields.Float('Direction actuelle (degrés)')
    
    # Statut du véhicule
    engine_status = fields.Boolean('Moteur allumé')
    doors_status = fields.Selection([
        ('closed', 'Fermées'),
        ('open', 'Ouvertes'),
        ('partial', 'Partiellement ouvertes')
    ], string='Statut des portes', default='closed')
    
    # Alertes
    alert_ids = fields.One2many('transport.tracking.alert', 'tracking_id', 'Alertes')
    
    # Historique des positions
    position_history_ids = fields.One2many('transport.position.history', 'tracking_id', 'Historique positions')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('transport.tracking') or _('Nouveau')
        return super(TransportTracking, self).create(vals)
    
    def update_position(self, latitude, longitude, speed=0, heading=0):
        """Mettre à jour la position du véhicule"""
        self.write({
            'current_latitude': latitude,
            'current_longitude': longitude,
            'current_speed': speed,
            'current_heading': heading,
            'last_update': fields.Datetime.now()
        })
        
        # Enregistrer dans l'historique
        self.env['transport.position.history'].create({
            'tracking_id': self.id,
            'vehicle_id': self.vehicle_id.id,
            'latitude': latitude,
            'longitude': longitude,
            'speed': speed,
            'heading': heading,
            'timestamp': fields.Datetime.now()
        })
        
        # Vérifier les alertes
        self._check_alerts(latitude, longitude, speed)
    
    def _check_alerts(self, latitude, longitude, speed):
        """Vérifier et générer les alertes si nécessaire"""
        # Alerte de vitesse
        if speed > self.vehicle_id.max_speed:
            self._create_alert('speed', f'Vitesse excessive: {speed} km/h')
        
        # Alerte de géofence (à implémenter selon les besoins)
        # if not self._is_in_authorized_zone(latitude, longitude):
        #     self._create_alert('geofence', 'Véhicule hors zone autorisée')
    
    def _create_alert(self, alert_type, message):
        """Créer une alerte"""
        self.env['transport.tracking.alert'].create({
            'tracking_id': self.id,
            'vehicle_id': self.vehicle_id.id,
            'alert_type': alert_type,
            'message': message,
            'latitude': self.current_latitude,
            'longitude': self.current_longitude,
            'timestamp': fields.Datetime.now()
        })
    
    def action_start_tracking(self):
        self.tracking_active = True
    
    def action_stop_tracking(self):
        self.tracking_active = False


class TransportPositionHistory(models.Model):
    _name = 'transport.position.history'
    _description = 'Historique Position'
    _order = 'timestamp desc'

    tracking_id = fields.Many2one('transport.tracking', 'Suivi', required=True, ondelete='cascade')
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', required=True)
    trip_id = fields.Many2one('transport.trip', 'Trajet')
    
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
    
    # Distance parcourue depuis la dernière position
    distance_from_previous = fields.Float('Distance depuis position précédente (m)')


class TransportTrackingAlert(models.Model):
    _name = 'transport.tracking.alert'
    _description = 'Alerte de Suivi'
    _order = 'timestamp desc'

    tracking_id = fields.Many2one('transport.tracking', 'Suivi', required=True, ondelete='cascade')
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', required=True)
    trip_id = fields.Many2one('transport.trip', 'Trajet')
    
    # Type d'alerte
    alert_type = fields.Selection([
        ('speed', 'Excès de vitesse'),
        ('geofence', 'Sortie de zone'),
        ('breakdown', 'Panne'),
        ('emergency', 'Urgence'),
        ('delay', 'Retard'),
        ('route_deviation', 'Déviation d\'itinéraire'),
        ('fuel_low', 'Carburant faible'),
        ('maintenance', 'Maintenance requise')
    ], string='Type d\'alerte', required=True)
    
    # Détails
    message = fields.Text('Message', required=True)
    severity = fields.Selection([
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
        ('critical', 'Critique')
    ], string='Gravité', required=True, default='medium')
    
    # Position
    latitude = fields.Float('Latitude', digits=(10, 7))
    longitude = fields.Float('Longitude', digits=(10, 7))
    
    # Horodatage
    timestamp = fields.Datetime('Horodatage', required=True, default=fields.Datetime.now)
    
    # Statut
    state = fields.Selection([
        ('new', 'Nouvelle'),
        ('acknowledged', 'Accusée'),
        ('resolved', 'Résolue'),
        ('ignored', 'Ignorée')
    ], default='new', string='Statut')
    
    # Traitement
    acknowledged_by = fields.Many2one('res.users', 'Accusée par')
    acknowledged_date = fields.Datetime('Date accusé')
    resolved_by = fields.Many2one('res.users', 'Résolue par')
    resolved_date = fields.Datetime('Date résolution')
    resolution_notes = fields.Text('Notes de résolution')
    
    def action_acknowledge(self):
        self.write({
            'state': 'acknowledged',
            'acknowledged_by': self.env.user.id,
            'acknowledged_date': fields.Datetime.now()
        })
    
    def action_resolve(self):
        self.write({
            'state': 'resolved',
            'resolved_by': self.env.user.id,
            'resolved_date': fields.Datetime.now()
        })
    
    def action_ignore(self):
        self.state = 'ignored'


class TransportGeofence(models.Model):
    _name = 'transport.geofence'
    _description = 'Zone Géographique'

    name = fields.Char('Nom de la zone', required=True)
    description = fields.Text('Description')
    
    # Type de zone
    zone_type = fields.Selection([
        ('school', 'École'),
        ('pickup', 'Point de ramassage'),
        ('restricted', 'Zone interdite'),
        ('service', 'Zone de service'),
        ('parking', 'Parking')
    ], string='Type de zone', required=True)
    
    # Géométrie de la zone (polygone)
    geometry = fields.Text('Géométrie (GeoJSON)')
    
    # Centre de la zone
    center_latitude = fields.Float('Latitude centre', digits=(10, 7))
    center_longitude = fields.Float('Longitude centre', digits=(10, 7))
    
    # Rayon (pour les zones circulaires)
    radius = fields.Float('Rayon (m)', help='Pour les zones circulaires')
    
    # Couleur d'affichage
    color = fields.Char('Couleur', default='#FF0000')
    
    # Statut
    active = fields.Boolean('Active', default=True)
    
    # Relations
    route_ids = fields.Many2many('transport.route', string='Itinéraires concernés')
    
    def is_point_inside(self, latitude, longitude):
        """Vérifier si un point est dans la zone"""
        # Implémentation basique pour zone circulaire
        if self.radius and self.center_latitude and self.center_longitude:
            from math import radians, cos, sin, asin, sqrt
            
            def haversine(lon1, lat1, lon2, lat2):
                """Calculer la distance entre deux points GPS"""
                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                r = 6371000  # Rayon de la Terre en mètres
                return c * r
            
            distance = haversine(self.center_longitude, self.center_latitude, longitude, latitude)
            return distance <= self.radius
        
        return False


class TransportRouteOptimization(models.Model):
    _name = 'transport.route.optimization'
    _description = 'Optimisation d\'Itinéraire'

    name = fields.Char('Nom', required=True, default=lambda self: _('Nouveau'))
    date = fields.Date('Date', required=True, default=fields.Date.today)
    
    # Paramètres d'optimisation
    optimization_type = fields.Selection([
        ('distance', 'Distance minimale'),
        ('time', 'Temps minimal'),
        ('fuel', 'Consommation minimale'),
        ('cost', 'Coût minimal')
    ], string='Type d\'optimisation', required=True, default='time')
    
    # Itinéraires à optimiser
    route_ids = fields.Many2many('transport.route', string='Itinéraires')
    
    # Contraintes
    max_capacity = fields.Integer('Capacité maximale par véhicule')
    max_duration = fields.Float('Durée maximale par trajet (heures)')
    
    # Résultats
    optimized_routes = fields.Text('Itinéraires optimisés (JSON)')
    total_distance = fields.Float('Distance totale optimisée (km)')
    total_time = fields.Float('Temps total optimisé (min)')
    fuel_savings = fields.Float('Économie de carburant (%)')
    
    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('running', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué')
    ], default='draft', string='Statut')
    
    def action_optimize(self):
        """Lancer l'optimisation des itinéraires"""
        self.state = 'running'
        # Ici, on implémenterait l'algorithme d'optimisation
        # Pour l'instant, on simule juste
        self.state = 'completed'
        return True
