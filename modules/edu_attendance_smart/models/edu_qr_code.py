# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import qrcode
import base64
from io import BytesIO
import secrets
import hashlib
import logging

_logger = logging.getLogger(__name__)


class EduQRCode(models.Model):
    """Gestion des QR codes pour le pointage"""
    _name = 'edu.qr.code'
    _description = 'QR Code de pointage'
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom',
        required=True,
        help="Nom du QR code"
    )
    
    # Type de QR code
    qr_type = fields.Selection([
        ('student', 'Élève personnel'),
        ('faculty', 'Enseignant personnel'),
        ('session', 'Session de cours'),
        ('device', 'Dispositif de pointage'),
        ('location', 'Lieu/Salle'),
        ('event', 'Événement'),
        ('temporary', 'Temporaire'),
        ('emergency', 'Urgence')
    ], string='Type de QR code', required=True, default='student')
    
    # Contenu et données
    content = fields.Text(
        string='Contenu',
        required=True,
        help="Contenu encodé dans le QR code"
    )
    
    encrypted_content = fields.Text(
        string='Contenu chiffré',
        help="Version chiffrée du contenu"
    )
    
    qr_token = fields.Char(
        string='Token',
        required=True,
        default=lambda self: self._generate_token(),
        help="Token unique d'authentification"
    )
    
    security_hash = fields.Char(
        string='Hash de sécurité',
        compute='_compute_security_hash',
        store=True,
        help="Hash de sécurité pour validation"
    )
    
    # Relations
    student_id = fields.Many2one(
        'res.partner',
        string='Élève',
        domain="[('is_student', '=', True)]",
        help="Élève propriétaire du QR code"
    )
    
    teacher_id = fields.Many2one(
        'res.partner',
        string='Enseignant',
        domain="[('is_teacher', '=', True)]",
        help="Enseignant propriétaire du QR code"
    )
    
    session_id = fields.Many2one(
        'edu.attendance.session',
        string='Session',
        help="Session associée au QR code"
    )
    
    device_id = fields.Many2one(
        'edu.attendance.device',
        string='Dispositif',
        help="Dispositif associé au QR code"
    )
    
    classroom_name = fields.Char(
        string='Salle',
        help="Nom de la salle associée au QR code"
    )
    
    # Image du QR code
    qr_image = fields.Binary(
        string='Image QR Code',
        compute='_compute_qr_image',
        store=True,
        help="Image générée du QR code"
    )
    
    qr_image_filename = fields.Char(
        string='Nom fichier',
        compute='_compute_qr_image_filename',
        help="Nom du fichier image"
    )
    
    # Configuration
    size = fields.Selection([
        ('small', 'Petit (150x150)'),
        ('medium', 'Moyen (300x300)'),
        ('large', 'Grand (600x600)'),
        ('xlarge', 'Très grand (1200x1200)')
    ], string='Taille', default='medium', help="Taille de l'image générée")
    
    error_correction = fields.Selection([
        ('L', 'Faible (~7%)'),
        ('M', 'Moyen (~15%)'),
        ('Q', 'Élevé (~25%)'),
        ('H', 'Très élevé (~30%)')
    ], string='Correction d\'erreur', default='M', help="Niveau de correction d'erreur")
    
    border_size = fields.Integer(
        string='Taille bordure',
        default=4,
        help="Taille de la bordure en modules"
    )
    
    # Validité et sécurité
    active = fields.Boolean(
        string='Actif',
        default=True,
        help="QR code actif et utilisable"
    )
    
    expiry_date = fields.Datetime(
        string='Date d\'expiration',
        help="Date d'expiration du QR code"
    )
    
    max_uses = fields.Integer(
        string='Utilisations max',
        default=0,
        help="Nombre maximum d'utilisations (0 = illimité)"
    )
    
    current_uses = fields.Integer(
        string='Utilisations actuelles',
        default=0,
        help="Nombre d'utilisations actuelles"
    )
    
    is_single_use = fields.Boolean(
        string='Usage unique',
        default=False,
        help="QR code à usage unique"
    )
    
    is_expired = fields.Boolean(
        string='Expiré',
        compute='_compute_is_expired',
        help="QR code expiré"
    )
    
    # Restrictions d'usage
    allowed_devices = fields.Many2many(
        'edu.attendance.device',
        'qr_code_device_rel',
        'qr_code_id',
        'device_id',
        string='Dispositifs autorisés',
        help="Dispositifs autorisés à scanner ce QR code"
    )
    
    ip_whitelist = fields.Text(
        string='IPs autorisées',
        help="Liste des adresses IP autorisées (une par ligne)"
    )
    
    time_restrictions = fields.Boolean(
        string='Restrictions horaires',
        default=False,
        help="Activer les restrictions d'horaires"
    )
    
    valid_from_time = fields.Float(
        string='Valide à partir de',
        default=0.0,
        help="Heure de début de validité (24h)"
    )
    
    valid_to_time = fields.Float(
        string='Valide jusqu\'à',
        default=24.0,
        help="Heure de fin de validité (24h)"
    )
    
    # Statistiques d'usage
    scan_count = fields.Integer(
        string='Nombre de scans',
        default=0,
        help="Nombre total de scans"
    )
    
    success_scan_count = fields.Integer(
        string='Scans réussis',
        default=0,
        help="Nombre de scans réussis"
    )
    
    last_scan_date = fields.Datetime(
        string='Dernier scan',
        help="Date du dernier scan"
    )
    
    last_scan_ip = fields.Char(
        string='IP dernier scan',
        help="Adresse IP du dernier scan"
    )
    
    last_scan_device = fields.Char(
        string='Dispositif dernier scan',
        help="Dispositif du dernier scan"
    )
    
    # Logs de sécurité
    security_log_ids = fields.One2many(
        'edu.qr.code.log',
        'qr_code_id',
        string='Logs de sécurité'
    )
    
    # Calculs
    @api.depends('content', 'qr_token')
    def _compute_security_hash(self):
        """Calcule le hash de sécurité"""
        for record in self:
            if record.content and record.qr_token:
                data = f"{record.content}:{record.qr_token}:{record.id}"
                record.security_hash = hashlib.sha256(data.encode()).hexdigest()
            else:
                record.security_hash = ""
    
    @api.depends('content', 'size', 'error_correction', 'border_size')
    def _compute_qr_image(self):
        """Génère l'image du QR code"""
        for record in self:
            if record.content:
                try:
                    # Tailles en pixels
                    sizes = {
                        'small': 150,
                        'medium': 300,
                        'large': 600,
                        'xlarge': 1200
                    }
                    
                    # Créer le QR code
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=getattr(qrcode.constants, f'ERROR_CORRECT_{record.error_correction}'),
                        box_size=10,
                        border=record.border_size,
                    )
                    
                    qr.add_data(record.content)
                    qr.make(fit=True)
                    
                    # Créer l'image
                    img = qr.make_image(fill_color="black", back_color="white")
                    
                    # Redimensionner
                    size = sizes.get(record.size, 300)
                    img = img.resize((size, size))
                    
                    # Convertir en base64
                    buffer = BytesIO()
                    img.save(buffer, format='PNG')
                    
                    record.qr_image = base64.b64encode(buffer.getvalue()).decode()
                    
                except Exception as e:
                    _logger.error(f"Erreur génération QR code pour {record.name}: {e}")
                    record.qr_image = False
            else:
                record.qr_image = False
    
    @api.depends('name')
    def _compute_qr_image_filename(self):
        """Calcule le nom de fichier"""
        for record in self:
            if record.name:
                safe_name = "".join(c for c in record.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                record.qr_image_filename = f"qr_code_{safe_name.replace(' ', '_')}.png"
            else:
                record.qr_image_filename = "qr_code.png"
    
    @api.depends('expiry_date', 'max_uses', 'current_uses')
    def _compute_is_expired(self):
        """Vérifie si le QR code est expiré"""
        now = fields.Datetime.now()
        for record in self:
            expired = False
            
            # Vérifier la date d'expiration
            if record.expiry_date and now > record.expiry_date:
                expired = True
            
            # Vérifier le nombre d'utilisations
            if record.max_uses > 0 and record.current_uses >= record.max_uses:
                expired = True
            
            # Vérifier usage unique
            if record.is_single_use and record.current_uses > 0:
                expired = True
            
            record.is_expired = expired
    
    # Méthodes de génération
    @api.model
    def _generate_token(self):
        """Génère un token unique"""
        return secrets.token_urlsafe(32)
    
    def regenerate_token(self):
        """Régénère le token"""
        self.ensure_one()
        self.qr_token = self._generate_token()
        self._log_security_event('token_regenerated')
    
    def regenerate_qr_code(self):
        """Régénère complètement le QR code"""
        self.ensure_one()
        self.qr_token = self._generate_token()
        # Le contenu sera recalculé automatiquement
        self._update_content()
        self._log_security_event('qr_regenerated')
    
    def _update_content(self):
        """Met à jour le contenu du QR code"""
        self.ensure_one()
        
        # Construire le contenu selon le type
        if self.qr_type == 'student' and self.student_id:
            self.content = f"student:{self.student_id.id}:{self.qr_token}"
        elif self.qr_type == 'faculty' and self.faculty_id:
            self.content = f"faculty:{self.faculty_id.id}:{self.qr_token}"
        elif self.qr_type == 'session' and self.session_id:
            self.content = f"session:{self.session_id.id}:{self.qr_token}"
        elif self.qr_type == 'device' and self.device_id:
            self.content = f"device:{self.device_id.id}:{self.qr_token}"
        elif self.qr_type == 'location' and self.classroom_id:
            self.content = f"location:{self.classroom_id.id}:{self.qr_token}"
        else:
            self.content = f"{self.qr_type}:{self.id}:{self.qr_token}"
    
    # Validation et sécurité
    def validate_scan(self, device_id=None, ip_address=None, user_agent=None):
        """Valide un scan du QR code"""
        self.ensure_one()
        
        # Incrémenter les statistiques
        self.scan_count += 1
        self.last_scan_date = fields.Datetime.now()
        if ip_address:
            self.last_scan_ip = ip_address
        
        # Vérifications de sécurité
        if not self.active:
            self._log_security_event('scan_inactive', ip_address, device_id, user_agent)
            raise UserError(_("QR code inactif"))
        
        if self.is_expired:
            self._log_security_event('scan_expired', ip_address, device_id, user_agent)
            raise UserError(_("QR code expiré"))
        
        # Vérifier les restrictions horaires
        if self.time_restrictions:
            import datetime
            now = datetime.datetime.now()
            current_time = now.hour + now.minute / 60.0
            
            if not (self.valid_from_time <= current_time <= self.valid_to_time):
                self._log_security_event('scan_time_restricted', ip_address, device_id, user_agent)
                raise UserError(_("QR code non valide à cette heure"))
        
        # Vérifier les dispositifs autorisés
        if self.allowed_devices and device_id:
            device = self.env['edu.attendance.device'].browse(device_id)
            if device not in self.allowed_devices:
                self._log_security_event('scan_device_not_allowed', ip_address, device_id, user_agent)
                raise UserError(_("Dispositif non autorisé"))
        
        # Vérifier les IPs autorisées
        if self.ip_whitelist and ip_address:
            allowed_ips = [ip.strip() for ip in self.ip_whitelist.split('\n') if ip.strip()]
            if allowed_ips and ip_address not in allowed_ips:
                self._log_security_event('scan_ip_not_allowed', ip_address, device_id, user_agent)
                raise UserError(_("Adresse IP non autorisée"))
        
        # Valide !
        self.success_scan_count += 1
        self.current_uses += 1
        
        # Marquer comme inactif si usage unique
        if self.is_single_use:
            self.active = False
        
        self._log_security_event('scan_success', ip_address, device_id, user_agent)
        
        return True
    
    def _log_security_event(self, event_type, ip_address=None, device_id=None, user_agent=None):
        """Enregistre un événement de sécurité"""
        self.env['edu.qr.code.log'].create({
            'qr_code_id': self.id,
            'event_type': event_type,
            'ip_address': ip_address,
            'device_id': device_id,
            'user_agent': user_agent,
            'user_id': self.env.user.id,
            'timestamp': fields.Datetime.now(),
        })
    
    # Actions
    def action_activate(self):
        """Active le QR code"""
        self.write({'active': True})
    
    def action_deactivate(self):
        """Désactive le QR code"""
        self.write({'active': False})
    
    def action_reset_usage(self):
        """Remet à zéro les compteurs d'usage"""
        self.write({
            'current_uses': 0,
            'scan_count': 0,
            'success_scan_count': 0,
            'active': True
        })
    
    def action_view_logs(self):
        """Affiche les logs de sécurité"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Logs QR Code - %s') % self.name,
            'res_model': 'edu.qr.code.log',
            'view_mode': 'tree,form',
            'domain': [('qr_code_id', '=', self.id)],
        }
    
    def action_download_qr(self):
        """Télécharge l'image du QR code"""
        self.ensure_one()
        if not self.qr_image:
            raise UserError(_("Aucune image de QR code disponible"))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/qr_image/{self.qr_image_filename}',
            'target': 'new',
        }
    
    def action_print_qr(self):
        """Imprime le QR code"""
        self.ensure_one()
        return self.env.ref('edu_attendance_smart.action_report_qr_code').report_action(self)
    
    # Méthodes statiques
    @api.model
    def scan_qr_code(self, content, device_id=None, ip_address=None, user_agent=None):
        """Traite un scan de QR code"""
        try:
            # Parser le contenu
            parts = content.split(':')
            if len(parts) < 3:
                raise UserError(_("Format de QR code invalide"))
            
            qr_type, record_id, token = parts[0], int(parts[1]), parts[2]
            
            # Trouver le QR code correspondant
            if qr_type in ['student', 'faculty', 'session', 'device', 'location']:
                qr_code = self.search([
                    ('qr_type', '=', qr_type),
                    ('qr_token', '=', token),
                    ('content', '=', content)
                ], limit=1)
            else:
                qr_code = self.search([
                    ('id', '=', record_id),
                    ('qr_token', '=', token)
                ], limit=1)
            
            if not qr_code:
                raise UserError(_("QR code non trouvé ou invalide"))
            
            # Valider le scan
            qr_code.validate_scan(device_id, ip_address, user_agent)
            
            # Retourner les informations
            return {
                'success': True,
                'qr_code_id': qr_code.id,
                'qr_type': qr_code.qr_type,
                'record_id': record_id,
                'message': _("QR code scanné avec succès")
            }
            
        except Exception as e:
            _logger.error(f"Erreur scan QR code: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': _("Erreur lors du scan du QR code")
            }
    
    @api.model
    def generate_student_qr(self, student_id):
        """Génère un QR code personnel pour un élève"""
        student = self.env['op.student'].browse(student_id)
        if not student.exists():
            raise UserError(_("Élève non trouvé"))
        
        # Vérifier s'il existe déjà un QR code actif
        existing = self.search([
            ('qr_type', '=', 'student'),
            ('student_id', '=', student_id),
            ('active', '=', True)
        ], limit=1)
        
        if existing:
            return existing
        
        # Créer un nouveau QR code
        qr_code = self.create({
            'name': f"QR {student.name}",
            'qr_type': 'student',
            'student_id': student_id,
            'content': f"student:{student_id}:{self._generate_token()}",
            'active': True,
        })
        
        qr_code._update_content()
        return qr_code
    
    @api.model
    def generate_session_qr(self, session_id):
        """Génère un QR code pour une session"""
        session = self.env['edu.attendance.session'].browse(session_id)
        if not session.exists():
            raise UserError(_("Session non trouvée"))
        
        # Créer le QR code avec expiration automatique
        qr_code = self.create({
            'name': f"QR Session {session.name}",
            'qr_type': 'session',
            'session_id': session_id,
            'content': f"session:{session_id}:{self._generate_token()}",
            'expiry_date': session.end_datetime,
            'active': True,
            'is_single_use': False,
        })
        
        qr_code._update_content()
        return qr_code
    
    # Contraintes
    @api.constrains('qr_type', 'student_id', 'faculty_id', 'session_id', 'device_id')
    def _check_qr_relations(self):
        """Vérifie la cohérence des relations selon le type"""
        for record in self:
            if record.qr_type == 'student' and not record.student_id:
                raise ValidationError(_("Un QR code étudiant doit être lié à un étudiant"))
            elif record.qr_type == 'faculty' and not record.faculty_id:
                raise ValidationError(_("Un QR code enseignant doit être lié à un enseignant"))
            elif record.qr_type == 'session' and not record.session_id:
                raise ValidationError(_("Un QR code session doit être lié à une session"))
            elif record.qr_type == 'device' and not record.device_id:
                raise ValidationError(_("Un QR code dispositif doit être lié à un dispositif"))
    
    @api.constrains('valid_from_time', 'valid_to_time')
    def _check_time_restrictions(self):
        """Vérifie les restrictions horaires"""
        for record in self:
            if record.time_restrictions:
                if not (0 <= record.valid_from_time <= 24):
                    raise ValidationError(_("L'heure de début doit être entre 0 et 24"))
                if not (0 <= record.valid_to_time <= 24):
                    raise ValidationError(_("L'heure de fin doit être entre 0 et 24"))
                if record.valid_from_time >= record.valid_to_time:
                    raise ValidationError(_("L'heure de début doit être antérieure à l'heure de fin"))
    
    @api.model
    def create(self, vals):
        """Surcharge pour générer le contenu automatiquement"""
        record = super().create(vals)
        if not record.content or record.content == vals.get('content', ''):
            record._update_content()
        return record


class EduQRCodeLog(models.Model):
    """Log des événements de sécurité des QR codes"""
    _name = 'edu.qr.code.log'
    _description = 'Log QR Code'
    _order = 'timestamp desc'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Nom',
        compute='_compute_display_name',
        store=True
    )
    
    qr_code_id = fields.Many2one(
        'edu.qr.code',
        string='QR Code',
        required=True,
        ondelete='cascade'
    )
    
    event_type = fields.Selection([
        ('scan_success', 'Scan réussi'),
        ('scan_expired', 'Scan QR expiré'),
        ('scan_inactive', 'Scan QR inactif'),
        ('scan_time_restricted', 'Scan hors horaires'),
        ('scan_device_not_allowed', 'Dispositif non autorisé'),
        ('scan_ip_not_allowed', 'IP non autorisée'),
        ('token_regenerated', 'Token régénéré'),
        ('qr_regenerated', 'QR régénéré'),
        ('qr_activated', 'QR activé'),
        ('qr_deactivated', 'QR désactivé'),
        ('usage_reset', 'Usage remis à zéro')
    ], string='Type d\'événement', required=True)
    
    timestamp = fields.Datetime(
        string='Horodatage',
        required=True,
        default=fields.Datetime.now
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Utilisateur',
        help="Utilisateur qui a déclenché l'événement"
    )
    
    ip_address = fields.Char(
        string='Adresse IP',
        help="Adresse IP de la requête"
    )
    
    device_id = fields.Many2one(
        'edu.attendance.device',
        string='Dispositif',
        help="Dispositif utilisé"
    )
    
    user_agent = fields.Text(
        string='User Agent',
        help="Informations sur le navigateur/app"
    )
    
    details = fields.Text(
        string='Détails',
        help="Détails supplémentaires de l'événement"
    )
    
    @api.depends('event_type', 'timestamp', 'qr_code_id')
    def _compute_display_name(self):
        """Calcule le nom d'affichage"""
        for record in self:
            event_labels = dict(record._fields['event_type'].selection)
            event_label = event_labels.get(record.event_type, record.event_type)
            
            if record.timestamp:
                date_str = record.timestamp.strftime('%d/%m/%Y %H:%M')
                record.display_name = f"{event_label} - {date_str}"
            else:
                record.display_name = event_label
