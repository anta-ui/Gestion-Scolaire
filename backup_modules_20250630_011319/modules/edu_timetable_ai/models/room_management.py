# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RoomEnhanced(models.Model):
    _name = 'edu.room.enhanced'
    _description = 'Salle de classe améliorée'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'building_id, floor, name'

    # Informations de base
    name = fields.Char(
        string='Nom de la salle',
        required=True,
        tracking=True
    )
    
    code = fields.Char(
        string='Code salle',
        help='Code unique de la salle (ex: A101, B203)',
        tracking=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    # Localisation
    building_id = fields.Many2one(
        'edu.building',
        string='Bâtiment',
        required=True,
        tracking=True
    )
    
    floor = fields.Integer(
        string='Étage',
        default=0,
        tracking=True
    )
    
    wing = fields.Char(
        string='Aile/Section',
        help='Aile ou section du bâtiment'
    )
    
    # Caractéristiques physiques
    capacity = fields.Integer(
        string='Capacité',
        required=True,
        default=30,
        tracking=True
    )
    
    surface_area = fields.Float(
        string='Surface (m²)',
        help='Surface en mètres carrés'
    )
    
    room_type = fields.Selection([
        ('classroom', 'Salle de classe'),
        ('laboratory', 'Laboratoire'),
        ('computer_lab', 'Salle informatique'),
        ('conference', 'Salle de conférence'),
        ('library', 'Bibliothèque'),
        ('gym', 'Gymnase'),
        ('auditorium', 'Amphithéâtre'),
        ('workshop', 'Atelier'),
        ('art_room', 'Salle d\'art'),
        ('music_room', 'Salle de musique'),
        ('cafeteria', 'Cafétéria'),
        ('office', 'Bureau'),
        ('storage', 'Stockage'),
        ('other', 'Autre'),
    ], string='Type de salle', default='classroom', required=True, tracking=True)
    
    # Équipements et ressources
    equipment_ids = fields.Many2many(
        'edu.room.equipment',
        'room_equipment_rel',
        'room_id',
        'equipment_id',
        string='Équipements'
    )
    
    has_projector = fields.Boolean(
        string='Projecteur',
        default=False
    )
    
    has_whiteboard = fields.Boolean(
        string='Tableau blanc',
        default=True
    )
    
    has_computer = fields.Boolean(
        string='Ordinateur',
        default=False
    )
    
    has_internet = fields.Boolean(
        string='Internet/WiFi',
        default=True
    )
    
    has_air_conditioning = fields.Boolean(
        string='Climatisation',
        default=False
    )
    
    has_audio_system = fields.Boolean(
        string='Système audio',
        default=False
    )
    
    # Accessibilité
    is_accessible = fields.Boolean(
        string='Accessible PMR',
        default=False,
        help='Accessible aux personnes à mobilité réduite'
    )
    
    accessibility_features = fields.Text(
        string='Caractéristiques d\'accessibilité'
    )
    
    # Disponibilité et réservation
    is_bookable = fields.Boolean(
        string='Réservable',
        default=True,
        help='La salle peut-elle être réservée?'
    )
    
    booking_lead_time = fields.Integer(
        string='Délai de réservation (heures)',
        default=24,
        help='Délai minimum pour réserver la salle'
    )
    
    max_booking_duration = fields.Integer(
        string='Durée max de réservation (heures)',
        default=8,
        help='Durée maximum d\'une réservation'
    )
    
    # État et maintenance
    state = fields.Selection([
        ('available', 'Disponible'),
        ('occupied', 'Occupée'),
        ('maintenance', 'En maintenance'),
        ('renovation', 'En rénovation'),
        ('closed', 'Fermée'),
        ('reserved', 'Réservée'),
    ], string='État', default='available', tracking=True)
    
    maintenance_notes = fields.Text(
        string='Notes de maintenance'
    )
    
    last_maintenance = fields.Date(
        string='Dernière maintenance'
    )
    
    next_maintenance = fields.Date(
        string='Prochaine maintenance'
    )
    
    # Responsabilité
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsable',
        help='Responsable de la salle'
    )
    
    # Statistiques d'utilisation
    utilization_rate = fields.Float(
        string='Taux d\'utilisation (%)',
        compute='_compute_utilization_rate',
        help='Pourcentage d\'utilisation de la salle'
    )
    
    booking_count = fields.Integer(
        string='Nombre de réservations',
        compute='_compute_booking_stats'
    )
    
    hours_used_week = fields.Float(
        string='Heures utilisées/semaine',
        compute='_compute_booking_stats'
    )
    
    # Relations
    schedule_line_ids = fields.One2many(
        'edu.schedule.slot',
        'room_id',
        string='Créneaux programmés'
    )
    
    booking_ids = fields.One2many(
        'edu.room.booking',
        'room_id',
        string='Réservations'
    )
    
    # Configuration IA
    ai_priority = fields.Integer(
        string='Priorité IA',
        default=5,
        help='Priorité pour l\'assignation automatique (1-10)'
    )
    
    ai_preferences = fields.Text(
        string='Préférences IA',
        help='Préférences spécifiques pour l\'IA (JSON)'
    )
    
    # Métadonnées
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Couleur', default=0)
    
    @api.depends('schedule_line_ids')
    def _compute_utilization_rate(self):
        """Calculer le taux d'utilisation de la salle"""
        for room in self:
            # Calculer sur la semaine courante
            # TODO: Implémenter le calcul réel
            room.utilization_rate = 0.0
    
    @api.depends('booking_ids', 'schedule_line_ids')
    def _compute_booking_stats(self):
        """Calculer les statistiques de réservation"""
        for room in self:
            # TODO: Implémenter le calcul réel
            room.booking_count = len(room.booking_ids)
            room.hours_used_week = 0.0
    
    @api.constrains('capacity')
    def _check_capacity(self):
        """Valider la capacité"""
        for room in self:
            if room.capacity <= 0:
                raise ValidationError(_('La capacité doit être positive.'))
    
    def action_view_schedule(self):
        """Voir le planning de la salle"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Planning - %s') % self.name,
            'res_model': 'edu.schedule.slot',
            'view_mode': 'calendar,tree,form',
            'domain': [('room_id', '=', self.id)],
            'context': {
                'default_room_id': self.id,
            },
        }
    
    def action_book_room(self):
        """Réserver la salle"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Réserver - %s') % self.name,
            'res_model': 'edu.room.booking.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_room_id': self.id,
            },
        }
    
    def check_availability(self, date, start_time, end_time):
        """Vérifier la disponibilité de la salle"""
        if self.state not in ['available', 'reserved']:
            return False
        
        # Vérifier les conflits avec les créneaux existants
        conflicting_slots = self.env['edu.schedule.slot'].search([
            ('room_id', '=', self.id),
            ('date', '=', date),
            ('state', 'not in', ['cancelled']),
            '|',
            '&', ('start_time', '<=', start_time), ('end_time', '>', start_time),
            '&', ('start_time', '<', end_time), ('end_time', '>=', end_time),
        ])
        
        return len(conflicting_slots) == 0
    
    def get_available_slots(self, date):
        """Obtenir les créneaux disponibles pour une date"""
        # Récupérer tous les créneaux occupés
        occupied_slots = self.env['edu.schedule.slot'].search([
            ('room_id', '=', self.id),
            ('date', '=', date),
            ('state', 'not in', ['cancelled']),
        ]).mapped(lambda s: (s.start_time, s.end_time))
        
        # Générer les créneaux libres
        # TODO: Implémenter la logique de génération
        return []


class Building(models.Model):
    _name = 'edu.building'
    _description = 'Bâtiment'
    _order = 'name'

    name = fields.Char(
        string='Nom du bâtiment',
        required=True
    )
    
    code = fields.Char(
        string='Code bâtiment',
        help='Code unique du bâtiment'
    )
    
    address = fields.Text(
        string='Adresse'
    )
    
    floors_count = fields.Integer(
        string='Nombre d\'étages',
        default=1
    )
    
    room_ids = fields.One2many(
        'edu.room.enhanced',
        'building_id',
        string='Salles'
    )
    
    room_count = fields.Integer(
        string='Nombre de salles',
        compute='_compute_room_count'
    )
    
    total_capacity = fields.Integer(
        string='Capacité totale',
        compute='_compute_total_capacity'
    )
    
    active = fields.Boolean(default=True)
    
    @api.depends('room_ids')
    def _compute_room_count(self):
        for building in self:
            building.room_count = len(building.room_ids)
    
    @api.depends('room_ids.capacity')
    def _compute_total_capacity(self):
        for building in self:
            building.total_capacity = sum(building.room_ids.mapped('capacity'))


class RoomEquipment(models.Model):
    _name = 'edu.room.equipment'
    _description = 'Équipement de salle'
    _order = 'name'

    name = fields.Char(
        string='Nom de l\'équipement',
        required=True
    )
    
    code = fields.Char(
        string='Code équipement'
    )
    
    category = fields.Selection([
        ('audiovisual', 'Audiovisuel'),
        ('computer', 'Informatique'),
        ('furniture', 'Mobilier'),
        ('laboratory', 'Laboratoire'),
        ('sports', 'Sport'),
        ('security', 'Sécurité'),
        ('other', 'Autre'),
    ], string='Catégorie', default='other')
    
    description = fields.Text(
        string='Description'
    )
    
    is_required_for = fields.Selection([
        ('all', 'Tous les cours'),
        ('specific', 'Cours spécifiques'),
        ('optional', 'Optionnel'),
    ], string='Requis pour', default='optional')
    
    active = fields.Boolean(default=True)


class RoomBooking(models.Model):
    _name = 'edu.room.booking'
    _description = 'Réservation de salle'
    _inherit = ['mail.thread']
    _order = 'date desc, start_time'

    name = fields.Char(
        string='Motif de réservation',
        required=True
    )
    
    room_id = fields.Many2one(
        'edu.room.enhanced',
        string='Salle',
        required=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Demandeur',
        required=True,
        default=lambda self: self.env.user
    )
    
    date = fields.Date(
        string='Date',
        required=True
    )
    
    start_time = fields.Float(
        string='Heure de début',
        required=True
    )
    
    end_time = fields.Float(
        string='Heure de fin',
        required=True
    )
    
    purpose = fields.Text(
        string='Objectif'
    )
    
    expected_attendees = fields.Integer(
        string='Nombre de participants attendus'
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('approved', 'Approuvée'),
        ('rejected', 'Rejetée'),
        ('confirmed', 'Confirmée'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
    ], string='État', default='draft', tracking=True)
    
    notes = fields.Text(
        string='Notes'
    )
    
    active = fields.Boolean(default=True)
