# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class OpStudentAttendance(models.Model):
    _name = 'op.student.attendance'
    _description = 'Présence étudiant (compatibilité)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char('Référence', required=True, copy=False, readonly=True, 
                      default=lambda self: _('Nouveau'))
    student_id = fields.Many2one('res.partner', 'Étudiant', required=True,
                                domain="[('is_student', '=', True)]")
    session_id = fields.Many2one('edu.attendance.session', 'Session')
    
    # Informations de base
    date = fields.Date('Date', required=True, default=fields.Date.today)
    check_in = fields.Datetime('Heure d\'entrée')
    check_out = fields.Datetime('Heure de sortie')
    
    # Statut
    state = fields.Selection([
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('late', 'En retard'),
        ('excused', 'Excusé'),
        ('partial', 'Partiel')
    ], string='Statut', default='absent', tracking=True)
    
    # Calculs
    duration = fields.Float('Durée (heures)', compute='_compute_duration', store=True)
    late_minutes = fields.Integer('Minutes de retard', compute='_compute_late_minutes')
    
    # Métadonnées
    created_by = fields.Many2one('res.users', 'Créé par', default=lambda self: self.env.user)
    notes = fields.Text('Notes')
    
    # Contraintes
    _sql_constraints = [
        ('unique_student_date', 'unique(student_id, date)', 
         'Un étudiant ne peut avoir qu\'un seul enregistrement par jour!')
    ]

    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('op.student.attendance') or _('Nouveau')
        return super().create(vals)

    @api.depends('check_in', 'check_out')
    def _compute_duration(self):
        for record in self:
            if record.check_in and record.check_out:
                duration = record.check_out - record.check_in
                record.duration = duration.total_seconds() / 3600.0
            else:
                record.duration = 0.0

    @api.depends('check_in', 'session_id.start_datetime')
    def _compute_late_minutes(self):
        for record in self:
            if record.check_in and record.session_id.start_datetime:
                if record.check_in > record.session_id.start_datetime:
                    late = record.check_in - record.session_id.start_datetime
                    record.late_minutes = int(late.total_seconds() / 60)
                else:
                    record.late_minutes = 0
            else:
                record.late_minutes = 0

    @api.onchange('check_in')
    def _onchange_check_in(self):
        if self.check_in and self.session_id.start_datetime:
            if self.check_in > self.session_id.start_datetime:
                self.state = 'late'
            else:
                self.state = 'present'

    def action_check_in(self):
        """Pointage d'entrée"""
        self.ensure_one()
        self.write({
            'check_in': fields.Datetime.now(),
            'state': 'present'
        })
        return True

    def action_check_out(self):
        """Pointage de sortie"""
        self.ensure_one()
        self.write({'check_out': fields.Datetime.now()})
        return True

    def action_mark_absent(self):
        """Marquer comme absent"""
        self.ensure_one()
        self.write({'state': 'absent'})
        return True

    def action_mark_excused(self):
        """Marquer comme excusé"""
        self.ensure_one()
        self.write({'state': 'excused'})
        return True

    def get_attendance_summary(self):
        """Obtenir un résumé de présence"""
        return {
            'student': self.student_id.name,
            'date': self.date,
            'status': dict(self._fields['state'].selection)[self.state],
            'check_in': self.check_in,
            'check_out': self.check_out,
            'duration': f"{self.duration:.2f} heures",
            'late_minutes': self.late_minutes
        }
