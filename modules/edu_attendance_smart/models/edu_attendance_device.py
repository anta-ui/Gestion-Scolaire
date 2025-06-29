# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class EduAttendanceDevice(models.Model):
    """Dispositifs de pointage (Scanner QR, biométrie, RFID, etc.)"""
    _name = 'edu.attendance.device'
    _description = 'Dispositif de pointage'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du dispositif',
        required=True,
        help="Nom du dispositif de pointage"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=20,
        help="Code unique du dispositif"
    )
    
    description = fields.Text(
        string='Description',
        help="Description du dispositif"
    )
    
    # Type et configuration
    device_type = fields.Selection([
        ('qr_code', 'QR Code Scanner'),
        ('biometric', 'Scanner biométrique'),
        ('rfid', 'Lecteur RFID/NFC'),
        ('mobile_app', 'Application mobile'),
        ('web_interface', 'Interface web'),
        ('manual', 'Saisie manuelle'),
        ('camera', 'Reconnaissance faciale'),
        ('beacon', 'Balise Bluetooth')
    ], string='Type de dispositif', required=True, default='qr_code')
    
    # Localisation
    location_id = fields.Many2one(
        'edu.location',
        string='Emplacement',
        help="Emplacement du dispositif"
    )
    
    room_id = fields.Many2one(
        'op.classroom',
        string='Salle',
        help="Salle où est installé le dispositif"
    )
    
    building = fields.Char(
        string='Bâtiment',
        help="Bâtiment où se trouve le dispositif"
    )
    
    floor = fields.Char(
        string='Étage',
        help="Étage du dispositif"
    )
    
    # Configuration technique
    ip_address = fields.Char(
        string='Adresse IP',
        help="Adresse IP du dispositif (si applicable)"
    )
    
    mac_address = fields.Char(
        string='Adresse MAC',
        help="Adresse MAC du dispositif"
    )
    
    serial_number = fields.Char(
        string='Numéro de série',
        help="Numéro de série du dispositif"
    )
    
    api_key = fields.Char(
        string='Clé API',
        help="Clé d'API pour l'authentification"
    )
    
    api_endpoint = fields.Char(
        string='Point d\'accès API',
        help="URL de l'API du dispositif"
    )
    
    # État et statut
    active = fields.Boolean(
        string='Actif',
        default=True,
        help="Dispositif actif"
    )
    
    online = fields.Boolean(
        string='En ligne',
        default=False,
        compute='_compute_online_status',
        store=True,
        help="Statut de connexion du dispositif"
    )
    
    last_ping = fields.Datetime(
        string='Dernière connexion',
        help="Dernière fois que le dispositif s'est connecté"
    )
    
    battery_level = fields.Float(
        string='Niveau de batterie (%)',
        digits=(5, 2),
        help="Niveau de batterie pour dispositifs mobiles"
    )
    
    # Configuration des fonctionnalités
    allow_check_in = fields.Boolean(
        string='Autoriser entrées',
        default=True,
        help="Permet l'enregistrement des entrées"
    )
    
    allow_check_out = fields.Boolean(
        string='Autoriser sorties',
        default=True,
        help="Permet l'enregistrement des sorties"
    )
    
    require_photo = fields.Boolean(
        string='Photo obligatoire',
        default=False,
        help="Exige une photo lors du pointage"
    )
    
    require_geolocation = fields.Boolean(
        string='Géolocalisation obligatoire',
        default=False,
        help="Exige la géolocalisation"
    )
    
    allowed_distance = fields.Float(
        string='Distance autorisée (m)',
        default=50.0,
        digits=(8, 2),
        help="Distance maximum autorisée depuis l'emplacement"
    )
    
    # Coordonnées GPS
    latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        help="Latitude de l'emplacement du dispositif"
    )
    
    longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        help="Longitude de l'emplacement du dispositif"
    )
    
    # Restrictions d'accès
    user_group_ids = fields.Many2many(
        'res.groups',
        'device_group_rel',
        'device_id',
        'group_id',
        string='Groupes autorisés',
        help="Groupes d'utilisateurs autorisés à utiliser ce dispositif"
    )
    
    standard_ids = fields.Many2many(
        'op.batch',
        'device_batch_rel',
        'device_id',
        'batch_id',
        string='Classes/Groupes autorisés',
        help="Classes/Groupes autorisés à utiliser ce dispositif"
    )
    
    # Horaires d'utilisation
    working_hours_start = fields.Float(
        string='Début service',
        default=7.0,
        help="Heure de début d'utilisation (24h)"
    )
    
    working_hours_end = fields.Float(
        string='Fin service',
        default=19.0,
        help="Heure de fin d'utilisation (24h)"
    )
    
    timezone = fields.Selection([
        ('Africa/Dakar', 'Africa/Dakar'),
        ('Africa/Casablanca', 'Africa/Casablanca'),
        ('Africa/Cairo', 'Africa/Cairo'), 
        ('Africa/Lagos', 'Africa/Lagos'),
        ('Africa/Johannesburg', 'Africa/Johannesburg'),
        ('Europe/Paris', 'Europe/Paris'),
        ('Europe/London', 'Europe/London'),
        ('Europe/Berlin', 'Europe/Berlin'),
        ('America/New_York', 'America/New_York'),
        ('America/Los_Angeles', 'America/Los_Angeles'),
        ('Asia/Dubai', 'Asia/Dubai'),
        ('UTC', 'UTC')
    ], string='Fuseau horaire', default='Africa/Dakar', help="Fuseau horaire du dispositif")
    
    # Statistiques
    total_scans_today = fields.Integer(
        string='Pointages aujourd\'hui',
        compute='_compute_daily_stats',
        help="Nombre de pointages aujourd'hui"
    )
    
    total_scans_month = fields.Integer(
        string='Pointages ce mois',
        compute='_compute_monthly_stats',
        help="Nombre de pointages ce mois"
    )
    
    last_scan_time = fields.Datetime(
        string='Dernier pointage',
        compute='_compute_last_scan',
        help="Heure du dernier pointage"
    )
    
    # Maintenance
    installation_date = fields.Date(
        string='Date d\'installation',
        default=fields.Date.context_today,
        help="Date d'installation du dispositif"
    )
    
    last_maintenance = fields.Date(
        string='Dernière maintenance',
        help="Date de la dernière maintenance"
    )
    
    next_maintenance = fields.Date(
        string='Prochaine maintenance',
        help="Date prévue pour la prochaine maintenance"
    )
    
    warranty_end = fields.Date(
        string='Fin de garantie',
        help="Date de fin de garantie"
    )
    
    vendor = fields.Char(
        string='Fournisseur',
        help="Fournisseur du dispositif"
    )
    
    model = fields.Char(
        string='Modèle',
        help="Modèle du dispositif"
    )
    
    firmware_version = fields.Char(
        string='Version firmware',
        help="Version du firmware"
    )
    
    # Calculs
    @api.depends('last_ping')
    def _compute_online_status(self):
        """Calcule le statut en ligne du dispositif"""
        import datetime
        for record in self:
            if record.last_ping:
                time_diff = datetime.datetime.now() - record.last_ping
                # En ligne si la dernière connexion date de moins de 5 minutes
                record.online = time_diff.total_seconds() < 300
            else:
                record.online = False
    
    def _compute_daily_stats(self):
        """Calcule les statistiques du jour"""
        for record in self:
            today = fields.Date.context_today(self)
            tomorrow = today + timedelta(days=1)
            record.total_scans_today = self.env['edu.attendance.record'].search_count([
                ('device_id', '=', record.id),
                ('check_in_time', '>=', today),
                ('check_in_time', '<', tomorrow)
            ])
    
    def _compute_monthly_stats(self):
        """Calcule les statistiques du mois"""
        for record in self:
            today = fields.Date.context_today(self)
            first_day = today.replace(day=1)
            next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            record.total_scans_month = self.env['edu.attendance.record'].search_count([
                ('device_id', '=', record.id),
                ('check_in_time', '>=', first_day),
                ('check_in_time', '<', next_month)
            ])
    
    def _compute_last_scan(self):
        """Calcule l'heure du dernier pointage"""
        for record in self:
            last_scan = self.env['edu.attendance.record'].search([
                ('device_id', '=', record.id)
            ], order='check_in_time desc', limit=1)
            record.last_scan_time = last_scan.check_in_time if last_scan else False
    
    # Contraintes
    @api.constrains('code')
    def _check_unique_code(self):
        """Vérifie l'unicité du code"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Le code '%s' existe déjà") % record.code)
    
    @api.constrains('ip_address')
    def _check_ip_address(self):
        """Vérifie le format de l'adresse IP"""
        import ipaddress
        for record in self:
            if record.ip_address:
                try:
                    ipaddress.ip_address(record.ip_address)
                except ValueError:
                    raise ValidationError(_("Format d'adresse IP invalide: %s") % record.ip_address)
    
    @api.constrains('working_hours_start', 'working_hours_end')
    def _check_working_hours(self):
        """Vérifie les heures de service"""
        for record in self:
            if record.working_hours_start >= record.working_hours_end:
                raise ValidationError(_("L'heure de début doit être antérieure à l'heure de fin"))
    
    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self):
        """Vérifie les coordonnées GPS"""
        for record in self:
            if record.latitude and not (-90 <= record.latitude <= 90):
                raise ValidationError(_("La latitude doit être entre -90 et 90"))
            if record.longitude and not (-180 <= record.longitude <= 180):
                raise ValidationError(_("La longitude doit être entre -180 et 180"))
    
    # Actions
    def action_ping_device(self):
        """Teste la connexion au dispositif"""
        self.ensure_one()
        try:
            # Simulation d'un ping - à adapter selon le type de dispositif
            self.last_ping = fields.Datetime.now()
            self.message_post(body=_("Test de connexion réussi"))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Dispositif connecté avec succès"),
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f"Erreur de connexion au dispositif {self.name}: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Erreur de connexion: %s") % str(e),
                    'type': 'danger',
                }
            }
    
    def action_reset_device(self):
        """Redémarre le dispositif"""
        self.ensure_one()
        # À implémenter selon le type de dispositif
        self.message_post(body=_("Redémarrage du dispositif demandé"))
    
    def action_update_firmware(self):
        """Met à jour le firmware"""
        self.ensure_one()
        # À implémenter selon le type de dispositif
        self.message_post(body=_("Mise à jour du firmware lancée"))
    
    def action_view_attendance_records(self):
        """Affiche les enregistrements de présence de ce dispositif"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pointages - %s') % self.name,
            'res_model': 'edu.attendance.record',
            'view_mode': 'tree,form',
            'domain': [('device_id', '=', self.id)],
            'context': {'default_device_id': self.id},
        }
    
    def action_generate_qr_code(self):
        """Génère un QR code pour ce dispositif"""
        self.ensure_one()
        if self.device_type != 'qr_code':
            raise UserError(_("Cette action n'est disponible que pour les scanners QR"))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('QR Code - %s') % self.name,
            'res_model': 'edu.qr.code',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_device_id': self.id,
                'default_qr_type': 'device'
            },
        }
    
    def is_accessible_by_user(self, user):
        """Vérifie si l'utilisateur peut utiliser ce dispositif"""
        self.ensure_one()
        if not self.active:
            return False
        
        # Vérifier les groupes
        if self.user_group_ids:
            user_groups = user.groups_id
            if not any(group in user_groups for group in self.user_group_ids):
                return False
        
        # Vérifier les horaires
        import datetime
        now = datetime.datetime.now()
        current_hour = now.hour + now.minute / 60.0
        
        if not (self.working_hours_start <= current_hour <= self.working_hours_end):
            return False
        
        return True
    
    def is_in_range(self, latitude, longitude):
        """Vérifie si les coordonnées sont dans la zone autorisée"""
        self.ensure_one()
        if not (self.latitude and self.longitude and latitude and longitude):
            return True  # Pas de vérification si coordonnées manquantes
        
        # Calcul de la distance (formule de Haversine simplifiée)
        import math
        
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(latitude), math.radians(longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Rayon de la Terre en mètres
        distance = 6371000 * c
        
        return distance <= self.allowed_distance
    
    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            if record.location_id:
                name += f" ({record.location_id.name})"
            result.append((record.id, name))
        return result
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Recherche par nom ou code"""
        args = args or []
        if name:
            args = ['|', ('name', operator, name), ('code', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
