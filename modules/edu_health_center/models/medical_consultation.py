# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class MedicalConsultation(models.Model):
    _name = 'edu.medical.consultation'
    _description = 'Consultation Médicale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'consultation_date desc, consultation_time desc'

    # Informations de base
    name = fields.Char(
        string='Référence consultation',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau')
    )
    
    health_record_id = fields.Many2one(
        'edu.health.record',
        string='Dossier médical',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    patient_name = fields.Char(
        string='Nom du patient',
        related='health_record_id.student_id.name',
        readonly=True
    )
    
    # Date et heure
    consultation_date = fields.Date(
        string='Date de consultation',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    consultation_time = fields.Float(
        string='Heure de consultation',
        required=True,
        default=lambda self: datetime.now().hour + datetime.now().minute/60.0,
        help='Heure au format 24h (ex: 14.5 pour 14h30)'
    )
    
    consultation_datetime = fields.Datetime(
        string='Date et heure complète',
        compute='_compute_consultation_datetime',
        store=True
    )
    
    duration = fields.Float(
        string='Durée (minutes)',
        default=30.0,
        help='Durée de la consultation en minutes'
    )
    
    # Personnel médical
    doctor_id = fields.Many2one(
        'medical.staff',
        string='Médecin/Infirmier',
        required=True,
        domain=[('staff_type', 'in', ['doctor', 'nurse'])],
        tracking=True
    )
    
    assistant_id = fields.Many2one(
        'medical.staff',
        string='Assistant',
        domain=[('staff_type', '=', 'assistant')]
    )
    
    # Type et motif de consultation
    consultation_type = fields.Selection([
        ('routine', 'Consultation de routine'),
        ('follow_up', 'Suivi médical'),
        ('emergency', 'Urgence'),
        ('vaccination', 'Vaccination'),
        ('screening', 'Dépistage'),
        ('sports_medical', 'Visite sportive'),
        ('psychological', 'Consultation psychologique'),
        ('dental', 'Consultation dentaire'),
        ('ophthalmology', 'Consultation ophtalmologique'),
        ('other', 'Autre'),
    ], string='Type de consultation', required=True, default='routine', tracking=True)
    
    chief_complaint = fields.Text(
        string='Motif de consultation',
        required=True,
        help='Raison principale de la visite'
    )
    
    # Examen clinique
    symptoms = fields.Text(
        string='Symptômes',
        help='Description des symptômes rapportés'
    )
    
    # Signes vitaux
    temperature = fields.Float(
        string='Température (°C)',
        help='Température corporelle en degrés Celsius'
    )
    
    blood_pressure_systolic = fields.Integer(
        string='Pression artérielle systolique',
        help='Pression systolique en mmHg'
    )
    
    blood_pressure_diastolic = fields.Integer(
        string='Pression artérielle diastolique',
        help='Pression diastolique en mmHg'
    )
    
    heart_rate = fields.Integer(
        string='Fréquence cardiaque',
        help='Battements par minute'
    )
    
    respiratory_rate = fields.Integer(
        string='Fréquence respiratoire',
        help='Respirations par minute'
    )
    
    oxygen_saturation = fields.Float(
        string='Saturation oxygène (%)',
        help='Saturation en oxygène en pourcentage'
    )
    
    # Mesures physiques
    weight = fields.Float(
        string='Poids (kg)',
        help='Poids en kilogrammes'
    )
    
    height = fields.Float(
        string='Taille (cm)',
        help='Taille en centimètres'
    )
    
    bmi = fields.Float(
        string='IMC',
        compute='_compute_bmi',
        store=True,
        help='Indice de Masse Corporelle'
    )
    
    # Examen physique
    physical_examination = fields.Html(
        string='Examen physique',
        help='Résultats de l\'examen physique'
    )
    
    head_neck_exam = fields.Text(
        string='Tête et cou'
    )
    
    cardiovascular_exam = fields.Text(
        string='Système cardiovasculaire'
    )
    
    respiratory_exam = fields.Text(
        string='Système respiratoire'
    )
    
    abdominal_exam = fields.Text(
        string='Examen abdominal'
    )
    
    neurological_exam = fields.Text(
        string='Examen neurologique'
    )
    
    skin_exam = fields.Text(
        string='Examen cutané'
    )
    
    # Diagnostic et plan de traitement
    diagnosis = fields.Html(
        string='Diagnostic',
        required=True,
        help='Diagnostic médical'
    )
    
    differential_diagnosis = fields.Text(
        string='Diagnostic différentiel',
        help='Autres diagnostics possibles'
    )
    
    treatment_plan = fields.Html(
        string='Plan de traitement',
        help='Plan thérapeutique proposé'
    )
    
    recommendations = fields.Text(
        string='Recommandations',
        help='Conseils et recommandations au patient'
    )
    
    # Prescriptions et examens
    # prescription_ids = fields.One2many(
    #     'medication.prescription',
    #     'consultation_id',
    #     string='Prescriptions'
    # )
    
    # lab_test_ids = fields.One2many(
    #     'edu.lab.test.order',
    #     'consultation_id',
    #     string='Examens de laboratoire'
    # )
    
    # imaging_order_ids = fields.One2many(
    #     'edu.imaging.order',
    #     'consultation_id',
    #     string='Examens d\'imagerie'
    # )
    
    # Suivi et rendez-vous
    follow_up_required = fields.Boolean(
        string='Suivi requis',
        default=False
    )
    
    follow_up_date = fields.Date(
        string='Date de suivi'
    )
    
    follow_up_notes = fields.Text(
        string='Notes de suivi'
    )
    
    # next_appointment_id = fields.Many2one(
    #     'edu.medical.appointment',
    #     string='Prochain rendez-vous'
    # )
    
    # Certificats et documents
    medical_certificate_required = fields.Boolean(
        string='Certificat médical requis',
        default=False
    )
    
    certificate_type = fields.Selection([
        ('fitness', 'Aptitude physique'),
        ('absence', 'Justificatif d\'absence'),
        ('sports', 'Certificat sportif'),
        ('swimming', 'Certificat piscine'),
        ('travel', 'Certificat voyage'),
        ('other', 'Autre'),
    ], string='Type de certificat')
    
    certificate_duration_days = fields.Integer(
        string='Durée certificat (jours)',
        default=0
    )
    
    # Documents joints
    consultation_documents = fields.Many2many(
        'ir.attachment',
        'consultation_document_rel',
        'consultation_id',
        'attachment_id',
        string='Documents'
    )
    
    # État et statut
    state = fields.Selection([
        ('scheduled', 'Programmée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
        ('no_show', 'Absence'),
    ], string='État', default='scheduled', required=True, tracking=True)
    
    urgency_level = fields.Selection([
        ('low', 'Faible'),
        ('normal', 'Normal'),
        ('high', 'Élevé'),
        ('critical', 'Critique'),
    ], string='Niveau d\'urgence', default='normal', tracking=True)
    
    # Facturation
    billable = fields.Boolean(
        string='Facturable',
        default=False
    )
    
    consultation_fee = fields.Float(
        string='Honoraires de consultation'
    )
    
    insurance_covered = fields.Boolean(
        string='Pris en charge assurance',
        default=True
    )
    
    # Télémédecine
    is_telemedicine = fields.Boolean(
        string='Téléconsultation',
        default=False
    )
    
    telemedicine_platform = fields.Selection([
        ('zoom', 'Zoom'),
        ('teams', 'Microsoft Teams'),
        ('meet', 'Google Meet'),
        ('jitsi', 'Jitsi Meet'),
        ('other', 'Autre'),
    ], string='Plateforme télémédecine')
    
    telemedicine_link = fields.Char(
        string='Lien téléconsultation'
    )
    
    # Consentement et signatures
    patient_consent = fields.Boolean(
        string='Consentement patient',
        default=False,
        help='Le patient a-t-il donné son consentement?'
    )
    
    parent_consent = fields.Boolean(
        string='Consentement parental',
        default=False,
        help='Consentement des parents requis pour les mineurs'
    )
    
    doctor_signature = fields.Binary(
        string='Signature médecin',
        attachment=True
    )
    
    patient_signature = fields.Binary(
        string='Signature patient/parent',
        attachment=True
    )
    
    # Notes et observations
    private_notes = fields.Text(
        string='Notes privées',
        help='Notes confidentielles du médecin'
    )
    
    public_notes = fields.Text(
        string='Notes publiques',
        help='Notes visibles par l\'équipe soignante'
    )
    
    # Métadonnées
    created_by_id = fields.Many2one(
        'res.users',
        string='Créé par',
        default=lambda self: self.env.user,
        readonly=True
    )
    
    active = fields.Boolean(default=True)
    
    @api.depends('consultation_date', 'consultation_time')
    def _compute_consultation_datetime(self):
        """Calculer la date et heure complète"""
        for consultation in self:
            if consultation.consultation_date and consultation.consultation_time:
                # Convertir l'heure flottante en heures et minutes
                hours = int(consultation.consultation_time)
                minutes = int((consultation.consultation_time - hours) * 60)
                
                consultation.consultation_datetime = datetime.combine(
                    consultation.consultation_date,
                    datetime.min.time().replace(hour=hours, minute=minutes)
                )
            else:
                consultation.consultation_datetime = False
    
    @api.depends('weight', 'height')
    def _compute_bmi(self):
        """Calculer l'IMC"""
        for consultation in self:
            if consultation.height and consultation.weight and consultation.height > 0:
                height_m = consultation.height / 100  # Conversion cm -> m
                consultation.bmi = round(consultation.weight / (height_m ** 2), 2)
            else:
                consultation.bmi = 0.0
    
    @api.model
    def create(self, vals):
        """Créer une consultation avec numéro automatique"""
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'edu.medical.consultation'
            ) or _('Nouveau')
        
        return super().create(vals)
    
    @api.constrains('consultation_time')
    def _check_consultation_time(self):
        """Valider l'heure de consultation"""
        for consultation in self:
            if consultation.consultation_time < 0 or consultation.consultation_time >= 24:
                raise ValidationError(_('L\'heure de consultation doit être entre 0 et 24.'))
    
    @api.constrains('temperature')
    def _check_temperature(self):
        """Valider la température"""
        for consultation in self:
            if consultation.temperature and (consultation.temperature < 30 or consultation.temperature > 45):
                raise ValidationError(_('La température doit être entre 30°C et 45°C.'))
    
    @api.constrains('blood_pressure_systolic', 'blood_pressure_diastolic')
    def _check_blood_pressure(self):
        """Valider la pression artérielle"""
        for consultation in self:
            if consultation.blood_pressure_systolic and consultation.blood_pressure_diastolic:
                if consultation.blood_pressure_systolic <= consultation.blood_pressure_diastolic:
                    raise ValidationError(_('La pression systolique doit être supérieure à la pression diastolique.'))
    
    def action_start_consultation(self):
        """Commencer la consultation"""
        self.ensure_one()
        
        if self.state != 'scheduled':
            raise UserError(_('Seules les consultations programmées peuvent être démarrées.'))
        
        self.write({
            'state': 'in_progress',
            'consultation_datetime': fields.Datetime.now(),
        })
        
        # Mettre à jour le dossier médical avec les nouvelles mesures
        if self.weight or self.height:
            update_vals = {}
            if self.weight:
                update_vals['weight'] = self.weight
            if self.height:
                update_vals['height'] = self.height
            
            if update_vals:
                self.health_record_id.write(update_vals)
        
        self.message_post(
            body=_('Consultation démarrée par %s') % self.env.user.name
        )
    
    def action_complete_consultation(self):
        """Terminer la consultation"""
        self.ensure_one()
        
        if self.state != 'in_progress':
            raise UserError(_('Seules les consultations en cours peuvent être terminées.'))
        
        # Vérifier que les champs obligatoires sont remplis
        if not self.diagnosis:
            raise UserError(_('Le diagnostic doit être renseigné avant de terminer la consultation.'))
        
        self.write({'state': 'completed'})
        
        # Créer automatiquement le rendez-vous de suivi si requis
        if self.follow_up_required and self.follow_up_date:
            self._create_follow_up_appointment()
        
        # Générer le certificat médical si requis
        if self.medical_certificate_required:
            self._generate_medical_certificate()
        
        # Envoyer les notifications
        self._send_consultation_notifications()
        
        self.message_post(
            body=_('Consultation terminée par %s') % self.env.user.name
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Consultation terminée'),
                'message': _('La consultation a été terminée avec succès.'),
                'type': 'success',
            }
        }
    
    def action_cancel_consultation(self):
        """Annuler la consultation"""
        self.ensure_one()
        
        if self.state == 'completed':
            raise UserError(_('Une consultation terminée ne peut pas être annulée.'))
        
        self.write({'state': 'cancelled'})
        
        self.message_post(
            body=_('Consultation annulée par %s') % self.env.user.name
        )
    
    def action_mark_no_show(self):
        """Marquer comme absence"""
        self.ensure_one()
        
        if self.state != 'scheduled':
            raise UserError(_('Seules les consultations programmées peuvent être marquées comme absence.'))
        
        self.write({'state': 'no_show'})
        
        # Créer une activité de suivi
        self.activity_schedule(
            'mail.mail_activity_data_call',
            summary=_('Absence à la consultation'),
            note=_('Le patient ne s\'est pas présenté à sa consultation du %s') % self.consultation_date,
            user_id=self.doctor_id.user_id.id if self.doctor_id.user_id else self.env.user.id,
        )
        
        self.message_post(
            body=_('Patient absent à la consultation')
        )
    
    def action_reschedule(self):
        """Reprogrammer la consultation"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reprogrammer la consultation'),
            'res_model': 'edu.consultation.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_consultation_id': self.id,
                'default_new_date': self.consultation_date,
                'default_new_time': self.consultation_time,
            },
        }
    
    def action_add_prescription(self):
        """Ajouter une prescription"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nouvelle prescription'),
            'res_model': 'edu.medication.prescription',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_consultation_id': self.id,
                'default_health_record_id': self.health_record_id.id,
                'default_prescribed_by_id': self.doctor_id.id,
            },
        }
    
    def action_order_lab_test(self):
        """Commander des examens de laboratoire"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commander des examens'),
            'res_model': 'edu.lab.test.order.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_consultation_id': self.id,
                'default_health_record_id': self.health_record_id.id,
            },
        }
    
    def action_generate_certificate(self):
        """Générer un certificat médical"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Générer certificat médical'),
            'res_model': 'edu.medical.certificate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_consultation_id': self.id,
                'default_health_record_id': self.health_record_id.id,
                'default_certificate_type': self.certificate_type,
                'default_duration_days': self.certificate_duration_days,
            },
        }
    
    def _create_follow_up_appointment(self):
        """Créer un rendez-vous de suivi"""
        if not self.follow_up_date:
            return
        
        appointment_vals = {
            'name': _('Suivi - %s') % self.name,
            'health_record_id': self.health_record_id.id,
            'doctor_id': self.doctor_id.id,
            'appointment_date': self.follow_up_date,
            'appointment_time': self.consultation_time,  # Même heure que la consultation originale
            'consultation_type': 'follow_up',
            'notes': self.follow_up_notes,
            'parent_consultation_id': self.id,
        }
        
        appointment = self.env['edu.medical.appointment'].create(appointment_vals)
        
        self.write({'next_appointment_id': appointment.id})
        
        return appointment
    
    def _generate_medical_certificate(self):
        """Générer automatiquement un certificat médical"""
        if not self.medical_certificate_required:
            return
        
        certificate_vals = {
            'consultation_id': self.id,
            'health_record_id': self.health_record_id.id,
            'certificate_type': self.certificate_type or 'fitness',
            'issued_date': fields.Date.today(),
            'valid_from': fields.Date.today(),
            'valid_until': fields.Date.today() + timedelta(days=self.certificate_duration_days or 30),
            'diagnosis': self.diagnosis,
            'recommendations': self.recommendations,
            'issued_by_id': self.doctor_id.id,
        }
        
        certificate = self.env['edu.medical.certificate'].create(certificate_vals)
        
        return certificate
    
    def _send_consultation_notifications(self):
        """Envoyer les notifications de fin de consultation"""
        # Notifier les parents pour les mineurs
        if self.health_record_id.age < 18:
            # TODO: Envoyer notification aux parents
            pass
        
        # Notifier l'équipe soignante si urgence
        if self.urgency_level in ['high', 'critical']:
            # TODO: Envoyer alerte à l'équipe
            pass
        
        # Programmer des rappels si traitement prolongé
        if self.prescription_ids.filtered(lambda p: p.duration_days > 7):
            # TODO: Programmer rappels de traitement
            pass
    
    def get_vital_signs_summary(self):
        """Obtenir un résumé des signes vitaux"""
        self.ensure_one()
        
        vital_signs = {}
        
        if self.temperature:
            vital_signs['temperature'] = {
                'value': self.temperature,
                'unit': '°C',
                'normal_range': '36.5-37.5',
                'status': 'normal' if 36.5 <= self.temperature <= 37.5 else 'abnormal'
            }
        
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            vital_signs['blood_pressure'] = {
                'value': f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}",
                'unit': 'mmHg',
                'normal_range': '<120/80',
                'status': 'normal' if self.blood_pressure_systolic < 120 and self.blood_pressure_diastolic < 80 else 'abnormal'
            }
        
        if self.heart_rate:
            vital_signs['heart_rate'] = {
                'value': self.heart_rate,
                'unit': 'bpm',
                'normal_range': '60-100',
                'status': 'normal' if 60 <= self.heart_rate <= 100 else 'abnormal'
            }
        
        if self.respiratory_rate:
            vital_signs['respiratory_rate'] = {
                'value': self.respiratory_rate,
                'unit': '/min',
                'normal_range': '12-20',
                'status': 'normal' if 12 <= self.respiratory_rate <= 20 else 'abnormal'
            }
        
        if self.oxygen_saturation:
            vital_signs['oxygen_saturation'] = {
                'value': self.oxygen_saturation,
                'unit': '%',
                'normal_range': '>95',
                'status': 'normal' if self.oxygen_saturation > 95 else 'abnormal'
            }
        
        return vital_signs
    
    def check_vital_signs_alerts(self):
        """Vérifier les alertes sur les signes vitaux"""
        self.ensure_one()
        
        alerts = []
        
        # Température
        if self.temperature:
            if self.temperature >= 38.5:
                alerts.append({
                    'type': 'fever',
                    'message': _('Fièvre élevée'),
                    'value': f"{self.temperature}°C",
                    'severity': 'high'
                })
            elif self.temperature <= 36.0:
                alerts.append({
                    'type': 'hypothermia',
                    'message': _('Hypothermie'),
                    'value': f"{self.temperature}°C",
                    'severity': 'medium'
                })
        
        # Pression artérielle
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            if self.blood_pressure_systolic >= 140 or self.blood_pressure_diastolic >= 90:
                alerts.append({
                    'type': 'hypertension',
                    'message': _('Hypertension'),
                    'value': f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic} mmHg",
                    'severity': 'medium'
                })
            elif self.blood_pressure_systolic < 90 or self.blood_pressure_diastolic < 60:
                alerts.append({
                    'type': 'hypotension',
                    'message': _('Hypotension'),
                    'value': f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic} mmHg",
                    'severity': 'medium'
                })
        
        # Fréquence cardiaque
        if self.heart_rate:
            if self.heart_rate > 100:
                alerts.append({
                    'type': 'tachycardia',
                    'message': _('Tachycardie'),
                    'value': f"{self.heart_rate} bpm",
                    'severity': 'medium'
                })
            elif self.heart_rate < 60:
                alerts.append({
                    'type': 'bradycardia',
                    'message': _('Bradycardie'),
                    'value': f"{self.heart_rate} bpm",
                    'severity': 'medium'
                })
        
        # Saturation en oxygène
        if self.oxygen_saturation and self.oxygen_saturation < 95:
            severity = 'critical' if self.oxygen_saturation < 90 else 'high'
            alerts.append({
                'type': 'hypoxia',
                'message': _('Hypoxie'),
                'value': f"{self.oxygen_saturation}%",
                'severity': severity
            })
        
        return alerts
    
    @api.model
    def get_consultation_statistics(self, date_from=None, date_to=None):
        """Obtenir les statistiques des consultations"""
        domain = []
        
        if date_from:
            domain.append(('consultation_date', '>=', date_from))
        if date_to:
            domain.append(('consultation_date', '<=', date_to))
        
        consultations = self.search(domain)
        
        # Statistiques générales
        total_consultations = len(consultations)
        completed_consultations = len(consultations.filtered(lambda c: c.state == 'completed'))
        cancelled_consultations = len(consultations.filtered(lambda c: c.state == 'cancelled'))
        no_show_consultations = len(consultations.filtered(lambda c: c.state == 'no_show'))
        
        # Répartition par type
        type_stats = {}
        for consultation in consultations:
            cons_type = consultation.consultation_type
            type_stats[cons_type] = type_stats.get(cons_type, 0) + 1
        
        # Répartition par médecin
        doctor_stats = {}
        for consultation in consultations:
            doctor_name = consultation.doctor_id.name
            doctor_stats[doctor_name] = doctor_stats.get(doctor_name, 0) + 1
        
        # Consultations par jour de la semaine
        weekday_stats = {}
        for consultation in consultations:
            weekday = consultation.consultation_date.strftime('%A')
            weekday_stats[weekday] = weekday_stats.get(weekday, 0) + 1
        
        # Durée moyenne des consultations
        completed_with_duration = consultations.filtered(lambda c: c.state == 'completed' and c.duration > 0)
        avg_duration = sum(completed_with_duration.mapped('duration')) / len(completed_with_duration) if completed_with_duration else 0
        
        return {
            'total_consultations': total_consultations,
            'completion_rate': (completed_consultations / total_consultations * 100) if total_consultations > 0 else 0,
            'cancellation_rate': (cancelled_consultations / total_consultations * 100) if total_consultations > 0 else 0,
            'no_show_rate': (no_show_consultations / total_consultations * 100) if total_consultations > 0 else 0,
            'type_distribution': type_stats,
            'doctor_distribution': doctor_stats,
            'weekday_distribution': weekday_stats,
            'average_duration': avg_duration,
        }
    
    @api.model
    def create_emergency_consultation(self, health_record_id, emergency_data):
        """Créer une consultation d'urgence"""
        consultation_vals = {
            'health_record_id': health_record_id,
            'consultation_type': 'emergency',
            'urgency_level': emergency_data.get('urgency_level', 'critical'),
            'chief_complaint': emergency_data.get('complaint', 'Urgence médicale'),
            'symptoms': emergency_data.get('symptoms', ''),
            'consultation_date': fields.Date.today(),
            'consultation_time': datetime.now().hour + datetime.now().minute/60.0,
            'state': 'in_progress',
        }
        
        # Assigner automatiquement un médecin de garde
        on_duty_doctor = self.env['edu.medical.staff'].search([
            ('staff_type', 'in', ['doctor', 'nurse']),
            ('is_on_duty', '=', True),
        ], limit=1)
        
        if on_duty_doctor:
            consultation_vals['doctor_id'] = on_duty_doctor.id
        
        consultation = self.create(consultation_vals)
        
        # Créer l'urgence associée
        emergency_vals = {
            'health_record_id': health_record_id,
            'consultation_id': consultation.id,
            'emergency_type': emergency_data.get('emergency_type', 'medical'),
            'severity_level': emergency_data.get('urgency_level', 'critical'),
            'description': emergency_data.get('complaint', ''),
            'location': emergency_data.get('location', ''),
            'reported_by': emergency_data.get('reported_by', ''),
        }
        
        emergency = self.env['edu.health.emergency'].create(emergency_vals)
        
        return consultation, emergency
