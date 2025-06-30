# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StudentDocumentType(models.Model):
    _name = 'student.document.type'
    _description = 'Type de Document Élève'
    _order = 'sequence, name'
    
    name = fields.Char('Nom', required=True, translate=True)
    code = fields.Char('Code', required=True)
    category = fields.Selection([
        ('identity', 'Identité'),
        ('academic', 'Académique'),
        ('medical', 'Médical'),
        ('administrative', 'Administratif')
    ], string='Catégorie', required=True)
    is_mandatory = fields.Boolean('Obligatoire', default=False)
    requires_validation = fields.Boolean('Nécessite Validation', default=False)
    allowed_file_types = fields.Char('Types de Fichiers Autorisés')
    icon = fields.Char('Classe Icône')
    sequence = fields.Integer('Séquence', default=10)
    active = fields.Boolean('Actif', default=True)
    has_expiry = fields.Boolean('A une Date d\'Expiration', default=False)
    default_validity_days = fields.Integer('Jours de Validité par Défaut', default=365)

class StudentDocument(models.Model):
    """Documents élève"""
    _name = 'student.document'
    _description = 'Document Élève'
    
    student_id = fields.Many2one('op.student', string='Élève', required=True)
    document_type_id = fields.Many2one('student.document.type', string='Type de Document')
    name = fields.Char('Nom', required=True)
    file_data = fields.Binary('Fichier')
    date_created = fields.Date('Date de Création', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('under_review', 'En Révision'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté')
    ], string='État', default='draft')
    is_validated = fields.Boolean('Validé', compute='_compute_is_validated', store=True)
    
    @api.depends('state')
    def _compute_is_validated(self):
        for doc in self:
            doc.is_validated = doc.state == 'approved'

class DocumentHistory(models.Model):
    """Historique des actions sur les documents"""
    _name = 'document.history'
    _description = 'Historique Document'
    _order = 'date desc'
    
    document_id = fields.Many2one('student.document', string='Document', required=True)
    action = fields.Selection([
        ('created', 'Créé'),
        ('updated', 'Modifié'),
        ('submitted', 'Soumis'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté')
    ], string='Action', required=True)
    date = fields.Datetime('Date', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)
    notes = fields.Text('Notes')