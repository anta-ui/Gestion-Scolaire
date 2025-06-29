# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduLocation(models.Model):
    """Emplacements et lieux de pointage"""
    _name = 'edu.location'
    _description = 'Emplacement'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom de l\'emplacement',
        required=True,
        help="Nom de l'emplacement"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=20,
        help="Code unique de l'emplacement"
    )
    
    description = fields.Text(
        string='Description',
        help="Description de l'emplacement"
    )
    
    location_type = fields.Selection([
        ('classroom', 'Salle de classe'),
        ('laboratory', 'Laboratoire'),
        ('library', 'Bibliothèque'),
        ('cafeteria', 'Cafétéria'),
        ('gymnasium', 'Gymnase'),
        ('playground', 'Cour de récréation'),
        ('entrance', 'Entrée'),
        ('exit', 'Sortie'),
        ('office', 'Bureau'),
        ('meeting_room', 'Salle de réunion'),
        ('auditorium', 'Auditorium'),
        ('parking', 'Parking'),
        ('other', 'Autre')
    ], string='Type d\'emplacement', required=True, default='classroom')
    
    building = fields.Char(
        string='Bâtiment',
        help="Nom ou numéro du bâtiment"
    )
    
    floor = fields.Char(
        string='Étage',
        help="Étage de l'emplacement"
    )
    
    room_number = fields.Char(
        string='Numéro de salle',
        help="Numéro de la salle"
    )
    
    capacity = fields.Integer(
        string='Capacité',
        default=30,
        help="Nombre maximum de personnes"
    )
    
    # Coordonnées GPS
    latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        help="Latitude GPS"
    )
    
    longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        help="Longitude GPS"
    )
    
    gps_radius = fields.Float(
        string='Rayon GPS (m)',
        default=50.0,
        digits=(8, 2),
        help="Rayon de géolocalisation autorisé"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True,
        help="Emplacement actif"
    )
    
    # Relations
    device_ids = fields.One2many(
        'edu.attendance.device',
        'location_id',
        string='Dispositifs de pointage'
    )
    
    @api.constrains('code')
    def _check_unique_code(self):
        """Vérifie l'unicité du code"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Le code '%s' existe déjà") % record.code)
    
    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self):
        """Vérifie les coordonnées GPS"""
        for record in self:
            if record.latitude and not (-90 <= record.latitude <= 90):
                raise ValidationError(_("La latitude doit être entre -90 et 90"))
            if record.longitude and not (-180 <= record.longitude <= 180):
                raise ValidationError(_("La longitude doit être entre -180 et 180"))
    
    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            if record.building:
                name += f" ({record.building})"
            result.append((record.id, name))
        return result
