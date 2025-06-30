# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import datetime

_logger = logging.getLogger(__name__)


class EduParentPortalConfig(models.Model):
    """Configuration globale du portail parents"""
    _name = 'edu.parent.portal.config'
    _description = 'Configuration Portail Parents'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom de la configuration',
        required=True,
        help="Nom de la configuration"
    )
    
    active = fields.Boolean(
        string='Configuration active',
        default=True,
        help="Configuration actuellement utilisée"
    )
    
    # Apparence et thème
    theme_color = fields.Selection([
        ('blue', 'Bleu'),
        ('green', 'Vert'),
        ('orange', 'Orange'),
        ('purple', 'Violet'),
        ('red', 'Rouge'),
        ('dark', 'Sombre'),
        ('custom', 'Personnalisé')
    ], string='Couleur du thème', default='blue', help="Couleur principale du portail")
    
    custom_primary_color = fields.Char(
        string='Couleur primaire personnalisée',
        help="Code couleur hexadécimal (ex: #007bff)"
    )
    
    custom_secondary_color = fields.Char(
        string='Couleur secondaire personnalisée',
        help="Code couleur hexadécimal (ex: #6c757d)"
    )
    
    logo = fields.Binary(
        string='Logo du portail',
        help="Logo affiché dans le portail"
    )
    
    banner_image = fields.Binary(
        string='Image de bannière',
        help="Image de bannière du portail"
    )
    
    favicon = fields.Binary(
        string='Favicon',
        help="Icône du site web"
    )
    
    # Fonctionnalités activées
    enable_mobile_app = fields.Boolean(
        string='Application mobile PWA',
        default=True,
        help="Activer l'application mobile progressive"
    )
    
    enable_notifications = fields.Boolean(
        string='Notifications push',
        default=True,
        help="Activer les notifications push"
    )
    
    enable_chat = fields.Boolean(
        string='Chat en temps réel',
        default=True,
        help="Activer le chat avec les enseignants"
    )
    
    enable_payments = fields.Boolean(
        string='Paiements en ligne',
        default=True,
        help="Activer les paiements en ligne"
    )
    
    enable_appointments = fields.Boolean(
        string='Prise de rendez-vous',
        default=True,
        help="Activer la prise de rendez-vous"
    )
    
    enable_document_requests = fields.Boolean(
        string='Demandes de documents',
        default=True,
        help="Permettre les demandes de documents"
    )
    
    enable_multi_language = fields.Boolean(
        string='Multi-langues',
        default=True,
        help="Activer le support multi-langues"
    )
    
    # Modules visibles
    show_grades = fields.Boolean(
        string='Afficher les notes',
        default=True,
        help="Afficher la section notes et évaluations"
    )
    
    show_attendance = fields.Boolean(
        string='Afficher les présences',
        default=True,
        help="Afficher la section présences"
    )
    
    show_homework = fields.Boolean(
        string='Afficher les devoirs',
        default=True,
        help="Afficher la section devoirs"
    )
    
    show_schedule = fields.Boolean(
        string='Afficher le planning',
        default=True,
        help="Afficher l'emploi du temps"
    )
    
    show_disciplinary = fields.Boolean(
        string='Afficher le disciplinaire',
        default=False,
        help="Afficher les sanctions disciplinaires"
    )
    
    show_medical = fields.Boolean(
        string='Afficher le médical',
        default=True,
        help="Afficher les informations médicales"
    )
    
    show_transport = fields.Boolean(
        string='Afficher le transport',
        default=True,
        help="Afficher les informations de transport"
    )
    
    # Paramètres de sécurité
    require_2fa = fields.Boolean(
        string='Authentification 2FA obligatoire',
        default=False,
        help="Exiger l'authentification à deux facteurs"
    )
    
    session_timeout = fields.Integer(
        string='Délai de session (minutes)',
        default=60,
        help="Délai d'expiration de session en minutes"
    )
    
    max_login_attempts = fields.Integer(
        string='Tentatives de connexion max',
        default=5,
        help="Nombre maximum de tentatives de connexion"
    )
    
    lockout_duration = fields.Integer(
        string='Durée de blocage (minutes)',
        default=30,
        help="Durée de blocage après échec de connexion"
    )
    
    # Paramètres d'affichage
    items_per_page = fields.Integer(
        string='Éléments par page',
        default=20,
        help="Nombre d'éléments affichés par page"
    )
    
    auto_refresh_interval = fields.Integer(
        string='Intervalle de rafraîchissement (sec)',
        default=300,
        help="Intervalle de rafraîchissement automatique en secondes"
    )
    
    show_student_photos = fields.Boolean(
        string='Photos des élèves',
        default=True,
        help="Afficher les photos des élèves"
    )
    
    show_teacher_contacts = fields.Boolean(
        string='Contacts enseignants',
        default=True,
        help="Afficher les contacts des enseignants"
    )
    
    # Notifications et communications
    default_language = fields.Selection(
        '_get_languages',
        string='Langue par défaut',
        default='fr_FR',
        help="Langue par défaut du portail"
    )
    
    timezone = fields.Selection(
        '_get_timezone_list',
        string='Fuseau horaire',
        default='Africa/Dakar',
        help="Fuseau horaire par défaut"
    )
    
    email_notifications = fields.Boolean(
        string='Notifications email',
        default=True,
        help="Envoyer des notifications par email"
    )
    
    sms_notifications = fields.Boolean(
        string='Notifications SMS',
        default=True,
        help="Envoyer des notifications par SMS"
    )
    
    # Limitations et quotas
    max_children_per_parent = fields.Integer(
        string='Enfants max par parent',
        default=10,
        help="Nombre maximum d'enfants par compte parent"
    )
    
    max_file_upload_size = fields.Float(
        string='Taille max upload (MB)',
        default=10.0,
        help="Taille maximale des fichiers uploadés"
    )
    
    allowed_file_extensions = fields.Text(
        string='Extensions autorisées',
        default='pdf,doc,docx,jpg,jpeg,png,gif',
        help="Extensions de fichiers autorisées (séparées par des virgules)"
    )
    
    # Maintenance et disponibilité
    maintenance_mode = fields.Boolean(
        string='Mode maintenance',
        default=False,
        help="Activer le mode maintenance"
    )
    
    maintenance_message = fields.Html(
        string='Message de maintenance',
        default='<p>Le portail est temporairement indisponible pour maintenance.</p>',
        help="Message affiché pendant la maintenance"
    )
    
    available_hours_start = fields.Float(
        string='Heure de début',
        default=0.0,
        help="Heure de début de disponibilité (24h)"
    )
    
    available_hours_end = fields.Float(
        string='Heure de fin',
        default=24.0,
        help="Heure de fin de disponibilité (24h)"
    )
    
    # Analytics et rapports
    enable_analytics = fields.Boolean(
        string='Analytics activés',
        default=True,
        help="Activer le suivi analytique"
    )
    
    track_user_activity = fields.Boolean(
        string='Suivre l\'activité utilisateur',
        default=True,
        help="Enregistrer l'activité des utilisateurs"
    )
    
    generate_usage_reports = fields.Boolean(
        string='Rapports d\'usage',
        default=True,
        help="Générer des rapports d'utilisation"
    )
    
    # Statistiques (calculées)
    total_active_parents = fields.Integer(
        string='Parents actifs',
        compute='_compute_stats',
        help="Nombre de parents actifs"
    )
    
    total_portal_users = fields.Integer(
        string='Utilisateurs portail',
        compute='_compute_stats',
        help="Nombre total d'utilisateurs du portail"
    )
    
    avg_daily_visits = fields.Float(
        string='Visites quotidiennes moyennes',
        compute='_compute_stats',
        digits=(8, 2),
        help="Moyenne des visites quotidiennes"
    )
    
    # Calculs
    def _compute_stats(self):
        """Calcule les statistiques du portail"""
        for record in self:
            # Parents actifs (connectés dans les 30 derniers jours)
            thirty_days_ago = fields.Datetime.now() - datetime.timedelta(days=30)
            record.total_active_parents = self.env['res.users'].search_count([
                ('groups_id', 'in', [self.env.ref('base.group_portal').id]),
                ('login_date', '>=', thirty_days_ago),
                ('partner_id.is_parent', '=', True)
            ])
            
            # Total utilisateurs portail
            record.total_portal_users = self.env['res.users'].search_count([
                ('groups_id', 'in', [self.env.ref('base.group_portal').id]),
                ('partner_id.is_parent', '=', True)
            ])
            
            # Visites quotidiennes (simulation - à implémenter avec de vraies analytics)
            record.avg_daily_visits = record.total_active_parents * 2.5
    
    @api.model
    def _get_languages(self):
        """Retourne les langues disponibles"""
        return self.env['res.lang'].get_installed()
    
    @api.model
    def _get_timezone_list(self):
        """Retourne la liste des fuseaux horaires"""
        import pytz
        return [(tz, tz) for tz in sorted(pytz.common_timezones)]
    
    # Contraintes
    @api.constrains('session_timeout')
    def _check_session_timeout(self):
        """Vérifie le délai de session"""
        for record in self:
            if record.session_timeout < 5 or record.session_timeout > 480:
                raise ValidationError(_("Le délai de session doit être entre 5 et 480 minutes"))
    
    @api.constrains('max_login_attempts')
    def _check_max_login_attempts(self):
        """Vérifie le nombre de tentatives"""
        for record in self:
            if record.max_login_attempts < 3 or record.max_login_attempts > 20:
                raise ValidationError(_("Le nombre de tentatives doit être entre 3 et 20"))
    
    @api.constrains('available_hours_start', 'available_hours_end')
    def _check_available_hours(self):
        """Vérifie les heures de disponibilité"""
        for record in self:
            if record.available_hours_start >= record.available_hours_end:
                raise ValidationError(_("L'heure de début doit être antérieure à l'heure de fin"))
    
    @api.constrains('custom_primary_color', 'custom_secondary_color')
    def _check_color_format(self):
        """Vérifie le format des couleurs personnalisées"""
        import re
        color_pattern = r'^#[0-9A-Fa-f]{6}$'
        
        for record in self:
            if record.custom_primary_color and not re.match(color_pattern, record.custom_primary_color):
                raise ValidationError(_("Format de couleur primaire invalide. Utilisez #RRGGBB"))
            if record.custom_secondary_color and not re.match(color_pattern, record.custom_secondary_color):
                raise ValidationError(_("Format de couleur secondaire invalide. Utilisez #RRGGBB"))
    
    # Actions
    def action_enable_maintenance(self):
        """Active le mode maintenance"""
        self.maintenance_mode = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("Mode maintenance activé"),
                'type': 'warning',
            }
        }
    
    def action_disable_maintenance(self):
        """Désactive le mode maintenance"""
        self.maintenance_mode = False
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("Mode maintenance désactivé"),
                'type': 'success',
            }
        }
    
    def action_reset_all_sessions(self):
        """Déconnecte tous les utilisateurs du portail"""
        portal_users = self.env['res.users'].search([
            ('groups_id', 'in', [self.env.ref('base.group_portal').id]),
            ('partner_id.is_parent', '=', True)
        ])
        
        # Révoquer toutes les sessions (simulation)
        # Dans une vraie implémentation, il faudrait invalider les tokens de session
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("%d sessions utilisateurs réinitialisées") % len(portal_users),
                'type': 'info',
            }
        }
    
    def action_generate_test_data(self):
        """Génère des données de test pour le portail"""
        # Créer des parents de test si aucun n'existe
        if not self.env['res.partner'].search([('is_parent', '=', True)], limit=1):
            for i in range(5):
                parent = self.env['res.partner'].create({
                    'name': f'Parent Test {i+1}',
                    'email': f'parent{i+1}@test.com',
                    'phone': f'+221 77 123 456{i}',
                    'is_parent': True,
                    'is_company': False,
                })
                
                # Créer un utilisateur portail
                self.env['res.users'].create({
                    'name': parent.name,
                    'login': parent.email,
                    'email': parent.email,
                    'partner_id': parent.id,
                    'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
                })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("Données de test générées"),
                'type': 'success',
            }
        }
    
    # Méthodes utilitaires
    def is_portal_available(self):
        """Vérifie si le portail est disponible"""
        self.ensure_one()
        
        if self.maintenance_mode:
            return False
        
        # Vérifier les heures de disponibilité
        now = datetime.datetime.now()
        current_hour = now.hour + now.minute / 60.0
        
        return self.available_hours_start <= current_hour <= self.available_hours_end
    
    def get_theme_colors(self):
        """Retourne les couleurs du thème"""
        self.ensure_one()
        
        if self.theme_color == 'custom':
            return {
                'primary': self.custom_primary_color or '#007bff',
                'secondary': self.custom_secondary_color or '#6c757d'
            }
        
        # Couleurs prédéfinies
        colors = {
            'blue': {'primary': '#007bff', 'secondary': '#6c757d'},
            'green': {'primary': '#28a745', 'secondary': '#6c757d'},
            'orange': {'primary': '#fd7e14', 'secondary': '#6c757d'},
            'purple': {'primary': '#6f42c1', 'secondary': '#6c757d'},
            'red': {'primary': '#dc3545', 'secondary': '#6c757d'},
            'dark': {'primary': '#343a40', 'secondary': '#495057'},
        }
        
        return colors.get(self.theme_color, colors['blue'])
    
    def get_allowed_extensions(self):
        """Retourne la liste des extensions autorisées"""
        self.ensure_one()
        if self.allowed_file_extensions:
            return [ext.strip().lower() for ext in self.allowed_file_extensions.split(',')]
        return ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
    
    @api.model
    def get_active_config(self):
        """Retourne la configuration active"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            # Créer une configuration par défaut si aucune n'existe
            config = self.create({
                'name': 'Configuration par défaut',
                'active': True
            })
        return config
    
    def action_view_portal_users(self):
        """Action pour voir les utilisateurs du portail"""
        self.ensure_one()
        
        # Rechercher tous les partenaires qui sont des parents
        parent_partners = self.env['res.partner'].search([
            ('is_parent', '=', True),
            ('user_ids', '!=', False)
        ])
        
        return {
            'name': _('Utilisateurs du Portail Parents'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', parent_partners.ids)],
            'context': {
                'default_is_parent': True,
                'create': False,
            },
            'help': """
                <p class="o_view_nocontent_smiling_face">
                    Aucun utilisateur du portail parents trouvé
                </p>
                <p>
                    Les utilisateurs du portail parents sont automatiquement créés
                    lors de l'inscription des parents.
                </p>
            """
        }
    
    def action_sync_users(self):
        """Action pour synchroniser les utilisateurs du portail"""
        self.ensure_one()
        
        # Rechercher tous les parents sans compte utilisateur
        parents_without_users = self.env['res.partner'].search([
            ('is_parent', '=', True),
            ('user_ids', '=', False),
            ('email', '!=', False)
        ])
        
        created_users = 0
        for parent in parents_without_users:
            try:
                # Créer un utilisateur pour ce parent
                user_vals = {
                    'name': parent.name,
                    'login': parent.email,
                    'email': parent.email,
                    'partner_id': parent.id,
                    'groups_id': [(6, 0, [self.env.ref('edu_parent_portal.group_portal_parent').id])],
                    'active': True,
                }
                
                # Vérifier si l'email n'est pas déjà utilisé
                existing_user = self.env['res.users'].search([('login', '=', parent.email)], limit=1)
                if not existing_user:
                    self.env['res.users'].create(user_vals)
                    created_users += 1
                    
            except Exception as e:
                # Log l'erreur mais continue
                _logger.warning(f"Erreur lors de la création de l'utilisateur pour {parent.name}: {e}")
                continue
        
        # Recalculer les statistiques
        self._compute_stats()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Synchronisation terminée'),
                'message': _('%d nouveaux utilisateurs créés pour le portail parents.') % created_users,
                'type': 'success',
                'sticky': False,
            }
        }
