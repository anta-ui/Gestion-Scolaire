# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Identification pour les présences
    student_code = fields.Char('Code étudiant', help="Code unique pour identifier l'étudiant")
    teacher_code = fields.Char('Code enseignant', help="Code unique pour identifier l'enseignant")
    
    # Type de personne
    is_student = fields.Boolean('Est un étudiant', default=False)
    is_teacher = fields.Boolean('Est un enseignant', default=False)
    
    # Badges et cartes
    badge_number = fields.Char('Numéro de badge')
    rfid_code = fields.Char('Code RFID/NFC')
    
    # QR Code personnel
    personal_qr_code = fields.Char('QR Code personnel', compute='_compute_personal_qr_code', store=True)
    qr_code_image = fields.Binary('Image QR Code', compute='_compute_qr_code_image')
    
    # Données biométriques
    biometric_data_ids = fields.One2many('edu.biometric.data', 'partner_id', 'Données biométriques')
    has_biometric_data = fields.Boolean('A des données biométriques', compute='_compute_has_biometric_data')
    
    # Présences
    attendance_record_ids = fields.One2many('edu.attendance.record', 'student_id', 'Enregistrements de présence')
    excuse_ids = fields.One2many('edu.attendance.excuse', 'student_id', 'Justificatifs')
    
    # Sessions enseignées (pour les enseignants)
    taught_session_ids = fields.One2many('edu.attendance.session', 'teacher_id', 'Sessions enseignées')
    
    # Statistiques de présence
    total_attendance_records = fields.Integer('Total présences', compute='_compute_attendance_stats')
    present_count = fields.Integer('Nombre présent', compute='_compute_attendance_stats')
    absent_count = fields.Integer('Nombre absent', compute='_compute_attendance_stats')
    late_count = fields.Integer('Nombre retards', compute='_compute_attendance_stats')
    excused_count = fields.Integer('Nombre justifié', compute='_compute_attendance_stats')
    
    attendance_rate = fields.Float('Taux de présence (%)', compute='_compute_attendance_stats')
    absence_rate = fields.Float('Taux d\'absence (%)', compute='_compute_attendance_stats')
    
    # Configuration
    allow_mobile_checkin = fields.Boolean('Autoriser pointage mobile', default=True)
    require_location_checkin = fields.Boolean('Exiger géolocalisation', default=False)
    max_late_minutes = fields.Integer('Minutes de retard max', default=15,
                                     help="Au-delà, considéré comme absent")
    
    # Notifications
    notify_parents_absence = fields.Boolean('Notifier parents absence', default=True)
    parent_email = fields.Char('Email parent/tuteur')
    parent_phone = fields.Char('Téléphone parent/tuteur')
    
    # Dernières activités
    last_attendance_date = fields.Datetime('Dernière présence', compute='_compute_last_activities')
    last_session_taught = fields.Datetime('Dernière session enseignée', compute='_compute_last_activities')
    
    @api.depends('student_code', 'teacher_code', 'name')
    def _compute_personal_qr_code(self):
        for partner in self:
            if partner.is_student and partner.student_code:
                partner.personal_qr_code = f"STUDENT:{partner.student_code}:{partner.id}"
            elif partner.is_teacher and partner.teacher_code:
                partner.personal_qr_code = f"TEACHER:{partner.teacher_code}:{partner.id}"
            else:
                partner.personal_qr_code = f"PERSON:{partner.id}"
    
    @api.depends('personal_qr_code')
    def _compute_qr_code_image(self):
        for partner in self:
            if partner.personal_qr_code:
                try:
                    import qrcode
                    import io
                    import base64
                    
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(partner.personal_qr_code)
                    qr.make(fit=True)
                    
                    img = qr.make_image(fill_color="black", back_color="white")
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    buffer.seek(0)
                    
                    partner.qr_code_image = base64.b64encode(buffer.getvalue())
                except ImportError:
                    partner.qr_code_image = False
            else:
                partner.qr_code_image = False
    
    @api.depends('biometric_data_ids')
    def _compute_has_biometric_data(self):
        for partner in self:
            partner.has_biometric_data = bool(partner.biometric_data_ids.filtered(lambda b: b.state == 'active'))
    
    @api.depends('attendance_record_ids')
    def _compute_attendance_stats(self):
        for partner in self:
            records = partner.attendance_record_ids
            
            partner.total_attendance_records = len(records)
            partner.present_count = len(records.filtered(lambda r: r.state == 'present'))
            partner.absent_count = len(records.filtered(lambda r: r.state == 'absent'))
            partner.late_count = len(records.filtered(lambda r: r.state == 'late'))
            partner.excused_count = len(records.filtered(lambda r: r.is_excused))
            
            if partner.total_attendance_records:
                partner.attendance_rate = (partner.present_count + partner.late_count) / partner.total_attendance_records * 100
                partner.absence_rate = partner.absent_count / partner.total_attendance_records * 100
            else:
                partner.attendance_rate = 0
                partner.absence_rate = 0
    
    @api.depends('attendance_record_ids', 'taught_session_ids')
    def _compute_last_activities(self):
        for partner in self:
            # Dernière présence
            last_attendance = partner.attendance_record_ids.sorted('check_in', reverse=True)[:1]
            partner.last_attendance_date = last_attendance.check_in if last_attendance else False
            
            # Dernière session enseignée
            last_session = partner.taught_session_ids.sorted('start_time', reverse=True)[:1]
            partner.last_session_taught = last_session.start_time if last_session else False
    
    def action_view_attendance_records(self):
        """Voir les enregistrements de présence"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Présences de %s') % self.name,
            'res_model': 'edu.attendance.record',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id}
        }
    
    def action_view_excuses(self):
        """Voir les justificatifs"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Justificatifs de %s') % self.name,
            'res_model': 'edu.attendance.excuse',
            'view_mode': 'tree,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id}
        }
    
    def action_view_biometric_data(self):
        """Voir les données biométriques"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Données biométriques de %s') % self.name,
            'res_model': 'edu.biometric.data',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }
    
    def action_create_excuse(self):
        """Créer un justificatif d'absence"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nouveau justificatif'),
            'res_model': 'edu.attendance.excuse',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_student_id': self.id}
        }
    
    def check_attendance_today(self):
        """Vérifier la présence du jour"""
        self.ensure_one()
        today = fields.Date.today()
        today_records = self.attendance_record_ids.filtered(lambda r: r.date == today)
        
        if not today_records:
            return {'status': 'no_record', 'message': _('Aucun enregistrement aujourd\'hui')}
        
        latest_record = today_records.sorted('check_in', reverse=True)[0]
        
        return {
            'status': latest_record.state,
            'message': _('Statut: %s') % dict(latest_record._fields['state'].selection)[latest_record.state],
            'check_in': latest_record.check_in,
            'session': latest_record.session_id.name if latest_record.session_id else False
        }
    
    def get_attendance_summary(self, date_from=None, date_to=None):
        """Obtenir un résumé des présences sur une période"""
        self.ensure_one()
        
        if not date_from:
            date_from = fields.Date.today() - timedelta(days=30)
        if not date_to:
            date_to = fields.Date.today()
        
        records = self.attendance_record_ids.filtered(
            lambda r: date_from <= r.date <= date_to
        )
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'total_days': len(records.mapped('date')),
            'present_days': len(records.filtered(lambda r: r.state == 'present')),
            'absent_days': len(records.filtered(lambda r: r.state == 'absent')),
            'late_days': len(records.filtered(lambda r: r.state == 'late')),
            'excused_days': len(records.filtered(lambda r: r.is_excused)),
            'attendance_rate': (len(records.filtered(lambda r: r.state in ['present', 'late'])) / len(records) * 100) if records else 0,
            'total_late_minutes': sum(records.mapped('late_minutes'))
        }
    
    def send_absence_notification(self, session_name=None):
        """Envoyer une notification d'absence aux parents"""
        self.ensure_one()
        
        if not self.notify_parents_absence:
            return False
        
        if not (self.parent_email or self.parent_phone):
            return False
        
        # Préparer le message
        message = _("Votre enfant %s est absent") % self.name
        if session_name:
            message += _(" à la session: %s") % session_name
        
        # Envoyer email si disponible
        if self.parent_email:
            mail_values = {
                'subject': _('Notification d\'absence - %s') % self.name,
                'body_html': f'<p>{message}</p>',
                'email_to': self.parent_email,
                'auto_delete': True,
            }
            self.env['mail.mail'].create(mail_values).send()
        
        # Envoyer SMS si disponible (nécessite module SMS)
        if self.parent_phone:
            try:
                # Logique d'envoi SMS à implémenter selon le fournisseur
                pass
            except:
                pass
        
        return True
