# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EduMessageTemplate(models.Model):
    _name = 'edu.message.template'
    _description = 'Template de message'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char('Nom du template', required=True, tracking=True)
    code = fields.Char('Code', required=True, help="Code unique pour identifier le template")
    description = fields.Text('Description')
    
    # Type de template
    template_type = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Notification Push'),
        ('chat', 'Message Chat'),
        ('announcement', 'Annonce'),
    ], string='Type', required=True, default='email')
    
    # Contenu du template
    subject = fields.Char('Sujet', help="Sujet du message (pour email et notifications)")
    body_html = fields.Html('Corps HTML', help="Corps du message en HTML")
    body_text = fields.Text('Corps texte', help="Corps du message en texte simple")
    
    # Variables disponibles
    available_variables = fields.Text('Variables disponibles', 
                                     help="Liste des variables disponibles dans ce template")
    
    # Configuration
    active = fields.Boolean('Actif', default=True)
    is_default = fields.Boolean('Template par défaut', default=False)
    
    # Catégorie
    category_id = fields.Many2one('edu.message.template.category', 'Catégorie')
    
    # Langue
    language = fields.Selection([
        ('fr_FR', 'Français'),
        ('en_US', 'Anglais'),
        ('es_ES', 'Espagnol'),
        ('ar_001', 'Arabe'),
    ], string='Langue', default='fr_FR')
    
    # Statistiques d'utilisation
    usage_count = fields.Integer('Nombre d\'utilisations', default=0)
    last_used = fields.Datetime('Dernière utilisation')
    
    # Pièces jointes par défaut
    attachment_ids = fields.Many2many('ir.attachment', 'template_attachment_rel',
                                     'template_id', 'attachment_id',
                                     string='Pièces jointes par défaut')
    
    @api.model
    def create(self, vals):
        """S'assurer que le code est unique"""
        if vals.get('code'):
            existing = self.search([('code', '=', vals['code'])])
            if existing:
                vals['code'] = f"{vals['code']}_{len(existing) + 1}"
        return super().create(vals)
    
    def use_template(self, context_vars=None):
        """Utiliser le template et remplacer les variables"""
        self.ensure_one()
        context_vars = context_vars or {}
        
        # Remplacer les variables dans le sujet et le corps
        subject = self._replace_variables(self.subject or '', context_vars)
        body_html = self._replace_variables(self.body_html or '', context_vars)
        body_text = self._replace_variables(self.body_text or '', context_vars)
        
        # Mettre à jour les statistiques
        self.write({
            'usage_count': self.usage_count + 1,
            'last_used': fields.Datetime.now()
        })
        
        return {
            'subject': subject,
            'body_html': body_html,
            'body_text': body_text,
            'attachment_ids': self.attachment_ids.ids,
        }
    
    def _replace_variables(self, text, context_vars):
        """Remplacer les variables dans le texte"""
        if not text:
            return text
            
        # Variables de base toujours disponibles
        default_vars = {
            'company_name': self.env.company.name,
            'current_date': fields.Date.today().strftime('%d/%m/%Y'),
            'current_time': fields.Datetime.now().strftime('%H:%M'),
        }
        
        # Fusionner avec les variables du contexte
        all_vars = {**default_vars, **context_vars}
        
        # Remplacer les variables
        for var_name, var_value in all_vars.items():
            placeholder = f"{{{{ {var_name} }}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(var_value))
        
        return text


class EduMessageTemplateCategory(models.Model):
    _name = 'edu.message.template.category'
    _description = 'Catégorie de template de message'
    
    name = fields.Char('Nom', required=True)
    description = fields.Text('Description')
    color = fields.Integer('Couleur', default=1)
    active = fields.Boolean('Actif', default=True)
    
    template_ids = fields.One2many('edu.message.template', 'category_id', 
                                  'Templates')
