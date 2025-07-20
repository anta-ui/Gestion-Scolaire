# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class EduLocation(models.Model):
    _name = 'edu.location'
    _description = 'Lieu/Salle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Nom', required=True, tracking=True)
    code = fields.Char('Code', required=True, copy=False, tracking=True)
    description = fields.Text('Description')
    
    # Type de lieu
    location_type = fields.Selection([
        ('classroom', 'Salle de classe'),
        ('laboratory', 'Laboratoire'),
        ('library', 'Bibliothèque'),
        ('gymnasium', 'Gymnase'),
        ('auditorium', 'Auditorium'),
        ('office', 'Bureau'),
        ('cafeteria', 'Cafétéria'),
        ('outdoor', 'Extérieur'),
        ('other', 'Autre')
    ], string='Type de lieu', required=True, default='classroom')
    
    # Capacité
    capacity = fields.Integer('Capacité', help="Nombre maximum de personnes")
    current_occupancy = fields.Integer('Occupation actuelle', compute='_compute_occupancy')
    
    # Localisation
    building = fields.Char('Bâtiment')
    floor = fields.Char('Étage')
    room_number = fields.Char('Numéro de salle')
    
    # Coordonnées GPS
    latitude = fields.Float('Latitude', digits=(10, 7))
    longitude = fields.Float('Longitude', digits=(10, 7))
    gps_radius = fields.Integer('Rayon GPS (mètres)', default=50,
                               help="Rayon autorisé pour le pointage géolocalisé")
    
    # Équipements
    has_projector = fields.Boolean('Projecteur')
    has_computer = fields.Boolean('Ordinateur')
    has_whiteboard = fields.Boolean('Tableau blanc')
    has_audio = fields.Boolean('Système audio')
    has_wifi = fields.Boolean('WiFi')
    
    # État
    state = fields.Selection([
        ('available', 'Disponible'),
        ('occupied', 'Occupé'),
        ('maintenance', 'En maintenance'),
        ('reserved', 'Réservé')
    ], string='État', default='available', tracking=True)
    
    # Accessibilité
    is_accessible = fields.Boolean('Accessible aux personnes à mobilité réduite', default=True)
    has_elevator = fields.Boolean('Ascenseur')
    has_ramp = fields.Boolean('Rampes d\'accès')
    
    # Relations
    device_ids = fields.One2many('edu.attendance.device', 'location_id', 'Dispositifs')
    session_ids = fields.One2many('edu.attendance.session', 'location_id', 'Sessions')
    
    # Horaires d'ouverture
    opening_hours = fields.Text('Horaires d\'ouverture')
    is_24h = fields.Boolean('Ouvert 24h/24', default=False)
    
    # Contraintes
    _sql_constraints = [
        ('unique_location_code', 'unique(code)', 'Le code du lieu doit être unique!')
    ]

    @api.model
    def create(self, vals):
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('edu.location') or 'LOC'
        return super().create(vals)
    
    @api.depends('session_ids')
    def _compute_occupancy(self):
        for record in self:
            # Calculer l'occupation actuelle basée sur les sessions en cours
            active_sessions = record.session_ids.filtered(lambda s: s.state in ['open', 'in_progress'])
            record.current_occupancy = sum(len(s.student_ids) for s in active_sessions)

    def action_available(self):
        """Marquer comme disponible"""
        self.write({'state': 'available'})
        return True

    def action_occupied(self):
        """Marquer comme occupé"""
        self.write({'state': 'occupied'})
        return True

    def action_maintenance(self):
        """Mettre en maintenance"""
        self.write({'state': 'maintenance'})
        return True

    def action_reserve(self):
        """Réserver le lieu"""
        self.write({'state': 'reserved'})
        return True

    def get_location_info(self):
        """Obtenir les informations du lieu"""
        return {
            'id': self.id,
            'name': self.name,
            'type': dict(self._fields['location_type'].selection)[self.location_type],
            'capacity': self.capacity,
            'current_occupancy': self.current_occupancy,
            'state': dict(self._fields['state'].selection)[self.state],
            'building': self.building,
            'floor': self.floor,
            'room_number': self.room_number,
            'coordinates': {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'radius': self.gps_radius
            }
        }

    def check_availability(self, start_datetime, end_datetime):
        """Vérifier la disponibilité du lieu sur une période"""
        conflicting_sessions = self.session_ids.filtered(lambda s: 
            s.state in ['scheduled', 'open', 'in_progress'] and
            s.start_datetime < end_datetime and s.end_datetime > start_datetime
        )
        return len(conflicting_sessions) == 0

    def get_schedule(self, date=None):
        """Obtenir l'emploi du temps du lieu"""
        if not date:
            date = fields.Date.today()
        
        sessions = self.session_ids.filtered(lambda s: s.start_datetime.date() == date)
        return sessions.sorted('start_datetime')
