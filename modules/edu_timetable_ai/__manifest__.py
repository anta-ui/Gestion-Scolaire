# -*- coding: utf-8 -*-
{
    'name': 'École Extraordinaire - Emploi du Temps IA',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Gestion intelligente des emplois du temps avec IA',
    'description': """
        Système d'emploi du temps intelligent avec:
        ==========================================
        
        ✨ Fonctionnalités principales:
        - 🤖 Génération automatique avec IA
        - 🔧 Optimisation des conflits automatique
        - 📊 Gestion des contraintes avancées
        - 🎯 Planning dynamique et adaptatif
        - 🖱️ Interface drag & drop moderne
        - 🔔 Notifications temps réel
        - 📈 Rapports analytiques détaillés
        
        🏫 Gestion avancée:
        - Salles intelligentes avec capacités
        - Professeurs et disponibilités
        - Matières et programmes
        - Créneaux flexibles
        - Conflits automatiques
        
        📱 Interface moderne:
        - Vue calendrier interactive
        - Glisser-déposer intuitive
        - Responsive design
        - Notifications push
        - Export multi-formats
    """,
    'author': 'École Extraordinaire Dev Team',
    'website': 'https://ecole-extraordinaire.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
        'calendar',
        'resource',
        'hr',
        'openeducat_core',
        'openeducat_timetable',
        'edu_student_enhanced',
    ],
    'data': [
        # Sécurité
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Données de base
        'data/data.xml',
        
        # Vues
        'views/timetable_views.xml',
        'views/schedule_views.xml',
        'views/room_views.xml',
        'views/constraint_views.xml',
        'views/templates.xml',
        
        # Wizards
        'wizard/timetable_wizard.xml',
        
        # Rapports
        'reports/timetable_reports.xml',
        
        # Menu
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'edu_timetable_ai/static/src/js/timetable_widget.js',
            'edu_timetable_ai/static/src/js/drag_drop.js',
            'edu_timetable_ai/static/src/js/ai_optimizer.js',
            'edu_timetable_ai/static/src/css/timetable.css',
        ],
        'web.assets_frontend': [
            'edu_timetable_ai/static/src/css/timetable_public.css',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 7,
    'price': 299.00,
    'currency': 'EUR',
}
