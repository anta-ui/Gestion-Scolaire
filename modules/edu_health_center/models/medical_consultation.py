# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class MedicalConsultation(models.Model):
    """Consultation médicale"""
    _name = 'edu.medical.consultation'
    _description = 'Consultation Médicale'
    _order = 'consultation_date desc'

    # Informations de base
    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau')
    )
    
    health_record_id = fields.Many2one(
        'edu.health.record',
        string='Dossier médical',
        required=True
    )
    
    student_id = fields.Many2one(
        related='health_record_id.student_id',
        string='Étudiant',
        readonly=True,
        store=True
    )
    
    # Date et heure
    consultation_date = fields.Datetime(
        string='Date de consultation',
        required=True,
        default=fields.Datetime.now
    )
    
    duration = fields.Float(
        string='Durée (heures)',
        default=0.5
    )
    
    # Type de consultation
    consultation_type = fields.Selection([
        ('routine', 'Visite de routine'),
        ('emergency', 'Urgence'),
        ('follow_up', 'Suivi'),
        ('vaccination', 'Vaccination'),
        ('screening', 'Dépistage'),
        ('sports', 'Certificat médical sport'),
        ('other', 'Autre'),
    ], string='Type de consultation', required=True, default='routine')
    
    # Motif et diagnostic
    chief_complaint = fields.Text(
        string='Motif de consultation',
        required=True
    )
    
    diagnosis = fields.Text(
        string='Diagnostic'
    )
    
    treatment = fields.Text(
        string='Traitement prescrit'
    )
    
    # Signes vitaux
    temperature = fields.Float(
        string='Température (°C)'
    )
    
    blood_pressure_systolic = fields.Integer(
        string='Tension systolique'
    )
    
    blood_pressure_diastolic = fields.Integer(
        string='Tension diastolique'
    )
    
    heart_rate = fields.Integer(
        string='Fréquence cardiaque'
    )
    
    weight = fields.Float(
        string='Poids (kg)'
    )
    
    height = fields.Float(
        string='Taille (cm)'
    )
    
    # Personnel médical
    doctor_id = fields.Many2one(
        'res.users',
        string='Médecin',
        default=lambda self: self.env.user
    )
    
    nurse_id = fields.Many2one(
        'res.users',
        string='Infirmier/ère'
    )
    
    # Suivi
    follow_up_needed = fields.Boolean(
        string='Suivi nécessaire'
    )
    
    follow_up_date = fields.Date(
        string='Date de suivi prévue'
    )
    
    follow_up_notes = fields.Text(
        string='Notes de suivi'
    )
    
    # Documents
    # prescription_ids = fields.One2many(
    #     'medical.prescription',
    #     'consultation_id',
    #     string='Prescriptions'
    # )
    
    medical_certificate = fields.Binary(
        string='Certificat médical'
    )
    
    # État
    state = fields.Selection([
        ('scheduled', 'Programmée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
    ], string='État', default='scheduled')
    
    # Contraintes
    @api.constrains('consultation_date')
    def _check_consultation_date(self):
        for record in self:
            if record.consultation_date and record.consultation_date > fields.Datetime.now():
                # Consultation future - OK
                pass
    
    # Actions
    def action_start_consultation(self):
        """Démarrer la consultation"""
        self.state = 'in_progress'
        return True
    
    def action_complete_consultation(self):
        """Terminer la consultation"""
        self.state = 'completed'
        return True
    
    def action_cancel_consultation(self):
        """Annuler la consultation"""
        self.state = 'cancelled'
        return True
    
    @api.model
    def create(self, vals):
        """Génération automatique du numéro de consultation"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('medical.consultation') or _('Nouveau')
        return super().create(vals)
