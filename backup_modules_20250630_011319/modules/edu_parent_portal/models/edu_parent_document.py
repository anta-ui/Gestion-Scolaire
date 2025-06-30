# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EduParentDocument(models.Model):
    """Documents accessibles aux parents"""
    _name = 'edu.parent.document'
    _description = 'Document parent'
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du document',
        required=True,
        help="Nom du document"
    )
    
    description = fields.Text(
        string='Description',
        help="Description du document"
    )
    
    document_type = fields.Selection([
        ('bulletin', 'Bulletin de notes'),
        ('certificate', 'Certificat'),
        ('report', 'Rapport'),
        ('authorization', 'Autorisation'),
        ('invoice', 'Facture'),
        ('receipt', 'Reçu'),
        ('medical', 'Document médical'),
        ('transport', 'Transport'),
        ('other', 'Autre')
    ], string='Type de document', required=True, help="Type de document")
    
    category = fields.Selection([
        ('academic', 'Académique'),
        ('administrative', 'Administratif'),
        ('financial', 'Financier'),
        ('medical', 'Médical'),
        ('disciplinary', 'Disciplinaire'),
        ('transport', 'Transport'),
        ('other', 'Autre')
    ], string='Catégorie', required=True, help="Catégorie du document")
    
    student_id = fields.Many2one(
        'op.student',
        string='Élève',
        required=True,
        help="Élève concerné"
    )
    
    parent_ids = fields.Many2many(
        'res.partner',
        string='Parents autorisés',
        domain=[('is_parent', '=', True)],
        help="Parents autorisés à voir ce document"
    )
    
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Fichier',
        required=True,
        help="Fichier du document"
    )
    
    file_size = fields.Integer(
        string='Taille du fichier',
        related='attachment_id.file_size',
        help="Taille du fichier en octets"
    )
    
    mimetype = fields.Char(
        string='Type MIME',
        related='attachment_id.mimetype',
        help="Type MIME du fichier"
    )
    
    # Statut et visibilité
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé')
    ], string='État', default='draft', help="État du document")
    
    is_public = fields.Boolean(
        string='Public',
        default=False,
        help="Document visible par tous les parents de l'élève"
    )
    
    is_downloadable = fields.Boolean(
        string='Téléchargeable',
        default=True,
        help="Document téléchargeable"
    )
    
    is_printable = fields.Boolean(
        string='Imprimable',
        default=True,
        help="Document imprimable"
    )
    
    # Dates importantes
    valid_from = fields.Date(
        string='Valide à partir du',
        help="Date de début de validité"
    )
    
    valid_until = fields.Date(
        string='Valide jusqu\'au',
        help="Date de fin de validité"
    )
    
    publish_date = fields.Datetime(
        string='Date de publication',
        help="Date de publication du document"
    )
    
    # Signature et validation
    is_signed = fields.Boolean(
        string='Signé',
        default=False,
        help="Document signé électroniquement"
    )
    
    signature_date = fields.Datetime(
        string='Date de signature',
        help="Date de signature"
    )
    
    signed_by = fields.Many2one(
        'res.users',
        string='Signé par',
        help="Utilisateur ayant signé"
    )
    
    # Statistiques d'accès
    view_count = fields.Integer(
        string='Nombre de vues',
        default=0,
        help="Nombre de consultations"
    )
    
    download_count = fields.Integer(
        string='Nombre de téléchargements',
        default=0,
        help="Nombre de téléchargements"
    )
    
    last_viewed = fields.Datetime(
        string='Dernière consultation',
        help="Date de dernière consultation"
    )
    
    # Métadonnées
    created_by = fields.Many2one(
        'res.users',
        string='Créé par',
        default=lambda self: self.env.user,
        help="Utilisateur créateur"
    )
    
    academic_year_id = fields.Many2one(
        'op.academic.year',
        string='Année académique',
        help="Année académique concernée"
    )
    
    course_id = fields.Many2one(
        'op.course',
        string='Cours',
        help="Cours concerné"
    )
    
    def action_publish(self):
        """Publier le document"""
        self.write({
            'state': 'published',
            'publish_date': fields.Datetime.now()
        })
        self._send_publication_notification()
    
    def action_archive(self):
        """Archiver le document"""
        self.write({'state': 'archived'})
    
    def action_download(self):
        """Télécharger le document"""
        self.write({
            'download_count': self.download_count + 1,
            'last_viewed': fields.Datetime.now()
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}?download=true',
            'target': 'self',
        }
    
    def action_view(self):
        """Voir le document"""
        self.write({
            'view_count': self.view_count + 1,
            'last_viewed': fields.Datetime.now()
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}',
            'target': 'new',
        }
    
    def _send_publication_notification(self):
        """Envoyer notification de publication"""
        # Créer notification pour les parents
        notification_obj = self.env['edu.parent.notification']
        for parent in self.parent_ids:
            if parent.user_ids:
                notification_obj.create({
                    'title': f'Nouveau document: {self.name}',
                    'message': f'Un nouveau document "{self.name}" est disponible pour {self.student_id.name}.',
                    'category': 'document',
                    'recipient_ids': [(6, 0, parent.user_ids.ids)],
                    'student_ids': [(6, 0, [self.student_id.id])],
                    'state': 'sent',
                    'send_date': fields.Datetime.now()
                })


class EduDocumentRequest(models.Model):
    """Demande de document par les parents"""
    _name = 'edu.document.request'
    _description = 'Demande de document'
    _order = 'create_date desc'
    _rec_name = 'document_type'

    document_type = fields.Selection([
        ('bulletin', 'Bulletin de notes'),
        ('certificate', 'Certificat de scolarité'),
        ('transcript', 'Relevé de notes'),
        ('attendance', 'Certificat d\'assiduité'),
        ('medical', 'Certificat médical'),
        ('authorization', 'Autorisation'),
        ('other', 'Autre')
    ], string='Type de document', required=True, help="Type de document demandé")
    
    description = fields.Text(
        string='Description',
        help="Description de la demande"
    )
    
    student_id = fields.Many2one(
        'op.student',
        string='Élève',
        required=True,
        help="Élève concerné"
    )
    
    parent_id = fields.Many2one(
        'res.partner',
        string='Parent demandeur',
        required=True,
        domain=[('is_parent', '=', True)],
        help="Parent demandeur"
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('processing', 'En traitement'),
        ('ready', 'Prête'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', help="État de la demande", tracking=True)
    
    urgency = fields.Selection([
        ('normal', 'Normale'),
        ('urgent', 'Urgente')
    ], string='Urgence', default='normal', help="Niveau d'urgence")
    
    delivery_method = fields.Selection([
        ('portal', 'Portail en ligne'),
        ('email', 'Par email'),
        ('pickup', 'À récupérer'),
        ('mail', 'Par courrier')
    ], string='Mode de livraison', default='portal', help="Mode de livraison souhaité")
    
    expected_date = fields.Date(
        string='Date souhaitée',
        help="Date souhaitée de livraison"
    )
    
    processed_by = fields.Many2one(
        'res.users',
        string='Traité par',
        help="Utilisateur qui traite la demande"
    )
    
    notes = fields.Text(
        string='Notes',
        help="Notes sur la demande"
    )
    
    def action_submit(self):
        """Soumettre la demande"""
        self.write({'state': 'submitted'})
        self._send_submission_notification()
    
    def action_process(self):
        """Commencer le traitement"""
        self.write({
            'state': 'processing',
            'processed_by': self.env.user.id
        })
    
    def action_ready(self):
        """Marquer comme prête"""
        self.write({'state': 'ready'})
        self._send_ready_notification()
    
    def action_deliver(self):
        """Marquer comme livrée"""
        self.write({'state': 'delivered'})
    
    def action_cancel(self):
        """Annuler la demande"""
        self.write({'state': 'cancelled'})
    
    def _send_submission_notification(self):
        """Notification de soumission"""
        pass
    
    def _send_ready_notification(self):
        """Notification de disponibilité"""
        pass
