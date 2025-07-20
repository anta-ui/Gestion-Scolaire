# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import datetime, timedelta, date
import logging
import json
from cryptography.fernet import Fernet
import base64

_logger = logging.getLogger(__name__)

class HealthRecord(models.Model):
    """Dossier médical étudiant"""
    _name = 'edu.health.record'
    _description = 'Dossier de Santé Étudiant'
    _order = 'student_id, create_date desc'

    # Informations étudiantes
    student_id = fields.Many2one(
        'res.partner',
        string='Étudiant',
        required=True,
        domain=[('is_company', '=', False)]
    )
    
    # Informations médicales de base
    blood_type = fields.Selection([
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ], string='Groupe sanguin')
    
    allergies = fields.Text(
        string='Allergies connues',
        help='Liste des allergies connues de l\'étudiant'
    )
    
    chronic_conditions = fields.Text(
        string='Conditions chroniques',
        help='Maladies chroniques ou conditions médicales particulières'
    )
    
    medications = fields.Text(
        string='Médicaments réguliers',
        help='Liste des médicaments pris régulièrement'
    )
    
    # Contact d'urgence
    emergency_contact_name = fields.Char(
        string='Contact d\'urgence - Nom',
        required=True
    )
    
    emergency_contact_phone = fields.Char(
        string='Contact d\'urgence - Téléphone',
        required=True
    )
    
    emergency_contact_relation = fields.Char(
        string='Relation avec l\'étudiant'
    )
    
    # Informations médicales détaillées
    height = fields.Float(
        string='Taille (cm)',
        help='Taille en centimètres'
    )
    
    weight = fields.Float(
        string='Poids (kg)',
        help='Poids en kilogrammes'
    )
    
    # Historique médical
    medical_history = fields.Text(
        string='Historique médical',
        help='Historique médical complet de l\'étudiant'
    )
    
    # Restrictions et recommandations
    physical_restrictions = fields.Text(
        string='Restrictions physiques',
        help='Restrictions pour les activités physiques'
    )
    
    dietary_restrictions = fields.Text(
        string='Restrictions alimentaires',
        help='Allergies alimentaires ou régimes spéciaux'
    )
    
    # État et suivi
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    last_update = fields.Datetime(
        string='Dernière mise à jour',
        default=fields.Datetime.now
    )
    
    # Informations de création
    create_date = fields.Datetime(
        string='Date de création',
        default=fields.Datetime.now
    )

    # Contraintes
    @api.constrains('student_id')
    def _check_unique_student(self):
        for record in self:
            existing = self.search([
                ('student_id', '=', record.student_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValueError(_('Un dossier médical existe déjà pour cet étudiant.'))

    # Actions
    def action_update_record(self):
        """Mettre à jour la date de dernière modification"""
        self.last_update = fields.Datetime.now()
        return True

    @api.model
    def create(self, vals):
        """Surcharge pour mettre à jour last_update à la création"""
        vals['last_update'] = fields.Datetime.now()
        return super().create(vals)

    def write(self, vals):
        """Surcharge pour mettre à jour last_update à la modification"""
        vals['last_update'] = fields.Datetime.now()
        return super().write(vals)

    # Informations de base
    display_name = fields.Char(
        string='Nom d\'affichage',
        compute='_compute_display_name',
        store=True
    )
    
    record_number = fields.Char(
        string='Numéro de dossier',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau')
    )
    
    # Informations personnelles médicales
    birth_date = fields.Date(
        string='Date de naissance',
        tracking=True,
        help='Date de naissance du patient'
    )
    
    age = fields.Integer(
        string='Âge',
        compute='_compute_age',
        store=True
    )
    
    gender = fields.Selection([
        ('male', 'Masculin'),
        ('female', 'Féminin'),
        ('other', 'Autre'),
    ], string='Sexe', tracking=True)
    
    bmi = fields.Float(
        string='IMC',
        compute='_compute_bmi',
        store=True,
        help='Indice de Masse Corporelle'
    )
    
    bmi_category = fields.Selection([
        ('underweight', 'Insuffisance pondérale'),
        ('normal', 'Poids normal'),
        ('overweight', 'Surpoids'),
        ('obesity_1', 'Obésité modérée'),
        ('obesity_2', 'Obésité sévère'),
        ('obesity_3', 'Obésité morbide'),
    ], string='Catégorie IMC', compute='_compute_bmi_category', store=True)
    
    # Antécédents médicaux
    family_medical_history = fields.Html(
        string='Antécédents familiaux',
        help='Antécédents médicaux familiaux'
    )
    
    surgical_history = fields.Html(
        string='Antécédents chirurgicaux',
        help='Historique des interventions chirurgicales'
    )
    
    # Allergies et intolérances
    food_allergies = fields.Text(
        string='Allergies alimentaires',
        tracking=True
    )
    
    drug_allergies = fields.Text(
        string='Allergies médicamenteuses',
        tracking=True
    )
    
    has_allergies = fields.Boolean(
        string='A des allergies',
        compute='_compute_has_allergies',
        store=True
    )
    
    # Conditions médicales actuelles
    current_medications = fields.Text(
        string='Traitements en cours',
        help='Médicaments actuellement pris',
        tracking=True
    )
    
    medical_devices = fields.Text(
        string='Dispositifs médicaux',
        help='Prothèses, appareils auditifs, etc.',
        tracking=True
    )
    
    # Médecin traitant
    primary_doctor_name = fields.Char(
        string='Médecin traitant',
        tracking=True
    )
    
    primary_doctor_phone = fields.Char(
        string='Téléphone médecin traitant'
    )
    
    primary_doctor_address = fields.Text(
        string='Adresse médecin traitant'
    )
    
    # Assurance et sécurité sociale
    insurance_id = fields.Many2one(
        'health.insurance.policy',
        string='Assurance santé'
    )
    
    social_security_number = fields.Char(
        string='Numéro de sécurité sociale',
        help='Numéro de sécurité sociale (chiffré)'
    )
    
    insurance_number = fields.Char(
        string='Numéro d\'assurance'
    )
    
    # Relations avec autres modèles
    consultation_ids = fields.One2many(
        'edu.medical.consultation',
        'health_record_id',
        string='Consultations'
    )
    
    # vaccination_ids = fields.One2many(
    #     'vaccination.record',
    #     'health_record_id',
    #     string='Vaccinations'
    # )
    
    # emergency_ids = fields.One2many(
    #     'health.emergency',
    #     'health_record_id',
    #     string='Urgences'
    # )
    
    # medication_ids = fields.One2many(
    #     'medication.prescription',
    #     'health_record_id',
    #     string='Prescriptions'
    # )
    
    # Statistiques
    consultation_count = fields.Integer(
        string='Nombre de consultations',
        compute='_compute_consultation_count'
    )
    
    last_consultation_date = fields.Date(
        string='Dernière consultation',
        compute='_compute_last_consultation_date'
    )
    
    # État et autorisations
    state = fields.Selection([
        ('active', 'Actif'),
        ('suspended', 'Suspendu'),
        ('archived', 'Archivé'),
        ('confidential', 'Confidentiel'),
    ], string='État', default='active', tracking=True)
    
    confidentiality_level = fields.Selection([
        ('normal', 'Normal'),
        ('restricted', 'Restreint'),
        ('confidential', 'Confidentiel'),
        ('secret', 'Secret médical'),
    ], string='Niveau de confidentialité', default='normal', tracking=True)
    
    # Autorisations spéciales
    sports_authorization = fields.Boolean(
        string='Autorisé pour le sport',
        default=True,
        tracking=True
    )
    
    swimming_authorization = fields.Boolean(
        string='Autorisé pour la piscine',
        default=True,
        tracking=True
    )
    
    excursion_authorization = fields.Boolean(
        string='Autorisé pour les sorties',
        default=True,
        tracking=True
    )
    
    medication_self_admin = fields.Boolean(
        string='Auto-administration des médicaments',
        default=False,
        help='L\'étudiant peut-il prendre ses médicaments seul?',
        tracking=True
    )
    
    # Examens médicaux obligatoires
    last_medical_exam = fields.Date(
        string='Dernier examen médical'
    )
    
    next_medical_exam = fields.Date(
        string='Prochain examen médical',
        compute='_compute_next_medical_exam',
        store=True
    )
    
    medical_exam_frequency = fields.Integer(
        string='Fréquence examens (mois)',
        default=12,
        help='Fréquence des examens médicaux en mois'
    )
    
    # Fichiers et documents
    medical_documents = fields.Many2many(
        'ir.attachment',
        'health_record_document_rel',
        'record_id',
        'attachment_id',
        string='Documents médicaux'
    )
    
    # QR Code pour accès rapide
    qr_code = fields.Binary(
        string='QR Code',
        compute='_compute_qr_code'
    )
    
    # Champs de suivi
    created_by_id = fields.Many2one(
        'res.users',
        string='Créé par',
        default=lambda self: self.env.user,
        readonly=True
    )
    
    last_updated_by_id = fields.Many2one(
        'res.users',
        string='Dernière modification par',
        readonly=True
    )
    
    @api.depends('student_id.name', 'record_number')
    def _compute_display_name(self):
        """Calculer le nom d'affichage"""
        for record in self:
            if record.student_id:
                record.display_name = f"{record.student_id.name} - {record.record_number}"
            else:
                record.display_name = record.record_number or _('Nouveau dossier')
    
    @api.depends('birth_date')
    def _compute_age(self):
        """Calculer l'âge"""
        today = date.today()
        for record in self:
            if record.birth_date:
                record.age = today.year - record.birth_date.year - \
                    ((today.month, today.day) < (record.birth_date.month, record.birth_date.day))
            else:
                record.age = 0
    
    @api.depends('height', 'weight')
    def _compute_bmi(self):
        """Calculer l'IMC"""
        for record in self:
            if record.height and record.weight and record.height > 0:
                height_m = record.height / 100  # Conversion cm -> m
                record.bmi = round(record.weight / (height_m ** 2), 2)
            else:
                record.bmi = 0.0
    
    @api.depends('bmi', 'age')
    def _compute_bmi_category(self):
        """Déterminer la catégorie d'IMC"""
        for record in self:
            if record.bmi > 0:
                if record.age < 18:
                    # Utiliser les percentiles pour enfants/adolescents
                    # Simplification - en réalité, il faudrait des tables de percentiles
                    if record.bmi < 16:
                        record.bmi_category = 'underweight'
                    elif record.bmi < 25:
                        record.bmi_category = 'normal'
                    elif record.bmi < 30:
                        record.bmi_category = 'overweight'
                    else:
                        record.bmi_category = 'obesity_1'
                else:
                    # Classification adulte standard
                    if record.bmi < 18.5:
                        record.bmi_category = 'underweight'
                    elif record.bmi < 25:
                        record.bmi_category = 'normal'
                    elif record.bmi < 30:
                        record.bmi_category = 'overweight'
                    elif record.bmi < 35:
                        record.bmi_category = 'obesity_1'
                    elif record.bmi < 40:
                        record.bmi_category = 'obesity_2'
                    else:
                        record.bmi_category = 'obesity_3'
            else:
                record.bmi_category = False
    
    @api.depends('allergies', 'food_allergies', 'drug_allergies')
    def _compute_has_allergies(self):
        """Déterminer si le patient a des allergies"""
        for record in self:
            record.has_allergies = bool(
                record.allergies or record.food_allergies or record.drug_allergies
            )
    
    @api.depends('consultation_ids')
    def _compute_consultation_count(self):
        """Compter les consultations"""
        for record in self:
            record.consultation_count = len(record.consultation_ids)
    
    @api.depends('consultation_ids.consultation_date')
    def _compute_last_consultation_date(self):
        """Calculer la date de dernière consultation"""
        for record in self:
            if record.consultation_ids:
                record.last_consultation_date = max(
                    record.consultation_ids.mapped('consultation_date')
                )
            else:
                record.last_consultation_date = False
    
    @api.depends('last_medical_exam', 'medical_exam_frequency')
    def _compute_next_medical_exam(self):
        """Calculer la date du prochain examen médical"""
        for record in self:
            if record.last_medical_exam and record.medical_exam_frequency:
                record.next_medical_exam = record.last_medical_exam + \
                    timedelta(days=record.medical_exam_frequency * 30)
            else:
                record.next_medical_exam = False
    
    def _compute_qr_code(self):
        """Générer le QR code du dossier médical"""
        import qrcode
        from io import BytesIO
        import base64
        
        for record in self:
            if record.id:
                # Créer l'URL sécurisée pour le dossier médical
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                secure_url = f"{base_url}/health/record/{record.record_number}"
                
                # Générer le QR code
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(secure_url)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convertir en base64
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                record.qr_code = base64.b64encode(buffer.getvalue())
            else:
                record.qr_code = False
    
    @api.model
    def check_overdue_medical_exams(self):
        """Vérifier les examens médicaux en retard"""
        today = date.today()
        
        overdue_records = self.search([
            ('next_medical_exam', '<', today),
            ('state', '=', 'active'),
        ])
        
        for record in overdue_records:
            # Créer une activité de rappel
            record.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Examen médical en retard'),
                note=_('L\'étudiant %s a un examen médical en retard depuis le %s') % (
                    record.student_id.name,
                    record.next_medical_exam
                ),
                user_id=self.env.ref('base.user_admin').id,
            )
        
        return len(overdue_records)
    
    @api.model
    def generate_health_statistics(self, date_from=None, date_to=None):
        """Générer des statistiques de santé"""
        domain = [('state', '=', 'active')]
        
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))
        
        records = self.search(domain)
        
        # Statistiques générales
        total_students = len(records)
        students_with_allergies = len(records.filtered('has_allergies'))
        students_with_chronic = len(records.filtered('chronic_conditions'))
        
        # Répartition par groupe sanguin
        blood_type_stats = {}
        for record in records.filtered('blood_type'):
            blood_type = record.blood_type
            blood_type_stats[blood_type] = blood_type_stats.get(blood_type, 0) + 1
        
        # Répartition IMC
        bmi_stats = {}
        for record in records.filtered('bmi_category'):
            bmi_cat = record.bmi_category
            bmi_stats[bmi_cat] = bmi_stats.get(bmi_cat, 0) + 1
        
        # Consultations par mois
        consultation_stats = {}
        for record in records:
            for consultation in record.consultation_ids:
                month_key = consultation.consultation_date.strftime('%Y-%m')
                consultation_stats[month_key] = consultation_stats.get(month_key, 0) + 1
        
        return {
            'total_students': total_students,
            'allergy_rate': (students_with_allergies / total_students * 100) if total_students > 0 else 0,
            'chronic_rate': (students_with_chronic / total_students * 100) if total_students > 0 else 0,
            'blood_type_distribution': blood_type_stats,
            'bmi_distribution': bmi_stats,
            'consultation_trends': consultation_stats,
            'average_age': sum(records.mapped('age')) / len(records) if records else 0,
            'average_bmi': sum(records.filtered('bmi').mapped('bmi')) / len(records.filtered('bmi')) if records.filtered('bmi') else 0,
        }
    
    @api.model
    def import_health_records_from_students(self):
        """Importer les dossiers médicaux depuis les contacts/patients"""
        students_without_health_record = self.env['res.partner'].search([
            ('active', '=', True),
            ('is_company', '=', False),  # Exclure les entreprises
        ]).filtered(lambda s: not self.search([('student_id', '=', s.id)]))
        
        created_records = self.browse()
        
        for student in students_without_health_record:
            record_vals = {
                'student_id': student.id,
                'gender': 'other',  # Valeur par défaut
            }
            
            record = self.create(record_vals)
            created_records |= record
        
        return {
            'created_count': len(created_records),
            'created_records': created_records,
        }
    
    def action_anonymize_record(self):
        """Anonymiser le dossier médical"""
        self.ensure_one()
        
        if not self.env.user.has_group('edu_health_center.group_health_admin'):
            raise AccessError(_('Seuls les administrateurs peuvent anonymiser les dossiers.'))
        
        # Anonymiser les données sensibles
        self.write({
            'social_security_number': 'ANONYMIZED',
            'insurance_number': 'ANONYMIZED',
            'emergency_contact_name': 'Contact Anonyme',
            'emergency_contact_phone': 'XXX-XXX-XXXX',
            'primary_doctor_name': 'Médecin Anonyme',
            'primary_doctor_phone': 'XXX-XXX-XXXX',
            'state': 'archived',
        })
        
        self.message_post(
            body=_('Dossier médical anonymisé par %s') % self.env.user.name,
            message_type='notification'
        )
    
    def read(self, fields=None, load='_classic_read'):
        """Contrôler l'accès en lecture avec déchiffrement"""
        # Vérifier les permissions
        if not self.env.user.has_group('edu_health_center.group_health_user'):
            raise AccessError(_('Accès non autorisé aux dossiers médicaux.'))
        
        result = super().read(fields, load)
        
        # Déchiffrer les données sensibles si l'utilisateur a les droits
        if self.env.user.has_group('edu_health_center.group_health_staff'):
            for record_data in result:
                if 'social_security_number' in record_data and record_data['social_security_number']:
                    record = self.browse(record_data['id'])
                    record_data['social_security_number'] = record._decrypt_sensitive_data(
                        record_data['social_security_number']
                    )
        
        return result
