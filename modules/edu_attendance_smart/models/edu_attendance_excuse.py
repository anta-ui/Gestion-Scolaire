# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import base64
import logging

_logger = logging.getLogger(__name__)


class EduAttendanceExcuse(models.Model):
    _name = 'edu.attendance.excuse'
    _description = 'Justificatif d\'absence'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Référence', required=True, copy=False, readonly=True, 
                      default=lambda self: _('Nouveau'))
    student_id = fields.Many2one('res.partner', 'Étudiant', required=True,
                                domain="[('is_student', '=', True)]")
    session_id = fields.Many2one('edu.attendance.session', 'Session concernée')
    
    # Type de justificatif
    excuse_type = fields.Selection([
        ('medical', 'Médical'),
        ('family', 'Familial'),
        ('sport', 'Sport'),
        ('other', 'Autre')
    ], string='Type de justificatif', required=True, default='medical')
    
    # Période d'absence
    start_date = fields.Date('Date de début', required=True)
    end_date = fields.Date('Date de fin', required=True)
    duration_days = fields.Integer('Durée (jours)', compute='_compute_duration', store=True)
    
    # Raison
    reason = fields.Text('Raison', required=True)
    detailed_reason = fields.Html('Raison détaillée')
    
    # Documents
    document_ids = fields.Many2many('ir.attachment', 'excuse_attachment_rel', 
                                   'excuse_id', 'attachment_id', string='Documents')
    
    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté')
    ], string='Statut', default='draft', tracking=True)
    
    # Validation
    validated_by = fields.Many2one('res.users', 'Validé par')
    validation_date = fields.Datetime('Date de validation')
    validation_comment = fields.Text('Commentaire de validation')
    
    # Notifications
    notify_parents = fields.Boolean('Notifier les parents', default=True)
    notify_teachers = fields.Boolean('Notifier les enseignants', default=True)
    
    # Métadonnées
    created_by = fields.Many2one('res.users', 'Créé par', default=lambda self: self.env.user)
    submitted_date = fields.Datetime('Date de soumission')
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('edu.attendance.excuse') or _('Nouveau')
        return super().create(vals)

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.duration_days = delta.days + 1
            else:
                record.duration_days = 0

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date > record.end_date:
                    raise ValidationError(_('La date de début doit être antérieure à la date de fin'))

    def action_submit(self):
        """Soumettre le justificatif"""
        self.ensure_one()
        self.write({
            'state': 'submitted',
            'submitted_date': fields.Datetime.now()
        })
        return True

    def action_approve(self):
        """Approuver le justificatif"""
        self.ensure_one()
        self.write({
            'state': 'approved',
            'validated_by': self.env.user.id,
            'validation_date': fields.Datetime.now()
        })
        return True

    def action_reject(self):
        """Rejeter le justificatif"""
        self.ensure_one()
        self.write({
            'state': 'rejected',
            'validated_by': self.env.user.id,
            'validation_date': fields.Datetime.now()
        })
        return True

    def action_reset_to_draft(self):
        """Remettre en brouillon"""
        self.ensure_one()
        self.write({'state': 'draft'})
        return True

    def send_notifications(self):
        """Envoyer les notifications"""
        for record in self:
            if record.notify_parents and record.student_id.parent_email:
                # Envoyer email aux parents
                pass
            
            if record.notify_teachers and record.session_id.teacher_id:
                # Notifier les enseignants
                pass

    def get_excuse_summary(self):
        """Obtenir un résumé du justificatif"""
        return {
            'student': record.student_id.name,
            'type': dict(record._fields['excuse_type'].selection)[record.excuse_type],
            'period': f"{record.start_date} - {record.end_date}",
            'duration': f"{record.duration_days} jours",
            'status': dict(record._fields['state'].selection)[record.state]
        } 