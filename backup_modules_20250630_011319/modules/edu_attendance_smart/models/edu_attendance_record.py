# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import base64
import logging

_logger = logging.getLogger(__name__)


class EduAttendanceRecord(models.Model):
    """Enregistrement de présence individuel"""
    _name = 'edu.attendance.record'
    _description = 'Enregistrement de présence'
    _order = 'check_in_time desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Identification
    display_name = fields.Char(
        string='Nom',
        compute='_compute_display_name',
        store=True,
        help="Nom d'affichage de l'enregistrement"
    )
    
    # Relations principales
    session_id = fields.Many2one(
        'edu.attendance.session',
        string='Session',
        required=True,
        ondelete='cascade',
        help="Session de présence"
    )
    
    student_id = fields.Many2one(
        'op.student',
        string='Élève',
        help="Élève concerné"
    )
    
    faculty_id = fields.Many2one(
        'op.faculty',
        string='Enseignant',
        help="Enseignant concerné"
    )
    
    device_id = fields.Many2one(
        'edu.attendance.device',
        string='Dispositif',
        help="Dispositif utilisé pour le pointage"
    )
    
    # Justificatif d'absence/retard
    excuse_id = fields.Many2one(
        'edu.attendance.excuse',
        string='Justificatif',
        help="Justificatif d'absence ou de retard associé"
    )
    
    # Informations de pointage
    check_in_time = fields.Datetime(
        string='Heure d\'entrée',
        tracking=True,
        help="Heure de pointage d'entrée"
    )
    
    check_out_time = fields.Datetime(
        string='Heure de sortie',
        tracking=True,
        help="Heure de pointage de sortie"
    )
    
    expected_check_in = fields.Datetime(
        string='Entrée attendue',
        help="Heure d'entrée attendue"
    )
    
    expected_check_out = fields.Datetime(
        string='Sortie attendue',
        help="Heure de sortie attendue"
    )
    
    # Méthode de pointage
    check_in_method = fields.Selection([
        ('qr_code', 'QR Code'),
        ('biometric', 'Biométrie'),
        ('rfid', 'RFID/NFC'),
        ('mobile_app', 'App mobile'),
        ('manual', 'Manuel'),
        ('facial', 'Reconnaissance faciale'),
        ('beacon', 'Bluetooth'),
        ('geolocation', 'Géolocalisation')
    ], string='Méthode d\'entrée', help="Méthode utilisée pour l'entrée")
    
    check_out_method = fields.Selection([
        ('qr_code', 'QR Code'),
        ('biometric', 'Biométrie'),
        ('rfid', 'RFID/NFC'),
        ('mobile_app', 'App mobile'),
        ('manual', 'Manuel'),
        ('facial', 'Reconnaissance faciale'),
        ('beacon', 'Bluetooth'),
        ('geolocation', 'Géolocalisation'),
        ('auto', 'Automatique')
    ], string='Méthode de sortie', help="Méthode utilisée pour la sortie")
    
    # État de présence
    attendance_status = fields.Selection([
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('late', 'En retard'),
        ('excused', 'Excusé'),
        ('partial', 'Présence partielle')
    ], string='Statut', compute='_compute_attendance_status', store=True)
    
    is_absent = fields.Boolean(
        string='Absent',
        default=False,
        tracking=True,
        help="Marquer comme absent"
    )
    
    is_late = fields.Boolean(
        string='En retard',
        compute='_compute_is_late',
        store=True,
        help="Arrivé en retard"
    )
    
    is_excused = fields.Boolean(
        string='Excusé',
        default=False,
        tracking=True,
        help="Absence excusée"
    )
    
    late_minutes = fields.Float(
        string='Retard (min)',
        compute='_compute_late_minutes',
        store=True,
        digits=(6, 2),
        help="Nombre de minutes de retard"
    )
    
    # Durées
    hours_present = fields.Float(
        string='Heures de présence',
        compute='_compute_hours_present',
        store=True,
        digits=(6, 2),
        help="Nombre d'heures de présence effective"
    )
    
    hours_expected = fields.Float(
        string='Heures attendues',
        compute='_compute_hours_expected',
        store=True,
        digits=(6, 2),
        help="Nombre d'heures de présence attendues"
    )
    
    presence_rate = fields.Float(
        string='Taux de présence (%)',
        compute='_compute_presence_rate',
        store=True,
        digits=(5, 2),
        help="Pourcentage de présence effective"
    )
    
    # Géolocalisation
    check_in_latitude = fields.Float(
        string='Latitude entrée',
        digits=(10, 7),
        help="Latitude lors du pointage d'entrée"
    )
    
    check_in_longitude = fields.Float(
        string='Longitude entrée',
        digits=(10, 7),
        help="Longitude lors du pointage d'entrée"
    )
    
    check_out_latitude = fields.Float(
        string='Latitude sortie',
        digits=(10, 7),
        help="Latitude lors du pointage de sortie"
    )
    
    check_out_longitude = fields.Float(
        string='Longitude sortie',
        digits=(10, 7),
        help="Longitude lors du pointage de sortie"
    )
    
    location_verified = fields.Boolean(
        string='Localisation vérifiée',
        default=False,
        help="La géolocalisation a été vérifiée"
    )
    
    # Photos de vérification
    check_in_photo = fields.Binary(
        string='Photo d\'entrée',
        help="Photo prise lors du pointage d'entrée"
    )
    
    check_out_photo = fields.Binary(
        string='Photo de sortie',
        help="Photo prise lors du pointage de sortie"
    )
    
    photo_verified = fields.Boolean(
        string='Photo vérifiée',
        default=False,
        help="La photo a été vérifiée"
    )
    
    # Commentaires et justifications
    comment = fields.Text(
        string='Commentaire',
        help="Commentaire sur la présence"
    )
    
    excuse_reason = fields.Text(
        string='Motif d\'excuse',
        help="Raison de l'absence ou du retard"
    )
    
    excuse_document = fields.Binary(
        string='Justificatif',
        help="Document justificatif (certificat médical, etc.)"
    )
    
    excuse_document_name = fields.Char(
        string='Nom du justificatif',
        help="Nom du fichier justificatif"
    )
    
    # Validation et workflow
    validated = fields.Boolean(
        string='Validé',
        default=False,
        help="Présence validée par un responsable"
    )
    
    validated_by = fields.Many2one(
        'res.users',
        string='Validé par',
        help="Utilisateur qui a validé"
    )
    
    validated_date = fields.Datetime(
        string='Date de validation',
        help="Date de validation"
    )
    
    # Notifications
    notification_sent = fields.Boolean(
        string='Notification envoyée',
        default=False,
        help="Notification envoyée aux parents"
    )
    
    notification_date = fields.Datetime(
        string='Date notification',
        help="Date d'envoi de la notification"
    )
    
    # Données techniques
    user_agent = fields.Char(
        string='User Agent',
        help="Informations sur le navigateur/app utilisé"
    )
    
    ip_address = fields.Char(
        string='Adresse IP',
        help="Adresse IP lors du pointage"
    )
    
    check_in_source = fields.Char(
        string='Source entrée',
        help="Source technique du pointage d'entrée"
    )
    
    check_out_source = fields.Char(
        string='Source sortie',
        help="Source technique du pointage de sortie"
    )
    
    # Calculs automatiques
    @api.depends('student_id', 'faculty_id', 'session_id')
    def _compute_display_name(self):
        """Calcule le nom d'affichage"""
        for record in self:
            if record.student_id:
                name = record.student_id.name
            elif record.faculty_id:
                name = record.faculty_id.name
            else:
                name = "Participant inconnu"
            
            if record.session_id:
                name = f"{name} - {record.session_id.name}"
            
            record.display_name = name
    
    @api.depends('check_in_time', 'expected_check_in')
    def _compute_is_late(self):
        """Calcule si la personne est en retard"""
        for record in self:
            if record.check_in_time and record.expected_check_in:
                if record.session_id and record.session_id.late_threshold:
                    threshold = timedelta(minutes=record.session_id.late_threshold)
                    record.is_late = record.check_in_time > (record.expected_check_in + threshold)
                else:
                    record.is_late = record.check_in_time > record.expected_check_in
            else:
                record.is_late = False
    
    @api.depends('check_in_time', 'expected_check_in')
    def _compute_late_minutes(self):
        """Calcule le nombre de minutes de retard"""
        for record in self:
            if record.check_in_time and record.expected_check_in and record.is_late:
                delta = record.check_in_time - record.expected_check_in
                record.late_minutes = delta.total_seconds() / 60.0
            else:
                record.late_minutes = 0.0
    
    @api.depends('check_in_time', 'check_out_time')
    def _compute_hours_present(self):
        """Calcule les heures de présence effective"""
        for record in self:
            if record.check_in_time:
                if record.check_out_time:
                    # Présence complète avec sortie
                    delta = record.check_out_time - record.check_in_time
                    record.hours_present = delta.total_seconds() / 3600.0
                elif record.session_id and record.session_id.state == 'closed':
                    # Session fermée, calculer jusqu'à la fin prévue
                    end_time = record.expected_check_out or record.session_id.end_datetime
                    if end_time:
                        delta = end_time - record.check_in_time
                        record.hours_present = max(0, delta.total_seconds() / 3600.0)
                    else:
                        record.hours_present = 0.0
                else:
                    # Session en cours, calculer jusqu'à maintenant
                    now = fields.Datetime.now()
                    delta = now - record.check_in_time
                    record.hours_present = delta.total_seconds() / 3600.0
            else:
                record.hours_present = 0.0
    
    @api.depends('expected_check_in', 'expected_check_out', 'session_id')
    def _compute_hours_expected(self):
        """Calcule les heures de présence attendues"""
        for record in self:
            if record.expected_check_in and record.expected_check_out:
                delta = record.expected_check_out - record.expected_check_in
                record.hours_expected = delta.total_seconds() / 3600.0
            elif record.session_id and record.session_id.duration:
                record.hours_expected = record.session_id.duration
            else:
                record.hours_expected = 0.0
    
    @api.depends('hours_present', 'hours_expected')
    def _compute_presence_rate(self):
        """Calcule le taux de présence"""
        for record in self:
            if record.hours_expected and record.hours_expected > 0:
                rate = (record.hours_present / record.hours_expected) * 100
                record.presence_rate = min(100.0, rate)  # Plafonner à 100%
            else:
                record.presence_rate = 0.0 if record.is_absent else 100.0
    
    @api.depends('is_absent', 'is_late', 'is_excused', 'check_in_time')
    def _compute_attendance_status(self):
        """Calcule le statut de présence"""
        for record in self:
            if record.is_absent:
                if record.is_excused:
                    record.attendance_status = 'excused'
                else:
                    record.attendance_status = 'absent'
            elif record.check_in_time:
                if record.is_late:
                    record.attendance_status = 'late'
                elif record.presence_rate < 80:  # Moins de 80% de présence
                    record.attendance_status = 'partial'
                else:
                    record.attendance_status = 'present'
            else:
                record.attendance_status = 'absent'
    
    # Contraintes
    @api.constrains('student_id', 'faculty_id')
    def _check_participant(self):
        """Vérifie qu'il y a un participant (élève ou enseignant)"""
        for record in self:
            if not record.student_id and not record.faculty_id:
                raise ValidationError(_("Un enregistrement doit concerner un élève ou un enseignant"))
            if record.student_id and record.faculty_id:
                raise ValidationError(_("Un enregistrement ne peut pas concerner à la fois un élève et un enseignant"))
    
    @api.constrains('check_in_time', 'check_out_time')
    def _check_chronology(self):
        """Vérifie la chronologie des pointages"""
        for record in self:
            if record.check_in_time and record.check_out_time:
                if record.check_in_time >= record.check_out_time:
                    raise ValidationError(_("L'heure de sortie doit être postérieure à l'heure d'entrée"))
    
    @api.constrains('check_in_latitude', 'check_in_longitude')
    def _check_coordinates(self):
        """Vérifie les coordonnées GPS"""
        for record in self:
            if record.check_in_latitude and not (-90 <= record.check_in_latitude <= 90):
                raise ValidationError(_("La latitude doit être entre -90 et 90"))
            if record.check_in_longitude and not (-180 <= record.check_in_longitude <= 180):
                raise ValidationError(_("La longitude doit être entre -180 et 180"))
    
    # Actions
    def action_mark_present(self):
        """Marque comme présent manuellement"""
        self.ensure_one()
        self.write({
            'check_in_time': fields.Datetime.now(),
            'check_in_method': 'manual',
            'is_absent': False,
            'validated': True,
            'validated_by': self.env.user.id,
            'validated_date': fields.Datetime.now()
        })
    
    def action_mark_absent(self):
        """Marque comme absent"""
        self.ensure_one()
        self.write({
            'is_absent': True,
            'check_in_time': False,
            'check_out_time': False,
            'validated': True,
            'validated_by': self.env.user.id,
            'validated_date': fields.Datetime.now()
        })
    
    def action_excuse_absence(self):
        """Excuse l'absence"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Excuser l\'absence'),
            'res_model': 'edu.attendance.excuse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_attendance_record_id': self.id},
        }
    
    def action_validate(self):
        """Valide l'enregistrement"""
        self.ensure_one()
        self.write({
            'validated': True,
            'validated_by': self.env.user.id,
            'validated_date': fields.Datetime.now()
        })
    
    def action_check_in(self, method='manual', device_id=None, **kwargs):
        """Effectue un pointage d'entrée"""
        self.ensure_one()
        
        # Vérifications
        if self.check_in_time:
            raise UserError(_("L'entrée a déjà été enregistrée"))
        
        if self.session_id and not self.session_id.is_check_in_open():
            if not self.session_id.allow_late_check_in:
                raise UserError(_("La fenêtre de pointage d'entrée est fermée"))
        
        # Enregistrer le pointage
        values = {
            'check_in_time': fields.Datetime.now(),
            'check_in_method': method,
            'is_absent': False,
        }
        
        if device_id:
            values['device_id'] = device_id
        
        # Ajouter les données GPS si fournies
        if kwargs.get('latitude') and kwargs.get('longitude'):
            values.update({
                'check_in_latitude': kwargs['latitude'],
                'check_in_longitude': kwargs['longitude'],
                'location_verified': self._verify_location(kwargs['latitude'], kwargs['longitude'])
            })
        
        # Ajouter la photo si fournie
        if kwargs.get('photo'):
            values['check_in_photo'] = kwargs['photo']
        
        # Ajouter les données techniques
        if kwargs.get('user_agent'):
            values['user_agent'] = kwargs['user_agent']
        if kwargs.get('ip_address'):
            values['ip_address'] = kwargs['ip_address']
        if kwargs.get('source'):
            values['check_in_source'] = kwargs['source']
        
        self.write(values)
        
        # Log de l'action
        self.message_post(
            body=_("Pointage d'entrée effectué via %s") % method,
            message_type='notification'
        )
        
        return True
    
    def action_check_out(self, method='manual', device_id=None, **kwargs):
        """Effectue un pointage de sortie"""
        self.ensure_one()
        
        # Vérifications
        if not self.check_in_time:
            raise UserError(_("Aucune entrée enregistrée"))
        
        if self.check_out_time:
            raise UserError(_("La sortie a déjà été enregistrée"))
        
        if self.session_id and self.session_id.require_check_out:
            if not self.session_id.is_check_out_open():
                raise UserError(_("La fenêtre de pointage de sortie est fermée"))
        
        # Enregistrer le pointage
        values = {
            'check_out_time': fields.Datetime.now(),
            'check_out_method': method,
        }
        
        if device_id:
            values['device_id'] = device_id
        
        # Ajouter les données GPS si fournies
        if kwargs.get('latitude') and kwargs.get('longitude'):
            values.update({
                'check_out_latitude': kwargs['latitude'],
                'check_out_longitude': kwargs['longitude']
            })
        
        # Ajouter la photo si fournie
        if kwargs.get('photo'):
            values['check_out_photo'] = kwargs['photo']
        
        # Ajouter les données techniques
        if kwargs.get('source'):
            values['check_out_source'] = kwargs['source']
        
        self.write(values)
        
        # Log de l'action
        self.message_post(
            body=_("Pointage de sortie effectué via %s") % method,
            message_type='notification'
        )
        
        return True
    
    # Méthodes utilitaires
    def _verify_location(self, latitude, longitude):
        """Vérifie si la localisation est dans la zone autorisée"""
        self.ensure_one()
        if not self.session_id:
            return True
        
        # Vérifier avec les coordonnées de la session
        if self.session_id.latitude and self.session_id.longitude:
            return self.session_id._is_in_gps_range(latitude, longitude)
        
        # Vérifier avec le dispositif utilisé
        if self.device_id:
            return self.device_id.is_in_range(latitude, longitude)
        
        return True
    
    def get_status_color(self):
        """Retourne la couleur selon le statut"""
        self.ensure_one()
        colors = {
            'present': 'success',
            'late': 'warning',
            'absent': 'danger',
            'excused': 'info',
            'partial': 'warning'
        }
        return colors.get(self.attendance_status, 'muted')
    
    def get_status_icon(self):
        """Retourne l'icône selon le statut"""
        self.ensure_one()
        icons = {
            'present': 'fa-check-circle',
            'late': 'fa-clock-o',
            'absent': 'fa-times-circle',
            'excused': 'fa-info-circle',
            'partial': 'fa-adjust'
        }
        return icons.get(self.attendance_status, 'fa-question-circle')
    
    def send_notification_to_parents(self):
        """Envoie une notification aux parents"""
        self.ensure_one()
        if not self.student_id or self.notification_sent:
            return False
        
        # Logique d'envoi de notification
        # À implémenter selon le système de notification choisi
        
        self.write({
            'notification_sent': True,
            'notification_date': fields.Datetime.now()
        })
        
        return True
    
    # Méthodes de recherche et filtres
    @api.model
    def get_attendance_summary(self, domain=None, groupby='session_id'):
        """Retourne un résumé des présences"""
        domain = domain or []
        records = self.search(domain)
        
        summary = {}
        for record in records:
            key = getattr(record, groupby.replace('_id', '')).id if '_id' in groupby else getattr(record, groupby)
            
            if key not in summary:
                summary[key] = {
                    'total': 0,
                    'present': 0,
                    'absent': 0,
                    'late': 0,
                    'excused': 0
                }
            
            summary[key]['total'] += 1
            summary[key][record.attendance_status] += 1
        
        return summary
    
    @api.model
    def get_student_attendance_rate(self, student_id, date_from=None, date_to=None):
        """Calcule le taux de présence d'un élève"""
        domain = [('student_id', '=', student_id)]
        
        if date_from:
            domain.append(('expected_check_in', '>=', date_from))
        if date_to:
            domain.append(('expected_check_in', '<=', date_to))
        
        records = self.search(domain)
        
        if not records:
            return 0.0
        
        present_count = len(records.filtered(lambda r: r.attendance_status in ['present', 'late']))
        total_count = len(records)
        
        return (present_count / total_count) * 100 if total_count > 0 else 0.0
    
    # Méthodes d'import/export
    @api.model
    def import_attendance_data(self, data):
        """Importe des données de présence"""
        # À implémenter pour l'import de données externes
        pass
    
    def export_attendance_data(self):
        """Exporte les données de présence"""
        # À implémenter pour l'export de données
        pass
