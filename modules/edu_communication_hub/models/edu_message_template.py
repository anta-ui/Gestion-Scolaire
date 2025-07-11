# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduMessageTemplate(models.Model):
    """Templates de messages"""
    _name = 'edu.message.template'
    _description = 'Template de message'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du modèle',
        required=True,
        help="Nom identifiant du modèle de message"
    )
    
    description = fields.Text(
        string='Description',
        help="Description détaillée du template"
    )
    
    code = fields.Char(
        string='Code',
        help="Code unique du template"
    )
    
    template_type = fields.Selection([
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('general', 'Général')
    ], string='Type de template', required=True, default='general')
    
    category = fields.Selection([
        ('absence', 'Absence'),
        ('grade', 'Note'),
        ('announcement', 'Annonce'),
        ('reminder', 'Rappel'),
        ('meeting', 'Réunion'),
        ('event', 'Événement'),
        ('homework', 'Devoir'),
        ('custom', 'Personnalisé')
    ], string='Catégorie', default='custom')
    
    category_id = fields.Many2one(
        'edu.message.template.category',
        string='Catégorie de template',
        help="Catégorie du template"
    )
    
    subject = fields.Char(
        string='Sujet',
        help="Sujet du message"
    )
    
    subject_template = fields.Char(
        string='Sujet (template)',
        help="Template pour le sujet du message"
    )
    
    body_text = fields.Text(
        string='Corps du message',
        help="Contenu du message"
    )
    
    body_html = fields.Html(
        string='Corps du message HTML',
        help="Contenu du message en HTML pour les emails"
    )
    
    content_template = fields.Text(
        string='Contenu (template)',
        help="Template pour le contenu du message"
    )
    
    content_html_template = fields.Html(
        string='Contenu HTML (template)',
        help="Template HTML pour les emails"
    )
    
    is_default = fields.Boolean(
        string='Template par défaut',
        default=False,
        help="Indique si ce template est utilisé par défaut"
    )
    
    usage_count = fields.Integer(
        string='Nombre d\'utilisations',
        default=0,
        readonly=True,
        help="Nombre de fois que ce template a été utilisé"
    )
    
    last_used = fields.Datetime(
        string='Dernière utilisation',
        readonly=True,
        help="Date et heure de la dernière utilisation"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    language = fields.Selection([
        ('fr_FR', 'Français'),
        ('en_US', 'Anglais'),
        ('ar_SA', 'Arabe'),
        ('es_ES', 'Espagnol')
    ], string='Langue', default='fr_FR')
    
    # Variables disponibles
    available_variables = fields.Text(
        string='Variables disponibles',
        help="Liste des variables utilisables dans ce template",
        default="""Variables disponibles:
{student_name} - Nom de l'étudiant
{parent_name} - Nom du parent
{class_name} - Nom de la classe
{teacher_name} - Nom de l'enseignant
{date} - Date
{school_name} - Nom de l'école
{message} - Message personnalisé"""
    )
    
    # Pièces jointes
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Pièces jointes',
        help="Fichiers attachés à ce template"
    )
    
    def preview_template(self, context_data=None):
        """Prévisualiser le template avec des données d'exemple"""
        if not context_data:
            context_data = {
                'student_name': 'Ahmed BENALI',
                'parent_name': 'Fatima BENALI',
                'class_name': '5ème A',
                'teacher_name': 'M. HASSAN',
                'date': fields.Date.today().strftime('%d/%m/%Y'),
                'school_name': 'École Extraordinaire',
                'message': 'Message d\'exemple'
            }
        
        try:
            subject = self.subject_template.format(**context_data) if self.subject_template else ''
            content = self.content_template.format(**context_data)
            return {
                'subject': subject,
                'content': content
            }
        except KeyError as e:
            raise ValidationError(f"Variable manquante dans le template: {e}")


class EduNotificationType(models.Model):
    """Types de notifications"""
    _name = 'edu.notification.type'
    _description = 'Type de notification'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom',
        required=True
    )
    
    code = fields.Char(
        string='Code',
        required=True
    )
    
    priority = fields.Selection([
        ('low', 'Faible'),
        ('normal', 'Normal'),
        ('high', 'Élevé'),
        ('urgent', 'Urgent')
    ], string='Priorité', default='normal')
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    use_sms = fields.Boolean(
        string='Utiliser SMS',
        default=False
    )
    
    use_email = fields.Boolean(
        string='Utiliser Email',
        default=True
    )
    
    use_push = fields.Boolean(
        string='Utiliser Push',
        default=False
    )
    
    template_id = fields.Many2one(
        'edu.message.template',
        string='Template par défaut'
    )
    
    description = fields.Text(
        string='Description'
    )
    
    @api.constrains('code')
    def _check_unique_code(self):
        """Vérifier l'unicité du code"""
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(f"Le code '{record.code}' existe déjà")
