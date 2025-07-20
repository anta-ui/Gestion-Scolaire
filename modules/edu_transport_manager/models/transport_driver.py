# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class TransportDriver(models.Model):
    _name = 'transport.driver'
    _description = 'Chauffeur de Transport'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Nom complet', required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', 'Employé', tracking=True)
    code = fields.Char('Code chauffeur', required=True)
    
    # Informations personnelles
    phone = fields.Char('Téléphone', tracking=True)
    mobile = fields.Char('Mobile', tracking=True)
    email = fields.Char('Email', tracking=True)
    address = fields.Text('Adresse')
    
    # Informations professionnelles
    hire_date = fields.Date('Date d\'embauche', tracking=True)
    experience_years = fields.Integer('Années d\'expérience')
    
    # Permis de conduire
    license_number = fields.Char('Numéro de permis', required=True, tracking=True)
    license_type = fields.Selection([
        ('b', 'Permis B'),
        ('c', 'Permis C'),
        ('d', 'Permis D'),
        ('d1', 'Permis D1'),
        ('de', 'Permis D+E')
    ], string='Type de permis', required=True, tracking=True)
    license_expiry_date = fields.Date('Date d\'expiration du permis', tracking=True)
    
    # Certifications
    professional_card_number = fields.Char('Numéro carte professionnelle')
    professional_card_expiry = fields.Date('Expiration carte professionnelle')
    medical_certificate_date = fields.Date('Date certificat médical')
    medical_certificate_expiry = fields.Date('Expiration certificat médical')
    
    # Statut
    state = fields.Selection([
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('suspended', 'Suspendu'),
        ('training', 'En formation')
    ], default='active', string='Statut', tracking=True)
    
    # Relations
    vehicle_ids = fields.Many2many('transport.vehicle', string='Véhicules autorisés')
    trip_ids = fields.One2many('transport.trip', 'driver_id', 'Trajets')
    
    # Évaluations
    rating = fields.Float('Note moyenne', compute='_compute_rating')
    evaluation_ids = fields.One2many('transport.driver.evaluation', 'driver_id', 'Évaluations')
    
    # Statistiques
    total_trips = fields.Integer('Total trajets', compute='_compute_statistics')
    total_distance = fields.Float('Distance totale (km)', compute='_compute_statistics')
    accident_count = fields.Integer('Nombre d\'accidents', compute='_compute_statistics')
    
    # Alertes
    license_alert = fields.Boolean('Alerte permis', compute='_compute_alerts')
    medical_alert = fields.Boolean('Alerte médical', compute='_compute_alerts')
    
    @api.depends('evaluation_ids.rating')
    def _compute_rating(self):
        for driver in self:
            if driver.evaluation_ids:
                driver.rating = sum(driver.evaluation_ids.mapped('rating')) / len(driver.evaluation_ids)
            else:
                driver.rating = 0.0
    
    @api.depends('trip_ids')
    def _compute_statistics(self):
        for driver in self:
            driver.total_trips = len(driver.trip_ids)
            driver.total_distance = sum(driver.trip_ids.mapped('distance'))
            driver.accident_count = len(driver.trip_ids.filtered('has_incident'))
    
    @api.depends('license_expiry_date', 'medical_certificate_expiry')
    def _compute_alerts(self):
        today = fields.Date.today()
        alert_days = 30  # Alerte 30 jours avant expiration
        
        for driver in self:
            # Alerte permis
            if driver.license_expiry_date:
                driver.license_alert = (driver.license_expiry_date - today).days <= alert_days
            else:
                driver.license_alert = True
                
            # Alerte médical
            if driver.medical_certificate_expiry:
                driver.medical_alert = (driver.medical_certificate_expiry - today).days <= alert_days
            else:
                driver.medical_alert = True
    
    def action_suspend(self):
        self.state = 'suspended'
    
    def action_activate(self):
        self.state = 'active'


class TransportDriverEvaluation(models.Model):
    _name = 'transport.driver.evaluation'
    _description = 'Évaluation Chauffeur'
    _order = 'date desc'

    driver_id = fields.Many2one('transport.driver', 'Chauffeur', required=True, ondelete='cascade')
    date = fields.Date('Date d\'évaluation', default=fields.Date.today)
    evaluator_id = fields.Many2one('res.users', 'Évaluateur', default=lambda self: self.env.user)
    
    # Critères d'évaluation
    punctuality = fields.Integer('Ponctualité', help='Note sur 10')
    safety = fields.Integer('Sécurité', help='Note sur 10')
    communication = fields.Integer('Communication', help='Note sur 10')
    vehicle_care = fields.Integer('Soin du véhicule', help='Note sur 10')
    
    rating = fields.Float('Note globale', compute='_compute_rating', store=True)
    comments = fields.Text('Commentaires')
    
    @api.depends('punctuality', 'safety', 'communication', 'vehicle_care')
    def _compute_rating(self):
        for evaluation in self:
            scores = [evaluation.punctuality, evaluation.safety, 
                     evaluation.communication, evaluation.vehicle_care]
            valid_scores = [s for s in scores if s > 0]
            if valid_scores:
                evaluation.rating = sum(valid_scores) / len(valid_scores)
            else:
                evaluation.rating = 0.0
