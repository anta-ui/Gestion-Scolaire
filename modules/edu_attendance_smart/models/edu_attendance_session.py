# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class EduAttendanceSession(models.Model):
    _name = 'edu.attendance.session'
    _description = 'Session de présence'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc, id desc'
    _rec_name = 'name'

    # Informations de base
    name = fields.Char('Nom', required=True, tracking=True)
    code = fields.Char('Code', required=True, copy=False, tracking=True)
    description = fields.Text('Description')
    
    # Type de session
    session_type = fields.Selection([
        ('course', 'Cours'),
        ('exam', 'Examen'),
        ('activity', 'Activité'),
        ('meeting', 'Réunion'),
        ('other', 'Autre')
    ], string='Type de session', default='course', required=True, tracking=True)
    
    # Horaires
    start_datetime = fields.Datetime('Début', required=True, tracking=True)
    end_datetime = fields.Datetime('Fin', required=True, tracking=True)
    duration = fields.Float('Durée (heures)', compute='_compute_duration', store=True)
    timezone = fields.Selection('_get_timezone_list', string='Fuseau horaire', 
                               default=lambda self: self.env.context.get('tz'))
    
    # État de la session
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('scheduled', 'Programmée'),
        ('open', 'Ouvert'),
        ('in_progress', 'En cours'),
        ('closed', 'Fermé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    
    # Relations enseignement - utilisation de res.partner pour la compatibilité
    course_name = fields.Char(
        string='Matière/Cours',
        help="Nom de la matière ou cours concerné"
    )
    
    # Enseignant principal (res.partner)
    teacher_id = fields.Many2one(
        'res.partner',
        string='Enseignant',
        domain="[('is_teacher', '=', True)]",
        help="Enseignant responsable"
    )
    
    # Classes/Groupes sous forme de texte pour éviter les dépendances
    class_name = fields.Char(
        string='Classe/Groupe',
        help="Nom de la classe ou groupe concerné"
    )
    
    batch_name = fields.Char(
        string='Section',
        help="Nom de la section ou sous-groupe"
    )
    
    # Lieux - salle simple
    classroom_name = fields.Char(
        string='Salle de classe',
        help="Nom de la salle de classe"
    )
    
    location_id = fields.Many2one(
        'edu.location',
        string='Lieu',
        help="Lieu personnalisé"
    )
    
    external_location = fields.Char('Lieu externe', help="Adresse ou description du lieu externe")
    
    # Géolocalisation
    latitude = fields.Float('Latitude', digits=(10, 7))
    longitude = fields.Float('Longitude', digits=(10, 7))
    gps_radius = fields.Integer('Rayon GPS (mètres)', default=50,
                               help="Rayon autorisé pour le pointage géolocalisé")
    
    # Participants - utilisation de res.partner
    student_ids = fields.Many2many(
        'res.partner',
        'attendance_session_student_rel',
        'session_id', 'student_id',
        string='Étudiants',
        domain="[('is_student', '=', True)]",
        help="Liste des étudiants concernés"
    )
    
    teacher_ids = fields.Many2many(
        'res.partner',
        'attendance_session_teacher_rel',
        'session_id', 'partner_id',
        string='Enseignants participants',
        domain="[('is_teacher', '=', True)]",
        help="Enseignants participants"
    )
    
    # Dispositifs de pointage autorisés
    attendance_device_ids = fields.Many2many(
        'edu.attendance.device',
        'attendance_session_device_rel',
        'session_id', 'device_id',
        string='Dispositifs de pointage',
        help="Dispositifs autorisés pour cette session"
    )
    
    # Fenêtres de pointage
    check_in_start = fields.Datetime('Ouverture pointage entrée', 
                                    help="Heure d'ouverture du pointage d'entrée")
    check_in_end = fields.Datetime('Fermeture pointage entrée',
                                  help="Heure de fermeture du pointage d'entrée")
    check_out_start = fields.Datetime('Ouverture pointage sortie',
                                     help="Heure d'ouverture du pointage de sortie")
    check_out_end = fields.Datetime('Fermeture pointage sortie',
                                   help="Heure de fermeture du pointage de sortie")
    
    # Configuration
    allow_late_check_in = fields.Boolean('Autoriser retards', default=True,
                                        help="Autoriser le pointage d'entrée en retard")
    late_threshold = fields.Integer('Seuil retard (minutes)', default=15,
                                   help="Nombre de minutes pour considérer un retard")
    require_check_out = fields.Boolean('Sortie obligatoire', default=False,
                                      help="Pointage de sortie obligatoire")
    require_photo = fields.Boolean('Photo obligatoire', default=False,
                                  help="Photo obligatoire lors du pointage")
    auto_close_session = fields.Boolean('Fermeture automatique', default=True,
                                       help="Fermer automatiquement la session à la fin")
    
    # Notifications
    notify_parents = fields.Boolean('Notifier parents', default=True,
                                   help="Notifier les parents des absences")
    notify_delay = fields.Integer('Délai notification (minutes)', default=30,
                                 help="Délai avant envoi des notifications")
    notification_template_id = fields.Many2one(
        'mail.template',
        string='Modèle de notification',
        help="Modèle d'email pour les notifications"
    )
    
    # Relations avec les enregistrements
    attendance_record_ids = fields.One2many(
        'edu.attendance.record',
        'session_id',
        string='Enregistrements de présence'
    )
    
    # QR Code de session
    qr_code_id = fields.Many2one(
        'edu.qr.code',
        string='QR Code de session',
        help="QR Code généré pour cette session"
    )
    
    # Statistiques calculées
    expected_count = fields.Integer('Attendus', compute='_compute_stats', store=True)
    present_count = fields.Integer('Présents', compute='_compute_stats', store=True)
    absent_count = fields.Integer('Absents', compute='_compute_stats', store=True)
    late_count = fields.Integer('En retard', compute='_compute_stats', store=True)
    excused_count = fields.Integer('Excusés', compute='_compute_stats', store=True)
    attendance_rate = fields.Float('Taux de présence (%)', compute='_compute_stats', store=True)
    
    # Métadonnées
    created_by = fields.Many2one('res.users', string='Créé par', default=lambda self: self.env.user)
    opened_date = fields.Datetime('Date ouverture', readonly=True)
    closed_date = fields.Datetime('Date fermeture', readonly=True)
    
    # Champs calculés
    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for session in self:
            if session.start_datetime and session.end_datetime:
                diff = session.end_datetime - session.start_datetime
                session.duration = diff.total_seconds() / 3600.0
            else:
                session.duration = 0.0
    
    @api.depends('student_ids', 'attendance_record_ids')
    def _compute_stats(self):
        for session in self:
            session.expected_count = len(session.student_ids)
            
            # Compter les enregistrements réels
            records = session.attendance_record_ids
            session.present_count = len(records.filtered(lambda r: r.attendance_status == 'present'))
            session.absent_count = len(records.filtered(lambda r: r.attendance_status == 'absent'))
            session.late_count = len(records.filtered(lambda r: r.attendance_status == 'late'))
            session.excused_count = len(records.filtered(lambda r: r.attendance_status == 'excused'))
            
            # Calculer le taux de présence
            if session.expected_count > 0:
                session.attendance_rate = (session.present_count / session.expected_count) * 100
            else:
                session.attendance_rate = 0.0
    
    def _get_timezone_list(self):
        # Retourner les fuseaux horaires disponibles
        return []
    
    # Contraintes
    @api.constrains('start_datetime', 'end_datetime')
    def _check_dates(self):
        for session in self:
            if session.start_datetime and session.end_datetime:
                if session.start_datetime >= session.end_datetime:
                    raise ValidationError(_('La date de début doit être antérieure à la date de fin'))
    
    @api.constrains('code')
    def _check_code_unique(self):
        for session in self:
            if session.code:
                existing = self.search([
                    ('code', '=', session.code),
                    ('id', '!=', session.id)
                ])
                if existing:
                    raise ValidationError(_('Ce code de session existe déjà'))
    
    # Méthodes de workflow
    def action_schedule(self):
        self.write({'state': 'scheduled'})
        return True
    
    def action_open(self):
        self.write({
            'state': 'open',
            'opened_date': fields.Datetime.now()
        })
        return True
    
    def action_start(self):
        self.write({'state': 'in_progress'})
        return True
    
    def action_close(self):
        self.write({
            'state': 'closed',
            'closed_date': fields.Datetime.now()
        })
        return True
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True
    
    def action_reopen(self):
        self.write({'state': 'open'})
        return True
    
    def is_check_in_open(self):
        return self.state in ['open', 'in_progress']

    def is_check_out_open(self):
        return self.state in ['in_progress']
    
    # Autres méthodes utilitaires
    def get_participant_attendance(self, participant_id, participant_type):
        """Récupère l'enregistrement de présence d'un participant"""
        domain = [('session_id', '=', self.id)]
        if participant_type == 'student':
            domain.append(('student_id', '=', participant_id))
        elif participant_type == 'teacher':
            domain.append(('teacher_id', '=', participant_id))
        
        return self.env['edu.attendance.record'].search(domain, limit=1)
    
    @api.model
    def create(self, vals):
        # Générer un code si pas fourni
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('edu.attendance.session') or 'NEW'
        return super().create(vals)
