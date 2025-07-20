# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class StudentMedicalInfo(models.Model):
    """Informations médicales détaillées des élèves"""
    _name = 'student.medical.info'
    _description = 'Informations Médicales Élève'
    _order = 'date desc'
    _rec_name = 'medical_type'

    student_id = fields.Many2one('op.student', string='Élève', required=True, ondelete='cascade')
    student_name = fields.Char(related='student_id.name', string='Nom Élève', store=True)
    
    # Type d'information médicale
    medical_type = fields.Selection([
        ('allergy', '🚨 Allergie'),
        ('chronic', '🏥 Maladie Chronique'),
        ('medication', '💊 Traitement'),
        ('surgery', '🔬 Chirurgie'),
        ('vaccination', '💉 Vaccination'),
        ('injury', '🩹 Blessure'),
        ('checkup', '👩‍⚕️ Visite Médicale'),
        ('emergency', '🚑 Urgence'),
        ('other', '📋 Autre')
    ], string='Type', required=True, default='other')
    
    # Détails
    title = fields.Char('Titre', required=True)
    description = fields.Text('Description Détaillée')
    severity = fields.Selection([
        ('low', '🟢 Faible'),
        ('medium', '🟡 Modéré'),
        ('high', '🟠 Élevé'),
        ('critical', '🔴 Critique')
    ], string='Gravité', default='low')
    
    # Dates
    date = fields.Date('Date', required=True, default=fields.Date.today)
    start_date = fields.Date('Date de Début')
    end_date = fields.Date('Date de Fin')
    next_checkup = fields.Date('Prochain Contrôle')
    
    # Médecin et établissement
    doctor_name = fields.Char('Médecin Traitant')
    doctor_phone = fields.Char('Téléphone Médecin')
    hospital = fields.Char('Hôpital/Clinique')
    
    # Traitement
    treatment = fields.Text('Traitement Prescrit')
    medication_name = fields.Char('Nom du Médicament')
    dosage = fields.Char('Posologie')
    frequency = fields.Char('Fréquence')
    
    # Documents
    medical_report = fields.Binary('Rapport Médical', attachment=True)
    prescription = fields.Binary('Ordonnance', attachment=True)
    xray_scan = fields.Binary('Radiographie/Scanner', attachment=True)
    
    # Statut et alertes
    is_active = fields.Boolean('Actif', default=True)
    is_critical = fields.Boolean('Critique', compute='_compute_is_critical', store=True)
    requires_attention = fields.Boolean('Nécessite Attention', default=False)
    
    # Notifications
    notify_parents = fields.Boolean('Notifier Parents', default=False)
    notify_teachers = fields.Boolean('Notifier Enseignants', default=False)
    notify_nurse = fields.Boolean('Notifier Infirmerie', default=True)
    
    # Suivi
    notes = fields.Text('Notes de Suivi')
    created_by = fields.Many2one('res.users', string='Créé par', default=lambda self: self.env.user)
    
    # Champs calculés
    days_since = fields.Integer('Jours Écoulés', compute='_compute_days_since')
    status_color = fields.Integer('Couleur Statut', compute='_compute_status_color')
    
    @api.depends('severity', 'medical_type')
    def _compute_is_critical(self):
        """Déterminer si l'information est critique"""
        for record in self:
            critical_types = ['allergy', 'chronic', 'emergency']
            critical_severity = ['high', 'critical']
            
            record.is_critical = (
                record.medical_type in critical_types or 
                record.severity in critical_severity
            )
    
    @api.depends('date')
    def _compute_days_since(self):
        """Calculer les jours écoulés depuis la date"""
        for record in self:
            if record.date:
                delta = fields.Date.today() - record.date
                record.days_since = delta.days
            else:
                record.days_since = 0
    
    @api.depends('severity', 'is_active')
    def _compute_status_color(self):
        """Calculer la couleur selon le statut"""
        for record in self:
            if not record.is_active:
                record.status_color = 8  # Gris
            elif record.severity == 'critical':
                record.status_color = 1  # Rouge
            elif record.severity == 'high':
                record.status_color = 3  # Orange
            elif record.severity == 'medium':
                record.status_color = 4  # Jaune
            else:
                record.status_color = 10  # Vert
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Valider les dates"""
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date > record.end_date:
                    raise ValidationError(_("La date de fin doit être après la date de début."))
    
    def action_archive(self):
        """Archiver l'information médicale"""
        self.is_active = False
        return True
    
    def action_mark_critical(self):
        """Marquer comme critique"""
        self.severity = 'critical'
        self.requires_attention = True
        self.notify_parents = True
        self.notify_teachers = True
        return True
    
    def action_send_notifications(self):
        """Envoyer les notifications configurées"""
        for record in self:
            if record.notify_parents:
                # Envoyer aux parents
                record._send_parent_notification()
            
            if record.notify_teachers:
                # Envoyer aux enseignants
                record._send_teacher_notification()
            
            if record.notify_nurse:
                # Envoyer à l'infirmerie
                record._send_nurse_notification()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Notifications envoyées avec succès',
                'type': 'success'
            }
        }
    
    def _send_parent_notification(self):
        """Envoyer notification aux parents"""
        # Logique d'envoi email/SMS aux parents
        pass
    
    def _send_teacher_notification(self):
        """Envoyer notification aux enseignants"""
        # Logique d'envoi aux enseignants de la classe
        pass
    
    def _send_nurse_notification(self):
        """Envoyer notification à l'infirmerie"""
        # Logique d'envoi à l'infirmerie
        pass

class StudentMedicalCategory(models.Model):
    """Catégories d'informations médicales"""
    _name = 'student.medical.category'
    _description = 'Catégorie Médicale'
    
    name = fields.Char('Nom', required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')
    color = fields.Integer('Couleur', default=1)
    active = fields.Boolean('Actif', default=True)
    icon = fields.Char('Icône') 
class StudentVaccination(models.Model):
    """Carnet de vaccination"""
    _name = 'student.vaccination'
    _description = 'Vaccination Élève'
    _rec_name = 'vaccine_name'
    
    student_id = fields.Many2one('op.student', string='Élève', required=True, ondelete='cascade')
    vaccine_name = fields.Char('Nom du Vaccin', required=True)
    vaccine_type = fields.Selection([
        ('bcg', 'BCG'),
        ('dtp', 'DTP (Diphtérie-Tétanos-Poliomyélite)'),
        ('hepatitis_b', 'Hépatite B'),
        ('measles', 'Rougeole'),
        ('yellow_fever', 'Fièvre Jaune'),
        ('meningitis', 'Méningite'),
        ('covid19', 'COVID-19'),
        ('other', 'Autre')
    ], string='Type de Vaccin')
    
    administration_date = fields.Date('Date d\'Administration', required=True)
    expiry_date = fields.Date('Date d\'Expiration')
    batch_number = fields.Char('Numéro de Lot')
    administered_by = fields.Char('Administré par')
    location = fields.Char('Lieu d\'Administration')
    
    dose_number = fields.Integer('Numéro de Dose', default=1)
    is_booster = fields.Boolean('Rappel')
    next_dose_date = fields.Date('Prochaine Dose')
    
    certificate = fields.Binary('Certificat de Vaccination', attachment=True)
    notes = fields.Text('Notes')
    
    is_up_to_date = fields.Boolean('À Jour', compute='_compute_up_to_date')
    
    @api.depends('expiry_date', 'next_dose_date')
    def _compute_up_to_date(self):
        """Vérifier si la vaccination est à jour"""
        for record in self:
            today = fields.Date.today()
            record.is_up_to_date = True
            
            if record.expiry_date and record.expiry_date < today:
                record.is_up_to_date = False
            
            if record.next_dose_date and record.next_dose_date < today:
                record.is_up_to_date = False
