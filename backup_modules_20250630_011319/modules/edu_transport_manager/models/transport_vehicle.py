# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import logging
import qrcode
import base64
from io import BytesIO

_logger = logging.getLogger(__name__)

class TransportVehicle(models.Model):
    _name = 'transport.vehicle'
    _description = 'Véhicule de Transport Scolaire'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'name'

    # Informations de base
    name = fields.Char(
        string='Nom du véhicule',
        required=True,
        tracking=True,
        help='Nom ou numéro d\'identification du véhicule'
    )
    
    code = fields.Char(
        string='Code véhicule',
        required=True,
        copy=False,
        tracking=True
    )
    
    license_plate = fields.Char(
        string='Plaque d\'immatriculation',
        required=True,
        tracking=True
    )
    
    # Type et catégorie
    vehicle_type = fields.Selection([
        ('bus', 'Bus scolaire'),
        ('minibus', 'Minibus'),
        ('car', 'Voiture'),
        ('van', 'Fourgonnette'),
        ('coach', 'Autocar'),
        ('other', 'Autre'),
    ], string='Type de véhicule', required=True, default='bus', tracking=True)
    
    category = fields.Selection([
        ('standard', 'Standard'),
        ('luxury', 'Luxe'),
        ('accessibility', 'Accessibilité PMR'),
        ('emergency', 'Urgence'),
        ('special', 'Spécialisé'),
    ], string='Catégorie', default='standard')
    
    # Caractéristiques techniques
    brand = fields.Char(
        string='Marque',
        required=True,
        tracking=True
    )
    
    model = fields.Char(
        string='Modèle',
        required=True,
        tracking=True
    )
    
    year = fields.Integer(
        string='Année',
        required=True,
        tracking=True
    )
    
    engine_type = fields.Selection([
        ('gasoline', 'Essence'),
        ('diesel', 'Diesel'),
        ('electric', 'Électrique'),
        ('hybrid', 'Hybride'),
        ('gas', 'Gaz'),
    ], string='Type de moteur', default='diesel')
    
    engine_power = fields.Float(
        string='Puissance (CV)',
        help='Puissance du moteur en chevaux'
    )
    
    fuel_capacity = fields.Float(
        string='Capacité réservoir (L)',
        help='Capacité du réservoir de carburant en litres'
    )
    
    max_speed = fields.Float(
        string='Vitesse maximale (km/h)',
        default=90.0,
        help='Vitesse maximale autorisée pour ce véhicule'
    )
    
    # Capacités
    seating_capacity = fields.Integer(
        string='Nombre de places assises',
        required=True,
        default=50,
        tracking=True
    )
    
    standing_capacity = fields.Integer(
        string='Nombre de places debout',
        default=0
    )
    
    total_capacity = fields.Integer(
        string='Capacité totale',
        compute='_compute_total_capacity',
        store=True
    )
    
    wheelchair_spaces = fields.Integer(
        string='Emplacements fauteuil roulant',
        default=0
    )
    
    # État et statut
    state = fields.Selection([
        ('active', 'En service'),
        ('maintenance', 'En maintenance'),
        ('repair', 'En réparation'),
        ('inactive', 'Hors service'),
        ('sold', 'Vendu'),
        ('scrapped', 'Mis au rebut'),
    ], string='État', default='active', required=True, tracking=True)
    
    operational_status = fields.Selection([
        ('available', 'Disponible'),
        ('in_use', 'En service'),
        ('maintenance', 'Maintenance'),
        ('emergency', 'Urgence'),
        ('breakdown', 'Panne'),
    ], string='Statut opérationnel', default='available', tracking=True)
    
    # Localisation et GPS
    current_location = fields.Char(
        string='Position actuelle',
        help='Dernière position GPS connue'
    )
    
    current_latitude = fields.Float(
        string='Latitude actuelle',
        digits=(10, 6)
    )
    
    current_longitude = fields.Float(
        string='Longitude actuelle',
        digits=(10, 6)
    )
    
    last_gps_update = fields.Datetime(
        string='Dernière mise à jour GPS',
        readonly=True
    )
    
    gps_device_id = fields.Char(
        string='ID dispositif GPS',
        help='Identifiant unique du boîtier GPS'
    )
    
    # Informations d'achat et financières
    purchase_date = fields.Date(
        string='Date d\'achat',
        tracking=True
    )
    
    purchase_price = fields.Float(
        string='Prix d\'achat',
        tracking=True
    )
    
    current_value = fields.Float(
        string='Valeur actuelle',
        help='Valeur estimée actuelle du véhicule'
    )
    
    depreciation_rate = fields.Float(
        string='Taux d\'amortissement (%)',
        default=20.0,
        help='Taux d\'amortissement annuel en pourcentage'
    )
    
    # Kilométrage et usage
    initial_odometer = fields.Float(
        string='Kilométrage initial',
        default=0.0,
        help='Kilométrage à l\'achat'
    )
    
    current_odometer = fields.Float(
        string='Kilométrage actuel',
        tracking=True,
        help='Kilométrage actuel du véhicule'
    )
    
    total_distance = fields.Float(
        string='Distance totale parcourue',
        compute='_compute_total_distance',
        store=True,
        help='Distance totale depuis l\'achat'
    )
    
    daily_average_km = fields.Float(
        string='Moyenne quotidienne (km)',
        compute='_compute_daily_average_km'
    )
    
    # Assurance et documents légaux
    insurance_company = fields.Char(
        string='Compagnie d\'assurance'
    )
    
    insurance_policy_number = fields.Char(
        string='Numéro de police d\'assurance'
    )
    
    insurance_start_date = fields.Date(
        string='Début assurance'
    )
    
    insurance_end_date = fields.Date(
        string='Fin assurance',
        tracking=True
    )
    
    insurance_cost = fields.Float(
        string='Coût assurance annuel'
    )
    
    # Contrôle technique
    last_technical_control = fields.Date(
        string='Dernier contrôle technique'
    )
    
    next_technical_control = fields.Date(
        string='Prochain contrôle technique',
        tracking=True
    )
    
    technical_control_valid = fields.Boolean(
        string='Contrôle technique valide',
        compute='_compute_technical_control_valid'
    )
    
    # Équipements et options
    has_gps = fields.Boolean(
        string='GPS installé',
        default=True
    )
    
    has_camera = fields.Boolean(
        string='Caméras de surveillance',
        default=False
    )
    
    has_wifi = fields.Boolean(
        string='WiFi à bord',
        default=False
    )
    
    has_air_conditioning = fields.Boolean(
        string='Climatisation',
        default=True
    )
    
    has_first_aid = fields.Boolean(
        string='Trousse de premiers secours',
        default=True
    )
    
    has_fire_extinguisher = fields.Boolean(
        string='Extincteur',
        default=True
    )
    
    is_accessible = fields.Boolean(
        string='Accessible PMR',
        default=False,
        help='Véhicule adapté aux personnes à mobilité réduite'
    )
    
    accessibility_features = fields.Text(
        string='Équipements d\'accessibilité',
        help='Description des équipements pour personnes handicapées'
    )
    
    # Consommation et écologie
    fuel_consumption_city = fields.Float(
        string='Consommation ville (L/100km)',
        help='Consommation de carburant en ville'
    )
    
    fuel_consumption_highway = fields.Float(
        string='Consommation route (L/100km)',
        help='Consommation de carburant sur route'
    )
    
    co2_emission = fields.Float(
        string='Émissions CO2 (g/km)',
        help='Émissions de CO2 en grammes par kilomètre'
    )
    
    environmental_rating = fields.Selection([
        ('a', 'A - Très faible'),
        ('b', 'B - Faible'),
        ('c', 'C - Modéré'),
        ('d', 'D - Élevé'),
        ('e', 'E - Très élevé'),
    ], string='Classe environnementale')
    
    # Relations
    driver_ids = fields.Many2many(
        'transport.driver',
        'vehicle_driver_rel',
        'vehicle_id',
        'driver_id',
        string='Chauffeurs autorisés'
    )
    
    current_driver_id = fields.Many2one(
        'transport.driver',
        string='Chauffeur actuel'
    )
    
    trip_ids = fields.One2many(
        'transport.trip',
        'vehicle_id',
        string='Trajets'
    )
    
    maintenance_ids = fields.One2many(
        'transport.maintenance',
        'vehicle_id',
        string='Maintenances'
    )
    
    tracking_ids = fields.One2many(
        'transport.tracking',
        'vehicle_id',
        string='Suivis GPS'
    )
    
    # Statistiques
    total_trips = fields.Integer(
        string='Nombre total de trajets',
        compute='_compute_statistics'
    )
    
    total_students_transported = fields.Integer(
        string='Étudiants transportés',
        compute='_compute_statistics'
    )
    
    maintenance_cost_total = fields.Float(
        string='Coût total maintenance',
        compute='_compute_maintenance_costs'
    )
    
    maintenance_cost_current_year = fields.Float(
        string='Coût maintenance année',
        compute='_compute_maintenance_costs'
    )
    
    utilization_rate = fields.Float(
        string='Taux d\'utilisation (%)',
        compute='_compute_utilization_rate'
    )
    
    # QR Code
    qr_code = fields.Binary(
        string='QR Code',
        compute='_compute_qr_code'
    )
    
    # Documents
    vehicle_documents = fields.Many2many(
        'ir.attachment',
        'vehicle_document_rel',
        'vehicle_id',
        'attachment_id',
        string='Documents du véhicule'
    )
    
    # Métadonnées
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Couleur', default=0)
    sequence = fields.Integer(default=10)
    
    @api.depends('seating_capacity', 'standing_capacity')
    def _compute_total_capacity(self):
        """Calculer la capacité totale"""
        for vehicle in self:
            vehicle.total_capacity = vehicle.seating_capacity + vehicle.standing_capacity
    
    @api.depends('current_odometer', 'initial_odometer')
    def _compute_total_distance(self):
        """Calculer la distance totale parcourue"""
        for vehicle in self:
            vehicle.total_distance = max(0, vehicle.current_odometer - vehicle.initial_odometer)
    
    @api.depends('total_distance', 'purchase_date')
    def _compute_daily_average_km(self):
        """Calculer la moyenne quotidienne de kilomètres"""
        for vehicle in self:
            if vehicle.purchase_date and vehicle.total_distance > 0:
                days = (date.today() - vehicle.purchase_date).days
                if days > 0:
                    vehicle.daily_average_km = vehicle.total_distance / days
                else:
                    vehicle.daily_average_km = 0.0
            else:
                vehicle.daily_average_km = 0.0
    
    @api.depends('next_technical_control')
    def _compute_technical_control_valid(self):
        """Vérifier la validité du contrôle technique"""
        today = date.today()
        for vehicle in self:
            vehicle.technical_control_valid = (
                vehicle.next_technical_control and 
                vehicle.next_technical_control >= today
            )
    
    @api.depends('trip_ids')
    def _compute_statistics(self):
        """Calculer les statistiques du véhicule"""
        for vehicle in self:
            vehicle.total_trips = len(vehicle.trip_ids)
            
            # Calculer le nombre d'étudiants transportés (unique)
            students = vehicle.trip_ids.mapped('student_ids')
            unique_students = set()
            for student_list in students:
                unique_students.update(student_list.ids)
            vehicle.total_students_transported = len(unique_students)
    
    @api.depends('maintenance_ids.total_cost')
    def _compute_maintenance_costs(self):
        """Calculer les coûts de maintenance"""
        for vehicle in self:
            vehicle.maintenance_cost_total = sum(vehicle.maintenance_ids.mapped('total_cost'))
            
            # Coût de l'année en cours
            current_year = date.today().year
            current_year_maintenances = vehicle.maintenance_ids.filtered(
                lambda m: m.maintenance_date and m.maintenance_date.year == current_year
            )
            vehicle.maintenance_cost_current_year = sum(current_year_maintenances.mapped('total_cost'))
    
    def _compute_utilization_rate(self):
        """Calculer le taux d'utilisation"""
        for vehicle in self:
            # Calculer sur les 30 derniers jours
            thirty_days_ago = date.today() - timedelta(days=30)
            recent_trips = vehicle.trip_ids.filtered(
                lambda t: t.trip_date >= thirty_days_ago
            )
            
            # Supposer 20 jours ouvrables par mois
            if len(recent_trips) > 0:
                vehicle.utilization_rate = min(100.0, (len(recent_trips) / 20) * 100)
            else:
                vehicle.utilization_rate = 0.0
    
    def _compute_qr_code(self):
        """Générer le QR code du véhicule"""
        for vehicle in self:
            if vehicle.id:
                # Informations essentielles du véhicule
                vehicle_info = {
                    'id': vehicle.id,
                    'name': vehicle.name,
                    'license_plate': vehicle.license_plate,
                    'capacity': vehicle.total_capacity,
                    'type': vehicle.vehicle_type,
                }
                
                # Générer le QR code
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(str(vehicle_info))
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convertir en base64
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                vehicle.qr_code = base64.b64encode(buffer.getvalue())
            else:
                vehicle.qr_code = False
    
    @api.model
    def create(self, vals):
        """Créer un véhicule avec code automatique"""
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('transport.vehicle') or '/'
        
        return super().create(vals)
    
    @api.constrains('license_plate')
    def _check_license_plate_unique(self):
        """Vérifier l'unicité de la plaque d'immatriculation"""
        for vehicle in self:
            if self.search_count([
                ('license_plate', '=', vehicle.license_plate),
                ('id', '!=', vehicle.id)
            ]) > 0:
                raise ValidationError(_('Cette plaque d\'immatriculation existe déjà.'))
    
    @api.constrains('year')
    def _check_year(self):
        """Valider l'année du véhicule"""
        current_year = date.today().year
        for vehicle in self:
            if vehicle.year < 1990 or vehicle.year > current_year + 1:
                raise ValidationError(_('L\'année du véhicule doit être entre 1990 et %d.') % (current_year + 1))
    
    @api.constrains('seating_capacity')
    def _check_capacity(self):
        """Valider la capacité"""
        for vehicle in self:
            if vehicle.seating_capacity <= 0:
                raise ValidationError(_('La capacité doit être positive.'))
    
    def action_set_in_service(self):
        """Mettre en service"""
        self.ensure_one()
        
        # Vérifications avant mise en service
        if not self.technical_control_valid:
            raise UserError(_('Le contrôle technique doit être valide.'))
        
        if not self.insurance_end_date or self.insurance_end_date < date.today():
            raise UserError(_('L\'assurance doit être valide.'))
        
        self.write({
            'state': 'active',
            'operational_status': 'available'
        })
        
        self.message_post(body=_('Véhicule mis en service'))
    
    def action_set_maintenance(self):
        """Mettre en maintenance"""
        self.ensure_one()
        
        # Vérifier s'il y a des trajets en cours
        active_trips = self.trip_ids.filtered(lambda t: t.state == 'in_progress')
        if active_trips:
            raise UserError(_('Impossible de mettre en maintenance. Des trajets sont en cours.'))
        
        self.write({
            'state': 'maintenance',
            'operational_status': 'maintenance'
        })
        
        # Créer une maintenance préventive
        self.env['transport.maintenance'].create({
            'vehicle_id': self.id,
            'maintenance_type': 'preventive',
            'description': _('Maintenance programmée'),
            'maintenance_date': fields.Date.today(),
            'state': 'scheduled',
        })
        
        self.message_post(body=_('Véhicule mis en maintenance'))
    
    def action_emergency_stop(self):
        """Arrêt d'urgence"""
        self.ensure_one()
        
        self.write({
            'operational_status': 'emergency'
        })
        
        # Notifier tous les trajets en cours
        active_trips = self.trip_ids.filtered(lambda t: t.state == 'in_progress')
        for trip in active_trips:
            trip.action_emergency_stop()
        
        # Créer une urgence
        self.env['transport.emergency'].create({
            'vehicle_id': self.id,
            'emergency_type': 'vehicle_breakdown',
            'description': _('Arrêt d\'urgence du véhicule %s') % self.name,
            'location': self.current_location,
            'latitude': self.current_latitude,
            'longitude': self.current_longitude,
        })
        
        self.message_post(
            body=_('ARRÊT D\'URGENCE déclenché'),
            message_type='notification'
        )
    
    def action_update_location(self, latitude, longitude, location_name=None):
        """Mettre à jour la position GPS"""
        self.ensure_one()
        
        vals = {
            'current_latitude': latitude,
            'current_longitude': longitude,
            'last_gps_update': fields.Datetime.now(),
        }
        
        if location_name:
            vals['current_location'] = location_name
        
        self.write(vals)
        
        # Enregistrer dans l'historique de suivi
        self.env['transport.tracking'].create({
            'vehicle_id': self.id,
            'latitude': latitude,
            'longitude': longitude,
            'location_name': location_name,
            'timestamp': fields.Datetime.now(),
            'speed': 0,  # TODO: Calculer la vitesse
        })
    
    def action_schedule_maintenance(self):
        """Programmer une maintenance"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Programmer maintenance'),
            'res_model': 'transport.maintenance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_vehicle_id': self.id,
            },
        }
    
    def action_view_trips(self):
        """Voir les trajets du véhicule"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Trajets - %s') % self.name,
            'res_model': 'transport.trip',
            'view_mode': 'tree,form,calendar',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
    
    def action_view_maintenance(self):
        """Voir l'historique de maintenance"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Maintenance - %s') % self.name,
            'res_model': 'transport.maintenance',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
    
    def action_view_tracking(self):
        """Voir le suivi GPS"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Suivi GPS - %s') % self.name,
            'res_model': 'transport.tracking',
            'view_mode': 'tree,map',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
    
    def action_vehicle_inspection(self):
        """Inspection du véhicule"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Inspection véhicule'),
            'res_model': 'transport.inspection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_vehicle_id': self.id,
            },
        }
    
    def get_vehicle_status(self):
        """Obtenir le statut complet du véhicule"""
        self.ensure_one()
        
        # Vérifier les alertes
        alerts = []
        
        # Contrôle technique
        if not self.technical_control_valid:
            days_overdue = (date.today() - self.next_technical_control).days if self.next_technical_control else 0
            alerts.append({
                'type': 'technical_control',
                'message': _('Contrôle technique expiré'),
                'severity': 'critical' if days_overdue > 0 else 'warning',
                'days_overdue': days_overdue,
            })
        
        # Assurance
        if self.insurance_end_date:
            days_to_expiry = (self.insurance_end_date - date.today()).days
            if days_to_expiry <= 30:
                alerts.append({
                    'type': 'insurance',
                    'message': _('Assurance expire bientôt'),
                    'severity': 'critical' if days_to_expiry <= 0 else 'warning',
                    'days_to_expiry': days_to_expiry,
                })
        
        # Maintenance préventive
        if self.current_odometer > 0:
            km_since_last_maintenance = 0  # TODO: Calculer depuis dernière maintenance
            if km_since_last_maintenance > 10000:  # 10 000 km
                alerts.append({
                    'type': 'maintenance',
                    'message': _('Maintenance préventive recommandée'),
                    'severity': 'medium',
                    'km_overdue': km_since_last_maintenance - 10000,
                })
        
        return {
            'vehicle_info': {
                'name': self.name,
                'license_plate': self.license_plate,
                'state': self.state,
                'operational_status': self.operational_status,
                'current_location': self.current_location,
            },
            'capacity_info': {
                'total_capacity': self.total_capacity,
                'seating_capacity': self.seating_capacity,
                'wheelchair_spaces': self.wheelchair_spaces,
            },
            'technical_info': {
                'current_odometer': self.current_odometer,
                'fuel_level': 0,  # TODO: Intégrer capteur carburant
                'last_maintenance': None,  # TODO: Calculer
                'next_maintenance_due': None,  # TODO: Calculer
            },
            'alerts': alerts,
            'statistics': {
                'total_trips': self.total_trips,
                'utilization_rate': self.utilization_rate,
                'maintenance_cost_year': self.maintenance_cost_current_year,
                'daily_average_km': self.daily_average_km,
            }
        }
    
    @api.model
    def check_vehicle_alerts(self):
        """Vérifier les alertes de tous les véhicules"""
        vehicles = self.search([('state', '=', 'active')])
        alerts_count = 0
        
        for vehicle in vehicles:
            status = vehicle.get_vehicle_status()
            for alert in status['alerts']:
                if alert['severity'] in ['critical', 'warning']:
                    # Créer une activité de rappel
                    vehicle.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary=alert['message'],
                        note=_('Véhicule %s: %s') % (vehicle.name, alert['message']),
                        user_id=self.env.ref('base.user_admin').id,
                    )
                    alerts_count += 1
        
        return alerts_count
    
    @api.model
    def get_fleet_statistics(self):
        """Obtenir les statistiques de la flotte"""
        vehicles = self.search([])
        
        # Répartition par état
        state_stats = {}
        for vehicle in vehicles:
            state = vehicle.state
            state_stats[state] = state_stats.get(state, 0) + 1
        
        # Répartition par type
        type_stats = {}
        for vehicle in vehicles:
            vtype = vehicle.vehicle_type
            type_stats[vtype] = type_stats.get(vtype, 0) + 1
        
        # Statistiques d'âge
        current_year = date.today().year
        age_stats = {
            'new': 0,      # < 3 ans
            'recent': 0,   # 3-7 ans
            'old': 0,      # 7-15 ans
            'very_old': 0, # > 15 ans
        }
        
        for vehicle in vehicles:
            age = current_year - vehicle.year
            if age < 3:
                age_stats['new'] += 1
            elif age < 7:
                age_stats['recent'] += 1
            elif age < 15:
                age_stats['old'] += 1
            else:
                age_stats['very_old'] += 1
        
        # Capacité totale de la flotte
        total_capacity = sum(vehicles.mapped('total_capacity'))
        average_capacity = total_capacity / len(vehicles) if vehicles else 0
        
        # Coûts
        total_purchase_value = sum(vehicles.mapped('purchase_price'))
        total_current_value = sum(vehicles.mapped('current_value'))
        total_maintenance_cost = sum(vehicles.mapped('maintenance_cost_current_year'))
        
        # Utilisation
        active_vehicles = vehicles.filtered(lambda v: v.state == 'active')
        average_utilization = sum(active_vehicles.mapped('utilization_rate')) / len(active_vehicles) if active_vehicles else 0
        
        return {
            'fleet_size': len(vehicles),
            'active_vehicles': len(active_vehicles),
            'state_distribution': state_stats,
            'type_distribution': type_stats,
            'age_distribution': age_stats,
            'capacity_stats': {
                'total_capacity': total_capacity,
                'average_capacity': average_capacity,
            },
            'financial_stats': {
                'total_purchase_value': total_purchase_value,
                'total_current_value': total_current_value,
                'depreciation_amount': total_purchase_value - total_current_value,
                'maintenance_cost_year': total_maintenance_cost,
            },
            'utilization_stats': {
                'average_utilization': average_utilization,
                'vehicles_underutilized': len(active_vehicles.filtered(lambda v: v.utilization_rate < 50)),
                'vehicles_overutilized': len(active_vehicles.filtered(lambda v: v.utilization_rate > 80)),
            }
        }
    
    def calculate_route_efficiency(self, route_id):
        """Calculer l'efficacité pour un itinéraire donné"""
        self.ensure_one()
        
        route = self.env['transport.route'].browse(route_id)
        if not route.exists():
            return {}
        
        # Trajets sur cette route
        route_trips = self.trip_ids.filtered(lambda t: t.route_id.id == route_id)
        
        if not route_trips:
            return {'efficiency': 0, 'reason': 'No trips data'}
        
        # Calculer l'efficacité basée sur:
        # - Taux de remplissage
        # - Ponctualité
        # - Consommation de carburant
        
        total_capacity_used = sum(route_trips.mapped('student_count'))
        total_capacity_available = len(route_trips) * self.total_capacity
        
        fill_rate = (total_capacity_used / total_capacity_available * 100) if total_capacity_available > 0 else 0
        
        # Ponctualité (% de trajets à l'heure)
        on_time_trips = route_trips.filtered(lambda t: not t.is_delayed)
        punctuality_rate = (len(on_time_trips) / len(route_trips) * 100) if route_trips else 0
        
        # Score d'efficacité global
        efficiency_score = (fill_rate * 0.6 + punctuality_rate * 0.4)
        
        return {
            'efficiency': efficiency_score,
            'fill_rate': fill_rate,
            'punctuality_rate': punctuality_rate,
            'total_trips': len(route_trips),
            'average_students': total_capacity_used / len(route_trips) if route_trips else 0,
        }
