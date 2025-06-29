# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class EduAttendanceSession(models.Model):
    """Sessions de présence (cours, événements, sorties)"""
    _name = 'edu.attendance.session'
    _description = 'Session de présence'
    _order = 'start_datetime desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nom de la session',
        required=True,
        tracking=True,
        help="Nom de la session de présence"
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        size=20,
        help="Code unique de la session"
    )
    
    description = fields.Text(
        string='Description',
        help="Description de la session"
    )
    
    # Type de session
    session_type = fields.Selection([
        ('course', 'Cours'),
        ('exam', 'Examen'),
        ('meeting', 'Réunion'),
        ('event', 'Événement'),
        ('trip', 'Sortie scolaire'),
        ('activity', 'Activité'),
        ('study_hall', 'Étude surveillée'),
        ('break', 'Récréation'),
        ('lunch', 'Déjeuner'),
        ('other', 'Autre')
    ], string='Type de session', required=True, default='course')
    
    # Planification
    start_datetime = fields.Datetime(
        string='Début',
        required=True,
        tracking=True,
        help="Date et heure de début"
    )
    
    end_datetime = fields.Datetime(
        string='Fin',
        required=True,
        tracking=True,
        help="Date et heure de fin"
    )
    
    duration = fields.Float(
        string='Durée (heures)',
        compute='_compute_duration',
        store=True,
        digits=(6, 2),
        help="Durée de la session en heures"
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
    ], string='Fuseau horaire', default='Africa/Dakar', help="Fuseau horaire de la session")
    
    # Relations académiques
    course_id = fields.Many2one(
        'op.course',
        string='Matière',
        help="Matière enseignée"
    )
    
    faculty_id = fields.Many2one(
        'op.faculty',
        string='Enseignant (OpenEduCat)',
        help="Enseignant responsable (OpenEduCat)"
    )
    
    # Nouveau champ pour res.partner
    teacher_id = fields.Many2one(
        'res.partner',
        string='Enseignant',
        domain="[('is_teacher', '=', True)]",
        help="Enseignant responsable"
    )
    
    standard_id = fields.Many2one(
        'op.batch',
        string='Classe/Groupe',
        help="Classe/Groupe concerné"
    )
    
    batch_id = fields.Many2one(
        'op.batch',
        string='Groupe',
        help="Groupe/Section"
    )
    
    # Lieu
    classroom_id = fields.Many2one(
        'op.classroom',
        string='Salle',
        help="Salle de classe"
    )
    
    location_id = fields.Many2one(
        'edu.location',
        string='Lieu',
        help="Lieu de la session"
    )
    
    # Pour les sorties
    external_location = fields.Char(
        string='Lieu externe',
        help="Adresse du lieu externe"
    )
    
    latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        help="Latitude du lieu"
    )
    
    longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        help="Longitude du lieu"
    )
    
    gps_radius = fields.Float(
        string='Rayon GPS (m)',
        default=100.0,
        digits=(8, 2),
        help="Rayon autorisé pour le pointage GPS"
    )
    
    # Participants
    student_ids = fields.Many2many(
        'op.student',
        'session_student_rel',
        'session_id',
        'student_id',
        string='Élèves participants',
        help="Liste des élèves qui doivent être présents"
    )
    
    faculty_ids = fields.Many2many(
        'op.faculty',
        'session_faculty_rel',
        'session_id',
        'faculty_id',
        string='Enseignants participants',
        help="Liste des enseignants participants"
    )
    
    expected_count = fields.Integer(
        string='Participants attendus',
        compute='_compute_expected_count',
        store=True,
        help="Nombre total de participants attendus"
    )
    
    # Configuration de pointage
    attendance_device_ids = fields.Many2many(
        'edu.attendance.device',
        'session_device_rel',
        'session_id',
        'device_id',
        string='Dispositifs autorisés',
        help="Dispositifs de pointage autorisés pour cette session"
    )
    
    qr_code_id = fields.Many2one(
        'edu.qr.code',
        string='QR Code',
        help="QR Code spécifique à cette session"
    )
    
    # Fenêtres de pointage
    check_in_start = fields.Datetime(
        string='Début pointage entrée',
        help="Heure à partir de laquelle on peut pointer l'entrée"
    )
    
    check_in_end = fields.Datetime(
        string='Fin pointage entrée',
        help="Heure limite pour pointer l'entrée"
    )
    
    check_out_start = fields.Datetime(
        string='Début pointage sortie',
        help="Heure à partir de laquelle on peut pointer la sortie"
    )
    
    check_out_end = fields.Datetime(
        string='Fin pointage sortie',
        help="Heure limite pour pointer la sortie"
    )
    
    # Règles de présence
    allow_late_check_in = fields.Boolean(
        string='Retards autorisés',
        default=True,
        help="Autoriser les pointages en retard"
    )
    
    late_threshold = fields.Float(
        string='Seuil de retard (min)',
        default=15.0,
        digits=(6, 2),
        help="Délai en minutes avant d'être considéré en retard"
    )
    
    require_check_out = fields.Boolean(
        string='Sortie obligatoire',
        default=False,
        help="Exiger un pointage de sortie"
    )
    
    require_photo = fields.Boolean(
        string='Photo obligatoire',
        default=False,
        help="Exiger une photo lors du pointage"
    )
    
    auto_close_session = fields.Boolean(
        string='Fermeture automatique',
        default=True,
        help="Fermer automatiquement la session à l'heure de fin"
    )
    
    # État de la session
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('scheduled', 'Programmé'),
        ('open', 'Ouvert'),
        ('in_progress', 'En cours'),
        ('closed', 'Fermé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    
    # Statistiques de présence
    attendance_record_ids = fields.One2many(
        'edu.attendance.record',
        'session_id',
        string='Enregistrements de présence'
    )
    
    present_count = fields.Integer(
        string='Présents',
        compute='_compute_attendance_stats',
        store=True,
        help="Nombre de présents"
    )
    
    absent_count = fields.Integer(
        string='Absents',
        compute='_compute_attendance_stats',
        store=True,
        help="Nombre d'absents"
    )
    
    late_count = fields.Integer(
        string='Retards',
        compute='_compute_attendance_stats',
        store=True,
        help="Nombre de retards"
    )
    
    excused_count = fields.Integer(
        string='Excusés',
        compute='_compute_attendance_stats',
        store=True,
        help="Nombre d'absences excusées"
    )
    
    attendance_rate = fields.Float(
        string='Taux de présence (%)',
        compute='_compute_attendance_stats',
        store=True,
        digits=(5, 2),
        help="Pourcentage de présence"
    )
    
    # Notifications
    notify_parents = fields.Boolean(
        string='Notifier les parents',
        default=True,
        help="Envoyer des notifications aux parents"
    )
    
    notify_delay = fields.Integer(
        string='Délai notification (min)',
        default=30,
        help="Délai avant envoi de notification d'absence"
    )
    
    notification_template_id = fields.Many2one(
        'mail.template',
        string='Modèle de notification',
        help="Modèle d'email pour les notifications"
    )
    
    # Métadonnées
    created_by = fields.Many2one(
        'res.users',
        string='Créé par',
        default=lambda self: self.env.user,
        readonly=True
    )
    
    opened_date = fields.Datetime(
        string='Date d\'ouverture',
        readonly=True
    )
    
    closed_date = fields.Datetime(
        string='Date de fermeture',
        readonly=True
    )
    
    # Calculs
    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        """Calcule la durée de la session"""
        for record in self:
            if record.start_datetime and record.end_datetime:
                delta = record.end_datetime - record.start_datetime
                record.duration = delta.total_seconds() / 3600.0
            else:
                record.duration = 0.0
    
    @api.depends('student_ids', 'faculty_ids')
    def _compute_expected_count(self):
        """Calcule le nombre de participants attendus"""
        for record in self:
            record.expected_count = len(record.student_ids) + len(record.faculty_ids)
    
    @api.depends('attendance_record_ids', 'student_ids', 'faculty_ids')
    def _compute_attendance_stats(self):
        """Calcule les statistiques de présence"""
        for record in self:
            # Compter les présents (avec check-in)
            present_records = record.attendance_record_ids.filtered(
                lambda r: r.check_in_time and not r.is_absent
            )
            record.present_count = len(present_records)
            
            # Compter les retards
            late_records = record.attendance_record_ids.filtered('is_late')
            record.late_count = len(late_records)
            
            # Compter les excusés
            excused_records = record.attendance_record_ids.filtered('is_excused')
            record.excused_count = len(excused_records)
            
            # Calculer les absents (attendus - présents)
            record.absent_count = record.expected_count - record.present_count
            
            # Calculer le taux de présence
            if record.expected_count > 0:
                record.attendance_rate = (record.present_count / record.expected_count) * 100
            else:
                record.attendance_rate = 0.0
    
    # Contraintes
    @api.constrains('start_datetime', 'end_datetime')
    def _check_dates(self):
        """Vérifie la cohérence des dates"""
        for record in self:
            if record.start_datetime and record.end_datetime:
                if record.start_datetime >= record.end_datetime:
                    raise ValidationError(_("La date de début doit être antérieure à la date de fin"))
    
    @api.constrains('check_in_start', 'check_in_end', 'start_datetime')
    def _check_check_in_window(self):
        """Vérifie la fenêtre de pointage d'entrée"""
        for record in self:
            if record.check_in_start and record.check_in_end:
                if record.check_in_start >= record.check_in_end:
                    raise ValidationError(_("L'heure de début de pointage doit être antérieure à l'heure de fin"))
            
            if record.check_in_end and record.start_datetime:
                if record.check_in_end > record.start_datetime + timedelta(hours=1):
                    raise ValidationError(_("La fenêtre de pointage d'entrée ne peut pas s'étendre trop après le début"))
    
    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self):
        """Vérifie les coordonnées GPS"""
        for record in self:
            if record.latitude and not (-90 <= record.latitude <= 90):
                raise ValidationError(_("La latitude doit être entre -90 et 90"))
            if record.longitude and not (-180 <= record.longitude <= 180):
                raise ValidationError(_("La longitude doit être entre -180 et 180"))
    
    @api.constrains('code')
    def _check_unique_code(self):
        """Vérifie l'unicité du code"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Le code '%s' existe déjà") % record.code)
    
    # Actions du workflow
    def action_schedule(self):
        """Programme la session"""
        for record in self:
            if record.state == 'draft':
                record.state = 'scheduled'
                record._setup_default_check_windows()
                record._generate_qr_code()
    
    def action_open(self):
        """Ouvre la session pour les pointages"""
        for record in self:
            if record.state == 'scheduled':
                record.state = 'open'
                record.opened_date = fields.Datetime.now()
                record._create_attendance_records()
    
    def action_start(self):
        """Démarre la session"""
        for record in self:
            if record.state == 'open':
                record.state = 'in_progress'
    
    def action_close(self):
        """Ferme la session"""
        for record in self:
            if record.state in ['open', 'in_progress']:
                record.state = 'closed'
                record.closed_date = fields.Datetime.now()
                record._process_final_attendance()
                if record.notify_parents:
                    record._send_attendance_notifications()
    
    def action_cancel(self):
        """Annule la session"""
        for record in self:
            if record.state in ['draft', 'scheduled', 'open']:
                record.state = 'cancelled'
    
    def action_reopen(self):
        """Réouvre la session"""
        for record in self:
            if record.state == 'closed':
                record.state = 'open'
                record.closed_date = False
    
    # Méthodes auxiliaires
    def _setup_default_check_windows(self):
        """Configure les fenêtres de pointage par défaut"""
        self.ensure_one()
        if not self.check_in_start:
            self.check_in_start = self.start_datetime - timedelta(minutes=30)
        if not self.check_in_end:
            self.check_in_end = self.start_datetime + timedelta(minutes=30)
        if not self.check_out_start and self.require_check_out:
            self.check_out_start = self.end_datetime - timedelta(minutes=15)
        if not self.check_out_end and self.require_check_out:
            self.check_out_end = self.end_datetime + timedelta(minutes=30)
    
    def _generate_qr_code(self):
        """Génère un QR code pour la session"""
        self.ensure_one()
        if not self.qr_code_id:
            qr_code = self.env['edu.qr.code'].create({
                'name': f"QR Session {self.name}",
                'qr_type': 'session',
                'session_id': self.id,
                'content': f"session:{self.id}:{self.code}",
                'expiry_date': self.end_datetime,
                'active': True
            })
            self.qr_code_id = qr_code.id
    
    def _create_attendance_records(self):
        """Crée les enregistrements de présence pour tous les participants"""
        self.ensure_one()
        
        # Créer pour les élèves
        for student in self.student_ids:
            existing = self.env['edu.attendance.record'].search([
                ('session_id', '=', self.id),
                ('student_id', '=', student.id)
            ])
            if not existing:
                self.env['edu.attendance.record'].create({
                    'session_id': self.id,
                    'student_id': student.id,
                    'expected_check_in': self.start_datetime,
                    'expected_check_out': self.end_datetime if self.require_check_out else False,
                })
        
        # Créer pour les enseignants
        for faculty in self.faculty_ids:
            existing = self.env['edu.attendance.record'].search([
                ('session_id', '=', self.id),
                ('faculty_id', '=', faculty.id)
            ])
            if not existing:
                self.env['edu.attendance.record'].create({
                    'session_id': self.id,
                    'faculty_id': faculty.id,
                    'expected_check_in': self.start_datetime,
                    'expected_check_out': self.end_datetime if self.require_check_out else False,
                })
    
    def _process_final_attendance(self):
        """Traite les présences finales à la fermeture"""
        self.ensure_one()
        
        # Marquer comme absents ceux qui n'ont pas pointé
        no_checkin_records = self.attendance_record_ids.filtered(
            lambda r: not r.check_in_time and not r.is_excused
        )
        no_checkin_records.write({'is_absent': True})
        
        # Calculer les heures de présence
        for record in self.attendance_record_ids:
            record._compute_hours_present()
    
    def _send_attendance_notifications(self):
        """Envoie les notifications de présence aux parents"""
        self.ensure_one()
        if not self.notification_template_id:
            return
        
        # Notifier pour les absences non excusées
        absent_records = self.attendance_record_ids.filtered(
            lambda r: r.is_absent and not r.is_excused and r.student_id
        )
        
        for record in absent_records:
            if record.student_id.parent_ids:
                for parent in record.student_id.parent_ids:
                    self.notification_template_id.send_mail(
                        record.id,
                        email_values={'email_to': parent.email},
                        force_send=True
                    )
    
    # Actions utilisateur
    def action_view_attendance(self):
        """Affiche les enregistrements de présence"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Présences - %s') % self.name,
            'res_model': 'edu.attendance.record',
            'view_mode': 'tree,form',
            'domain': [('session_id', '=', self.id)],
            'context': {'default_session_id': self.id},
        }
    
    def action_take_attendance(self):
        """Interface de prise de présence manuelle"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Prise de présence - %s') % self.name,
            'res_model': 'edu.attendance.session',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': {'attendance_mode': True},
        }
    
    def action_show_qr_code(self):
        """Affiche le QR code de la session"""
        self.ensure_one()
        if not self.qr_code_id:
            self._generate_qr_code()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('QR Code - %s') % self.name,
            'res_model': 'edu.qr.code',
            'view_mode': 'form',
            'res_id': self.qr_code_id.id,
            'target': 'new',
        }
    
    def action_attendance_report(self):
        """Génère le rapport de présence"""
        self.ensure_one()
        return self.env.ref('edu_attendance_smart.action_report_session_attendance').report_action(self)
    
    # Méthodes utilitaires
    def is_check_in_open(self):
        """Vérifie si la fenêtre de pointage d'entrée est ouverte"""
        self.ensure_one()
        now = fields.Datetime.now()
        return (self.state in ['open', 'in_progress'] and 
                self.check_in_start <= now <= self.check_in_end)
    
    def is_check_out_open(self):
        """Vérifie si la fenêtre de pointage de sortie est ouverte"""
        self.ensure_one()
        if not self.require_check_out:
            return False
        now = fields.Datetime.now()
        return (self.state in ['in_progress', 'closed'] and 
                self.check_out_start <= now <= self.check_out_end)
    
    def get_participant_attendance(self, participant_id, participant_type='student'):
        """Récupère l'enregistrement de présence d'un participant"""
        self.ensure_one()
        domain = [('session_id', '=', self.id)]
        if participant_type == 'student':
            domain.append(('student_id', '=', participant_id))
        else:
            domain.append(('faculty_id', '=', participant_id))
        
        return self.env['edu.attendance.record'].search(domain, limit=1)
    
    def name_get(self):
        """Affichage personnalisé"""
        result = []
        for record in self:
            name = record.name
            if record.course_id:
                name = f"{record.course_id.name} - {name}"
            if record.start_datetime:
                date_str = record.start_datetime.strftime('%d/%m %H:%M')
                name = f"{name} ({date_str})"
            result.append((record.id, name))
        return result
    
    @api.model
    def create(self, vals):
        """Génère automatiquement un code si non fourni"""
        if not vals.get('code'):
            sequence = self.env['ir.sequence'].next_by_code('edu.attendance.session') or '/'
            vals['code'] = sequence
        return super().create(vals)
    
    # Tâches automatiques
    @api.model
    def _cron_auto_open_sessions(self):
        """Ouvre automatiquement les sessions programmées"""
        now = fields.Datetime.now()
        sessions_to_open = self.search([
            ('state', '=', 'scheduled'),
            ('check_in_start', '<=', now)
        ])
        sessions_to_open.action_open()
    
    @api.model
    def _cron_auto_start_sessions(self):
        """Démarre automatiquement les sessions ouvertes"""
        now = fields.Datetime.now()
        sessions_to_start = self.search([
            ('state', '=', 'open'),
            ('start_datetime', '<=', now)
        ])
        sessions_to_start.action_start()
    
    @api.model
    def _cron_auto_close_sessions(self):
        """Ferme automatiquement les sessions terminées"""
        now = fields.Datetime.now()
        sessions_to_close = self.search([
            ('state', 'in', ['open', 'in_progress']),
            ('end_datetime', '<=', now),
            ('auto_close_session', '=', True)
        ])
        sessions_to_close.action_close()
    
    @api.model
    def _cron_send_absence_notifications(self):
        """Envoie les notifications d'absence en retard"""
        now = fields.Datetime.now()
        sessions = self.search([
            ('state', '=', 'in_progress'),
            ('notify_parents', '=', True),
            ('start_datetime', '<=', now - timedelta(minutes=30))
        ])
        
        for session in sessions:
            absent_records = session.attendance_record_ids.filtered(
                lambda r: not r.check_in_time and not r.is_excused and 
                         not r.notification_sent and r.student_id
            )
            
            for record in absent_records:
                # Logique de notification à implémenter
                record.notification_sent = True
