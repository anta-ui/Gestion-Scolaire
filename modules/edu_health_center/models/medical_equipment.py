# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MedicalEquipment(models.Model):
    _name = 'medical.equipment'
    _description = 'Équipement Médical'
    _order = 'name'

    name = fields.Char(string='Nom de l\'équipement', required=True)
    equipment_type = fields.Selection([
        ('diagnostic', 'Diagnostic'),
        ('monitoring', 'Surveillance'),
        ('treatment', 'Traitement'),
        ('emergency', 'Urgence'),
        ('laboratory', 'Laboratoire'),
        ('other', 'Autre'),
    ], string='Type d\'équipement', required=True, default='diagnostic')
    
    model = fields.Char(string='Modèle')
    serial_number = fields.Char(string='Numéro de série')
    manufacturer = fields.Char(string='Fabricant')
    
    purchase_date = fields.Date(string='Date d\'achat')
    warranty_expiry = fields.Date(string='Fin de garantie')
    last_maintenance = fields.Date(string='Dernière maintenance')
    next_maintenance = fields.Date(string='Prochaine maintenance')
    
    state = fields.Selection([
        ('available', 'Disponible'),
        ('in_use', 'En utilisation'),
        ('maintenance', 'En maintenance'),
        ('out_of_order', 'Hors service'),
        ('retired', 'Retiré'),
    ], string='État', default='available', required=True)
    
    location = fields.Char(string='Emplacement')
    responsible_user = fields.Many2one('res.users', string='Responsable')
    
    description = fields.Text(string='Description')
    usage_instructions = fields.Text(string='Instructions d\'utilisation')
    safety_notes = fields.Text(string='Notes de sécurité')
    
    active = fields.Boolean(string='Actif', default=True)
    
    # Champs de suivi
    total_usage_hours = fields.Float(string='Heures d\'utilisation totales', default=0.0)
    last_used_date = fields.Datetime(string='Dernière utilisation')
    last_used_by = fields.Many2one('res.users', string='Dernier utilisateur')

    @api.model
    def get_available_equipment(self, equipment_type=None):
        """Retourne les équipements disponibles"""
        domain = [('state', '=', 'available')]
        if equipment_type:
            domain.append(('equipment_type', '=', equipment_type))
        return self.search(domain)

    def action_start_use(self):
        """Démarre l'utilisation de l'équipement"""
        self.write({
            'state': 'in_use',
            'last_used_date': fields.Datetime.now(),
            'last_used_by': self.env.user.id,
        })

    def action_stop_use(self, usage_hours=0):
        """Arrête l'utilisation de l'équipement"""
        self.write({
            'state': 'available',
            'total_usage_hours': self.total_usage_hours + usage_hours,
        })

    def action_send_to_maintenance(self):
        """Envoie l'équipement en maintenance"""
        self.write({
            'state': 'maintenance',
            'last_maintenance': fields.Date.today(),
        })

    def action_mark_out_of_order(self):
        """Marque l'équipement comme hors service"""
        self.write({'state': 'out_of_order'})

    @api.model
    def check_maintenance_due(self):
        """Vérifie les équipements nécessitant une maintenance"""
        today = fields.Date.today()
        equipment_due = self.search([
            ('next_maintenance', '<=', today),
            ('state', 'in', ['available', 'in_use'])
        ])
        
        # Ici on pourrait créer des alertes ou notifications
        return equipment_due
