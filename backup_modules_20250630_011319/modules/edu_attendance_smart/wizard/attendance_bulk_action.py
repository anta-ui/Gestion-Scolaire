# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AttendanceBulkAction(models.TransientModel):
    _name = 'attendance.bulk.action'
    _description = 'Actions en masse sur les présences'

    action_type = fields.Selection([
        ('mark_present', 'Marquer présent'),
        ('mark_absent', 'Marquer absent'),
        ('mark_late', 'Marquer en retard'),
        ('add_excuse', 'Ajouter un justificatif'),
        ('remove_excuse', 'Retirer le justificatif'),
        ('delete_records', 'Supprimer les enregistrements')
    ], string='Action', required=True, default='mark_present')
    
    session_id = fields.Many2one('edu.attendance.session', 'Session', required=True)
    student_ids = fields.Many2many('res.partner', string='Étudiants',
                                  domain="[('is_student', '=', True)]")
    
    # Pour les justificatifs
    excuse_type = fields.Selection([
        ('medical', 'Médical'),
        ('family', 'Familial'),
        ('transport', 'Transport'),
        ('personal', 'Personnel'),
        ('other', 'Autre')
    ], string='Type de justificatif')
    excuse_reason = fields.Text('Motif du justificatif')
    
    # Pour les retards
    late_minutes = fields.Integer('Minutes de retard', default=0)
    
    def action_apply(self):
        """Appliquer l'action en masse"""
        self.ensure_one()
        
        if not self.student_ids:
            raise UserError(_('Veuillez sélectionner au moins un étudiant.'))
        
        if self.action_type == 'mark_present':
            self._mark_present()
        elif self.action_type == 'mark_absent':
            self._mark_absent()
        elif self.action_type == 'mark_late':
            self._mark_late()
        elif self.action_type == 'add_excuse':
            self._add_excuse()
        elif self.action_type == 'remove_excuse':
            self._remove_excuse()
        elif self.action_type == 'delete_records':
            self._delete_records()
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _mark_present(self):
        """Marquer les étudiants comme présents"""
        for student in self.student_ids:
            record = self.env['edu.attendance.record'].search([
                ('student_id', '=', student.id),
                ('session_id', '=', self.session_id.id)
            ], limit=1)
            
            if record:
                record.write({'state': 'present'})
            else:
                self.env['edu.attendance.record'].create({
                    'student_id': student.id,
                    'session_id': self.session_id.id,
                    'state': 'present',
                    'check_in': fields.Datetime.now(),
                    'check_in_method': 'manual'
                })
    
    def _mark_absent(self):
        """Marquer les étudiants comme absents"""
        for student in self.student_ids:
            record = self.env['edu.attendance.record'].search([
                ('student_id', '=', student.id),
                ('session_id', '=', self.session_id.id)
            ], limit=1)
            
            if record:
                record.write({'state': 'absent'})
            else:
                self.env['edu.attendance.record'].create({
                    'student_id': student.id,
                    'session_id': self.session_id.id,
                    'state': 'absent',
                    'check_in_method': 'manual'
                })
    
    def _mark_late(self):
        """Marquer les étudiants en retard"""
        for student in self.student_ids:
            record = self.env['edu.attendance.record'].search([
                ('student_id', '=', student.id),
                ('session_id', '=', self.session_id.id)
            ], limit=1)
            
            if record:
                record.write({
                    'state': 'late',
                    'late_minutes': self.late_minutes
                })
            else:
                self.env['edu.attendance.record'].create({
                    'student_id': student.id,
                    'session_id': self.session_id.id,
                    'state': 'late',
                    'late_minutes': self.late_minutes,
                    'check_in': fields.Datetime.now(),
                    'check_in_method': 'manual'
                })
    
    def _add_excuse(self):
        """Ajouter un justificatif"""
        if not self.excuse_type:
            raise UserError(_('Veuillez sélectionner un type de justificatif.'))
        
        for student in self.student_ids:
            # Créer le justificatif
            excuse = self.env['edu.attendance.excuse'].create({
                'student_id': student.id,
                'reason': self.excuse_type,
                'description': self.excuse_reason or 'Justificatif ajouté en masse',
                'date': self.session_id.start_datetime.date(),
                'time_from': self.session_id.start_datetime.hour + self.session_id.start_datetime.minute/60.0,
                'time_to': self.session_id.end_datetime.hour + self.session_id.end_datetime.minute/60.0,
                'state': 'approved'
            })
            
            # Marquer les enregistrements comme justifiés
            records = self.env['edu.attendance.record'].search([
                ('student_id', '=', student.id),
                ('session_id', '=', self.session_id.id)
            ])
            records.write({
                'is_excused': True,
                'excuse_id': excuse.id
            })
    
    def _remove_excuse(self):
        """Retirer le justificatif"""
        for student in self.student_ids:
            records = self.env['edu.attendance.record'].search([
                ('student_id', '=', student.id),
                ('session_id', '=', self.session_id.id)
            ])
            records.write({
                'is_excused': False,
                'excuse_id': False
            })
    
    def _delete_records(self):
        """Supprimer les enregistrements"""
        records = self.env['edu.attendance.record'].search([
            ('student_id', 'in', self.student_ids.ids),
            ('session_id', '=', self.session_id.id)
        ])
        records.unlink() 