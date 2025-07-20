# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import base64
import logging

_logger = logging.getLogger(__name__)


class EduAttendanceRecord(models.Model):
    _name = 'edu.attendance.record'
    _description = 'Enregistrement de présence'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'check_in_time desc'

    name = fields.Char('Référence', required=True, copy=False, readonly=True, 
                      default=lambda self: _('Nouveau'))
    session_id = fields.Many2one('edu.attendance.session', 'Session', required=True, ondelete='cascade')
    student_id = fields.Many2one('res.partner', 'Étudiant', required=True, 
                                domain="[('is_student', '=', True)]")
    teacher_id = fields.Many2one('res.partner', 'Enseignant', 
                                domain="[('is_teacher', '=', True)]")
    device_id = fields.Many2one('edu.attendance.device', 'Dispositif')
    qr_code_id = fields.Many2one('edu.qr.code', 'QR Code utilisé')
    
    check_in_time = fields.Datetime('Heure d\'entrée')
    check_out_time = fields.Datetime('Heure de sortie')
    attendance_status = fields.Selection([
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('late', 'En retard'),
        ('excused', 'Excusé'),
        ('partial', 'Partiel')
    ], string='Statut', default='absent', tracking=True)
    
    is_absent = fields.Boolean('Absent', default=False)
    is_late = fields.Boolean('En retard', default=False)
    validated = fields.Boolean('Validé', default=False)
    
    # Champs additionnels
    photo = fields.Binary('Photo')
    location = fields.Char('Localisation')
    comment = fields.Text('Commentaire')
    excuse_id = fields.Many2one('edu.attendance.excuse', 'Justificatif')
    
    # Champs calculés
    duration = fields.Float('Durée (heures)', compute='_compute_duration', store=True)
    late_minutes = fields.Integer('Minutes de retard', compute='_compute_late_minutes')
    
    # Contraintes
    _sql_constraints = [
        ('unique_session_student', 'unique(session_id, student_id)', 
         'Un étudiant ne peut avoir qu\'un seul enregistrement par session!')
    ]

    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('edu.attendance.record') or _('Nouveau')
        return super().create(vals)

    @api.depends('check_in_time', 'check_out_time')
    def _compute_duration(self):
        for record in self:
            if record.check_in_time and record.check_out_time:
                duration = record.check_out_time - record.check_in_time
                record.duration = duration.total_seconds() / 3600.0
            else:
                record.duration = 0.0

    @api.depends('check_in_time', 'session_id.start_datetime')
    def _compute_late_minutes(self):
        for record in self:
            if record.check_in_time and record.session_id.start_datetime:
                if record.check_in_time > record.session_id.start_datetime:
                    late = record.check_in_time - record.session_id.start_datetime
                    record.late_minutes = int(late.total_seconds() / 60)
                else:
                    record.late_minutes = 0
            else:
                record.late_minutes = 0

    @api.onchange('check_in_time')
    def _onchange_check_in_time(self):
        if self.check_in_time and self.session_id.start_datetime:
            if self.check_in_time > self.session_id.start_datetime:
                self.is_late = True
                self.attendance_status = 'late'
            else:
                self.is_late = False
                self.attendance_status = 'present'

    def action_validate(self):
        """Valider l'enregistrement de présence"""
        self.ensure_one()
        self.validated = True
        self.message_post(body=_("Enregistrement validé par %s") % self.env.user.name)

    def action_invalidate(self):
        """Invalider l'enregistrement de présence"""
        self.ensure_one()
        self.validated = False
        self.message_post(body=_("Enregistrement invalidé par %s") % self.env.user.name)
