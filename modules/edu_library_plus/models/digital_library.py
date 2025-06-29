# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import mimetypes


class DigitalLibrary(models.Model):
    _name = 'digital.library'
    _description = 'Bibliothèque Numérique'
    _order = 'create_date desc'

    name = fields.Char(
        string='Titre du Document',
        required=True
    )
    
    book_id = fields.Many2one(
        'library.book',
        string='Livre Associé',
        required=True
    )
    
    file_data = fields.Binary(
        string='Fichier',
        attachment=True,
        required=True
    )
    
    file_name = fields.Char(
        string='Nom du Fichier Original'
    )
    
    file_size = fields.Integer(
        string='Taille du Fichier (bytes)',
        compute='_compute_file_size',
        store=True
    )
    
    file_type = fields.Selection([
        ('pdf', 'PDF'),
        ('epub', 'EPUB'),
        ('mobi', 'MOBI'),
        ('txt', 'Texte'),
        ('doc', 'Word Document'),
        ('docx', 'Word Document (DOCX)'),
        ('other', 'Autre')
    ], string='Type de Fichier', compute='_compute_file_type', store=True)
    
    mimetype = fields.Char(
        string='Type MIME',
        compute='_compute_mimetype',
        store=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    access_level = fields.Selection([
        ('public', 'Public'),
        ('members', 'Membres seulement'),
        ('restricted', 'Accès Restreint')
    ], string='Niveau d\'Accès', default='members')
    
    download_count = fields.Integer(
        string='Nombre de Téléchargements',
        default=0
    )
    
    is_downloadable = fields.Boolean(
        string='Téléchargeable',
        default=True
    )
    
    is_readable_online = fields.Boolean(
        string='Lecture en ligne',
        default=True
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    # Gestion des prêts numériques
    loan_ids = fields.One2many(
        'digital.loan',
        'digital_book_id',
        string='Prêts Numériques'
    )
    
    @api.depends('file_data')
    def _compute_file_size(self):
        for record in self:
            if record.file_data:
                # Approximation de la taille basée sur base64
                record.file_size = len(base64.b64decode(record.file_data))
            else:
                record.file_size = 0
    
    @api.depends('file_name')
    def _compute_file_type(self):
        for record in self:
            if record.file_name:
                extension = record.file_name.split('.')[-1].lower()
                if extension in ['pdf']:
                    record.file_type = 'pdf'
                elif extension in ['epub']:
                    record.file_type = 'epub'
                elif extension in ['mobi']:
                    record.file_type = 'mobi'
                elif extension in ['txt']:
                    record.file_type = 'txt'
                elif extension in ['doc']:
                    record.file_type = 'doc'
                elif extension in ['docx']:
                    record.file_type = 'docx'
                else:
                    record.file_type = 'other'
            else:
                record.file_type = 'other'
    
    @api.depends('file_name')
    def _compute_mimetype(self):
        for record in self:
            if record.file_name:
                mimetype, _ = mimetypes.guess_type(record.file_name)
                record.mimetype = mimetype or 'application/octet-stream'
            else:
                record.mimetype = 'application/octet-stream'
    
    def action_download(self):
        """Action pour télécharger le fichier"""
        self.download_count += 1
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.id}/file_data/{self.file_name}?download=true',
            'target': 'self',
        }
    
    def action_read_online(self):
        """Action pour lire en ligne"""
        if not self.is_readable_online:
            raise ValidationError(_("Ce fichier n'est pas disponible pour la lecture en ligne."))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.id}/file_data/{self.file_name}',
            'target': 'new',
        }
    
    @api.constrains('file_data')
    def _check_file_size(self):
        """Vérifier la taille du fichier"""
        max_size = 100 * 1024 * 1024  # 100 MB
        for record in self:
            if record.file_size > max_size:
                raise ValidationError(_("La taille du fichier ne peut pas dépasser 100 MB."))


class DigitalLoan(models.Model):
    _name = 'digital.loan'
    _description = 'Prêt Numérique'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau')
    )
    
    digital_book_id = fields.Many2one(
        'digital.library',
        string='Livre Numérique',
        required=True
    )
    
    member_id = fields.Many2one(
        'op.student',
        string='Étudiant',
        required=True
    )
    
    loan_date = fields.Datetime(
        string='Date de Prêt',
        default=fields.Datetime.now,
        required=True
    )
    
    expiry_date = fields.Datetime(
        string='Date d\'Expiration',
        required=True
    )
    
    access_token = fields.Char(
        string='Token d\'Accès',
        help='Token unique pour accéder au fichier'
    )
    
    state = fields.Selection([
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé')
    ], string='État', default='active', required=True)
    
    download_count = fields.Integer(
        string='Nombre de Téléchargements',
        default=0
    )
    
    max_downloads = fields.Integer(
        string='Téléchargements Maximum',
        default=3
    )
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nouveau')) == _('Nouveau'):
            vals['name'] = self.env['ir.sequence'].next_by_code('digital.loan') or _('Nouveau')
        
        # Générer un token d'accès unique
        import secrets
        vals['access_token'] = secrets.token_urlsafe(32)
        
        return super().create(vals)
    
    def action_download(self):
        """Télécharger le fichier numérique"""
        self.ensure_one()
        
        if self.state != 'active':
            raise UserError(_('Ce prêt n\'est plus actif.'))
        
        if self.expiry_date < fields.Datetime.now():
            self.state = 'expired'
            raise UserError(_('Ce prêt a expiré.'))
        
        if self.download_count >= self.max_downloads:
            raise UserError(_('Nombre maximum de téléchargements atteint.'))
        
        # Incrémenter le compteur
        self.download_count += 1
        
        # Retourner le fichier
        return {
            'type': 'ir.actions.act_url',
            'url': f'/digital_library/download/{self.access_token}',
            'target': 'new',
        }
