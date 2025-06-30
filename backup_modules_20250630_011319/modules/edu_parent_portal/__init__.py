# -*- coding: utf-8 -*-

from . import models
from . import controllers
from . import wizard


def post_init_hook(env):
    """Hook appelé après l'installation du module"""
    import logging
    _logger = logging.getLogger(__name__)
    
    try:
        # env est déjà fourni par Odoo 17.0
        
        # Créer la configuration par défaut du portail
        config = env['edu.parent.portal.config'].search([], limit=1)
        if not config:
            env['edu.parent.portal.config'].create({
                'name': 'Configuration portail par défaut',
                'active': True,
                'enable_mobile_app': True,
                'enable_notifications': True,
                'enable_chat': True,
                'enable_payments': True,
                'enable_appointments': True,
                'theme_color': 'blue',
                'show_grades': True,
                'show_attendance': True,
                'show_homework': True,
                'show_schedule': True,
                'auto_refresh_interval': 300,  # 5 minutes
            })
        
        # Créer les menus du portail par défaut
        portal_menus = [
            ('dashboard', 'Tableau de bord', 'fa-dashboard', 1, True),
            ('students', 'Mes enfants', 'fa-users', 2, True),
            ('grades', 'Notes & Évaluations', 'fa-star', 3, True),
            ('attendance', 'Présences', 'fa-check-circle', 4, True),
            ('homework', 'Devoirs', 'fa-book', 5, True),
            ('schedule', 'Planning', 'fa-calendar', 6, True),
            ('messages', 'Messages', 'fa-envelope', 7, True),
            ('documents', 'Documents', 'fa-file', 8, True),
            ('payments', 'Paiements', 'fa-credit-card', 9, True),
            ('appointments', 'Rendez-vous', 'fa-clock-o', 10, True),
            ('profile', 'Mon profil', 'fa-user', 11, True),
        ]
        
        for code, name, icon, sequence, visible in portal_menus:
            existing = env['edu.portal.menu'].search([('code', '=', code)])
            if not existing:
                env['edu.portal.menu'].create({
                    'name': name,
                    'code': code,
                    'icon': icon,
                    'sequence': sequence,
                    'visible': visible,
                    'active': True,
                })
        
        # Créer les préférences de notification par défaut
        notification_types = [
            ('absence', 'Absences', True, True, False),
            ('grade', 'Nouvelles notes', True, True, True),
            ('homework', 'Devoirs', True, False, True),
            ('announcement', 'Annonces', True, False, True),
            ('meeting', 'Réunions', True, True, False),
            ('payment', 'Paiements', True, True, False),
            ('document', 'Nouveaux documents', False, True, True),
        ]
        
        for code, name, email, sms, push in notification_types:
            existing = env['edu.notification.preference.template'].search([('code', '=', code)])
            if not existing:
                env['edu.notification.preference.template'].create({
                    'name': name,
                    'code': code,
                    'email_enabled': email,
                    'sms_enabled': sms,
                    'push_enabled': push,
                    'active': True,
                })
        
        # Activer les utilisateurs portail pour tous les parents
        parents = env['res.partner'].search([
            ('is_parent', '=', True),
            ('user_ids', '=', False)
        ])
        
        for parent in parents:
            if parent.email and '@' in parent.email:
                try:
                    # Créer un utilisateur portail
                    user_vals = {
                        'name': parent.name,
                        'login': parent.email,
                        'email': parent.email,
                        'partner_id': parent.id,
                        'groups_id': [(6, 0, [env.ref('base.group_portal').id])],
                        'active': True,
                    }
                    user = env['res.users'].create(user_vals)
                    
                    # Créer les préférences de notification
                    for template in env['edu.notification.preference.template'].search([]):
                        env['edu.notification.preference'].create({
                            'user_id': user.id,
                            'notification_type': template.code,
                            'email_enabled': template.email_enabled,
                            'sms_enabled': template.sms_enabled,
                            'push_enabled': template.push_enabled,
                        })
                    
                except Exception as e:
                    _logger.warning(f"Impossible de créer l'utilisateur portail pour {parent.name}: {e}")
        
        _logger.info("Module edu_parent_portal initialisé avec succès")
        
    except Exception as e:
        _logger.error(f"Erreur lors de l'initialisation du module: {e}")
