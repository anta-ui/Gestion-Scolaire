# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging

_logger = logging.getLogger(__name__)


class TransportMaintenance(models.Model):
    _name = 'transport.maintenance'
    _description = 'Maintenance Véhicule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char('Référence', required=True, default=lambda self: _('Nouveau'))
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', required=True, tracking=True)
    
    # Type de maintenance
    maintenance_type = fields.Selection([
        ('preventive', 'Préventive'),
        ('corrective', 'Corrective'),
        ('emergency', 'Urgence'),
        ('inspection', 'Contrôle technique')
    ], string='Type', required=True, default='preventive', tracking=True)
    
    # Planification
    date = fields.Date('Date prévue', required=True, default=fields.Date.today, tracking=True)
    duration = fields.Float('Durée estimée (heures)', default=2.0)
    
    # Exécution
    actual_date = fields.Date('Date réelle', tracking=True)
    actual_duration = fields.Float('Durée réelle (heures)')
    
    # Statut
    state = fields.Selection([
        ('planned', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée')
    ], default='planned', string='Statut', tracking=True)
    
    # Détails techniques
    description = fields.Text('Description des travaux', required=True)
    work_performed = fields.Text('Travaux effectués')
    
    # Personnel
    technician_id = fields.Many2one('hr.employee', 'Technicien responsable')
    garage_id = fields.Many2one('res.partner', 'Garage/Atelier')
    
    # Coûts
    labor_cost = fields.Float('Coût main d\'œuvre')
    parts_cost = fields.Float('Coût pièces', compute='_compute_parts_cost', store=True)
    total_cost = fields.Float('Coût total', compute='_compute_total_cost', store=True)
    
    # Pièces détachées
    part_ids = fields.One2many('transport.maintenance.part', 'maintenance_id', 'Pièces utilisées')
    
    # Kilométrage
    odometer_reading = fields.Float('Relevé kilométrique')
    next_maintenance_km = fields.Float('Prochaine maintenance (km)')
    
    # Documents
    invoice_ids = fields.Many2many('account.move', string='Factures')
    attachment_ids = fields.Many2many('ir.attachment', string='Documents joints')
    
    # Prochaine maintenance
    next_maintenance_date = fields.Date('Prochaine maintenance')
    next_maintenance_type = fields.Selection([
        ('preventive', 'Préventive'),
        ('inspection', 'Contrôle technique')
    ], string='Type prochaine maintenance')
    
    @api.depends('part_ids.total_cost')
    def _compute_parts_cost(self):
        for maintenance in self:
            maintenance.parts_cost = sum(maintenance.part_ids.mapped('total_cost'))
    
    @api.depends('labor_cost', 'parts_cost')
    def _compute_total_cost(self):
        for maintenance in self:
            maintenance.total_cost = maintenance.labor_cost + maintenance.parts_cost
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('transport.maintenance') or _('Nouveau')
        return super(TransportMaintenance, self).create(vals)
    
    def action_start(self):
        self.write({
            'state': 'in_progress',
            'actual_date': fields.Date.today()
        })
    
    def action_complete(self):
        self.write({
            'state': 'completed',
            'actual_date': fields.Date.today()
        })
        # Planifier la prochaine maintenance si nécessaire
        self._schedule_next_maintenance()
    
    def action_cancel(self):
        self.state = 'cancelled'
    
    def _schedule_next_maintenance(self):
        """Planifier automatiquement la prochaine maintenance"""
        if self.next_maintenance_date and self.next_maintenance_type:
            self.env['transport.maintenance'].create({
                'vehicle_id': self.vehicle_id.id,
                'maintenance_type': self.next_maintenance_type,
                'date': self.next_maintenance_date,
                'description': f'Maintenance programmée suite à {self.name}'
            })


class TransportMaintenancePart(models.Model):
    _name = 'transport.maintenance.part'
    _description = 'Pièce de Maintenance'

    maintenance_id = fields.Many2one('transport.maintenance', 'Maintenance', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Pièce', required=True)
    
    # Quantités
    quantity = fields.Float('Quantité', default=1.0, required=True)
    unit_price = fields.Float('Prix unitaire', required=True)
    total_cost = fields.Float('Coût total', compute='_compute_total_cost', store=True)
    
    # Informations
    part_number = fields.Char('Référence pièce')
    supplier_id = fields.Many2one('res.partner', 'Fournisseur')
    
    # Statut
    installed = fields.Boolean('Installée', default=False)
    installation_date = fields.Date('Date d\'installation')
    
    @api.depends('quantity', 'unit_price')
    def _compute_total_cost(self):
        for part in self:
            part.total_cost = part.quantity * part.unit_price


class TransportMaintenanceSchedule(models.Model):
    _name = 'transport.maintenance.schedule'
    _description = 'Planning de Maintenance'

    name = fields.Char('Nom du planning', required=True)
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', required=True)
    
    # Fréquence
    frequency_type = fields.Selection([
        ('km', 'Kilométrage'),
        ('time', 'Temps'),
        ('both', 'Les deux')
    ], string='Type de fréquence', required=True, default='time')
    
    frequency_km = fields.Integer('Fréquence (km)')
    frequency_months = fields.Integer('Fréquence (mois)')
    
    # Type de maintenance
    maintenance_type = fields.Selection([
        ('oil_change', 'Vidange'),
        ('brake_check', 'Contrôle freins'),
        ('tire_check', 'Contrôle pneus'),
        ('engine_check', 'Contrôle moteur'),
        ('full_inspection', 'Contrôle complet')
    ], string='Type de maintenance', required=True)
    
    # Statut
    active = fields.Boolean('Actif', default=True)
    
    # Dernière maintenance
    last_maintenance_date = fields.Date('Dernière maintenance')
    last_maintenance_km = fields.Float('Dernier kilométrage')
    
    # Prochaine maintenance
    next_maintenance_date = fields.Date('Prochaine maintenance', compute='_compute_next_maintenance')
    next_maintenance_km = fields.Float('Prochain kilométrage', compute='_compute_next_maintenance')
    
    @api.depends('last_maintenance_date', 'last_maintenance_km', 'frequency_months', 'frequency_km')
    def _compute_next_maintenance(self):
        for schedule in self:
            if schedule.frequency_type in ('time', 'both') and schedule.last_maintenance_date:
                schedule.next_maintenance_date = schedule.last_maintenance_date + timedelta(days=schedule.frequency_months * 30)
            
            if schedule.frequency_type in ('km', 'both') and schedule.last_maintenance_km:
                schedule.next_maintenance_km = schedule.last_maintenance_km + schedule.frequency_km
    
    def generate_maintenance_order(self):
        """Générer un ordre de maintenance"""
        maintenance_vals = {
            'vehicle_id': self.vehicle_id.id,
            'maintenance_type': 'preventive',
            'date': self.next_maintenance_date or fields.Date.today(),
            'description': f'Maintenance programmée: {self.name}',
            'odometer_reading': self.next_maintenance_km or 0,
        }
        maintenance = self.env['transport.maintenance'].create(maintenance_vals)
        return maintenance


class TransportVehicleDocument(models.Model):
    _name = 'transport.vehicle.document'
    _description = 'Document Véhicule'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nom du document', required=True)
    vehicle_id = fields.Many2one('transport.vehicle', 'Véhicule', required=True, tracking=True)
    
    # Type de document
    document_type = fields.Selection([
        ('registration', 'Carte grise'),
        ('insurance', 'Assurance'),
        ('inspection', 'Contrôle technique'),
        ('license', 'Permis de transport'),
        ('other', 'Autre')
    ], string='Type de document', required=True, tracking=True)
    
    # Dates
    issue_date = fields.Date('Date d\'émission', tracking=True)
    expiry_date = fields.Date('Date d\'expiration', tracking=True)
    
    # Détails
    document_number = fields.Char('Numéro de document')
    issuing_authority = fields.Char('Autorité émettrice')
    
    # Statut
    state = fields.Selection([
        ('valid', 'Valide'),
        ('expired', 'Expiré'),
        ('expiring_soon', 'Expire bientôt')
    ], string='Statut', compute='_compute_state', store=True)
    
    # Fichier
    attachment_id = fields.Many2one('ir.attachment', 'Fichier joint')
    
    # Alertes
    alert_days = fields.Integer('Alerte (jours avant expiration)', default=30)
    
    @api.depends('expiry_date')
    def _compute_state(self):
        today = fields.Date.today()
        for document in self:
            if not document.expiry_date:
                document.state = 'valid'
            elif document.expiry_date < today:
                document.state = 'expired'
            elif (document.expiry_date - today).days <= document.alert_days:
                document.state = 'expiring_soon'
            else:
                document.state = 'valid'
