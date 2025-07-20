# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class MedicalStaff(models.Model):
    """Gestion du personnel médical"""
    _name = 'medical.staff'
    _description = 'Personnel Médical'
    _order = 'name'

    # Informations personnelles
    name = fields.Char(
        string='Nom complet',
        required=True
    )

    first_name = fields.Char(
        string='Prénom'
    )

    last_name = fields.Char(
        string='Nom de famille'
    )

    # Type de personnel
    staff_type = fields.Selection([
        ('doctor', 'Médecin'),
        ('nurse', 'Infirmier/ère'),
        ('assistant', 'Assistant médical'),
        ('specialist', 'Spécialiste'),
        ('administrator', 'Administrateur'),
    ], string='Type de personnel', required=True, default='nurse')

    # Informations professionnelles
    employee_number = fields.Char(
        string='Numéro d\'employé',
        required=True
    )

    license_number = fields.Char(
        string='Numéro de licence'
    )

    specialization = fields.Char(
        string='Spécialisation'
    )

    qualification = fields.Text(
        string='Qualifications'
    )

    # Contact
    email = fields.Char(
        string='Email'
    )

    phone = fields.Char(
        string='Téléphone'
    )

    mobile = fields.Char(
        string='Mobile'
    )

    # Statut
    active = fields.Boolean(
        string='Actif',
        default=True
    )

    state = fields.Selection([
        ('active', 'Actif'),
        ('on_leave', 'En congé'),
        ('suspended', 'Suspendu'),
        ('terminated', 'Licencié'),
    ], string='État', default='active')

    # Dates
    hire_date = fields.Date(
        string='Date d\'embauche'
    )

    # Services d'urgence
    is_on_duty = fields.Boolean(
        string='De garde',
        default=False
    )

    duty_start_time = fields.Float(
        string='Heure début garde'
    )

    duty_end_time = fields.Float(
        string='Heure fin garde'
    )

    # Utilisateur Odoo associé
    user_id = fields.Many2one(
        'res.users',
        string='Utilisateur système'
    )

    # Adresse
    street = fields.Char(string='Rue')
    street2 = fields.Char(string='Rue 2')
    city = fields.Char(string='Ville')
    zip = fields.Char(string='Code postal')
    state_id = fields.Many2one('res.country.state', string='État')
    country_id = fields.Many2one('res.country', string='Pays')
    
    # Horaires de travail
    work_schedule = fields.Selection([
        ('full_time', 'Temps plein'),
        ('part_time', 'Temps partiel'),
        ('on_call', 'Sur appel'),
        ('contract', 'Contractuel')
    ], string='Horaire de travail', default='full_time')
    
    # Relations
    schedule_ids = fields.One2many(
        'medical.staff.schedule',
        'staff_id',
        string='Planning'
    )
    
    training_ids = fields.One2many(
        'medical.staff.training',
        'staff_id',
        string='Formations'
    )
    
    # Statistiques
    consultation_count = fields.Integer(
        string='Nombre de consultations',
        compute='_compute_consultation_stats'
    )
    
    # Métadonnées
    # company_id = fields.Many2one(
    #     'res.company',
    #     string='Société',
    #     required=True,
    #     default=lambda self: self.env.company
    # )
    
    @api.depends('first_name', 'last_name')
    def _compute_name(self):
        """Calculer le nom complet"""
        for staff in self:
            if staff.first_name and staff.last_name:
                staff.name = f"{staff.first_name} {staff.last_name}"
            elif staff.first_name:
                staff.name = staff.first_name
            elif staff.last_name:
                staff.name = staff.last_name
    
    def _compute_consultation_stats(self):
        """Calculer les statistiques de consultation"""
        for staff in self:
            consultations = self.env['edu.medical.consultation'].search([
                ('doctor_id', '=', staff.id)
            ])
            staff.consultation_count = len(consultations)
    
    def action_set_on_duty(self):
        """Mettre de garde"""
        self.is_on_duty = True
    
    def action_set_off_duty(self):
        """Retirer de garde"""
        self.is_on_duty = False


class MedicalStaffSchedule(models.Model):
    """Planning du personnel médical"""
    _name = 'medical.staff.schedule'
    _description = 'Planning Personnel Médical'
    _order = 'date, start_time'

    name = fields.Char(
        string='Référence',
        compute='_compute_name',
        store=True
    )
    
    staff_id = fields.Many2one(
        'medical.staff',
        string='Personnel',
        required=True
    )
    
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today
    )
    
    start_time = fields.Float(
        string='Heure de début',
        required=True,
        help='Heure au format 24h'
    )
    
    end_time = fields.Float(
        string='Heure de fin',
        required=True,
        help='Heure au format 24h'
    )
    
    shift_type = fields.Selection([
        ('morning', 'Matin'),
        ('afternoon', 'Après-midi'),
        ('evening', 'Soir'),
        ('night', 'Nuit'),
        ('day', 'Jour'),
        ('emergency', 'Urgence'),
        ('on_call', 'Astreinte')
    ], string='Type de service', required=True)
    
    location = fields.Char(
        string='Lieu',
        help="Lieu d'affectation"
    )
    
    notes = fields.Text(string='Notes')
    
    # État
    state = fields.Selection([
        ('scheduled', 'Programmé'),
        ('confirmed', 'Confirmé'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé')
    ], string='État', default='scheduled')
    
    @api.depends('staff_id.name', 'date', 'shift_type')
    def _compute_name(self):
        """Calculer le nom du planning"""
        for schedule in self:
            if schedule.staff_id and schedule.date:
                schedule.name = f"{schedule.staff_id.name} - {schedule.date} - {schedule.shift_type}"
            else:
                schedule.name = 'Nouveau planning'


class MedicalStaffTraining(models.Model):
    """Formations du personnel médical"""
    _name = 'medical.staff.training'
    _description = 'Formation Personnel Médical'
    _order = 'training_date desc'

    name = fields.Char(
        string='Nom de la formation',
        required=True
    )
    
    staff_id = fields.Many2one(
        'medical.staff',
        string='Personnel',
        required=True
    )
    
    training_type = fields.Selection([
        ('certification', 'Certification'),
        ('continuing_education', 'Formation continue'),
        ('safety', 'Sécurité'),
        ('emergency', 'Urgences'),
        ('equipment', 'Équipement'),
        ('other', 'Autre')
    ], string='Type de formation', required=True)
    
    training_date = fields.Date(
        string='Date de formation',
        required=True
    )
    
    expiry_date = fields.Date(
        string='Date d\'expiration',
        help="Date d'expiration de la certification"
    )
    
    provider = fields.Char(
        string='Organisme formateur',
        help="Organisme qui a dispensé la formation"
    )
    
    trainer = fields.Char(
        string='Formateur',
        help="Nom du formateur ou organisme"
    )
    
    certificate_number = fields.Char(
        string='Numéro de certificat'
    )
    
    certificate_issued = fields.Boolean(
        string='Certificat délivré',
        default=False,
        help="Indique si le certificat a été délivré"
    )
    
    duration_hours = fields.Float(
        string='Durée (heures)',
        help="Durée de la formation en heures"
    )
    
    description = fields.Text(
        string='Description',
        help="Description de la formation"
    )
    
    evaluation_score = fields.Float(
        string='Note d\'évaluation',
        help="Note obtenue lors de l'évaluation (/20)"
    )
    
    evaluation_notes = fields.Html(
        string='Notes d\'évaluation',
        help="Commentaires sur l'évaluation"
    )
    
    # État
    state = fields.Selection([
        ('planned', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('expired', 'Expirée'),
        ('cancelled', 'Annulée')
    ], string='État', default='planned')
    
    status = fields.Selection([
        ('planned', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('expired', 'Expirée'),
        ('cancelled', 'Annulée')
    ], string='Statut', default='planned')
    
    # Documents
    certificates = fields.Many2many(
        'ir.attachment',
        'training_certificate_rel',
        'training_id',
        'attachment_id',
        string='Certificats'
    )
    
    def action_complete(self):
        """Marquer la formation comme terminée"""
        self.state = 'completed'
    
    def action_cancel(self):
        """Annuler la formation"""
        self.state = 'cancelled'
