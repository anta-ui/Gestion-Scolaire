# -*- coding: utf-8 -*-
{
    'name': 'École Extraordinaire - Gestionnaire de Transport Scolaire',
    'version': '17.0.1.0.0',
    'category': 'Education/Transport',
    'summary': 'Système complet de gestion du transport scolaire avec GPS et IA',
    'description': """
Gestionnaire de Transport Scolaire Intelligent
==============================================

Système complet de gestion du transport scolaire incluant:

• Gestion de flotte avec maintenance
• Suivi GPS temps réel des véhicules  
• Gestion des chauffeurs et personnel
• Optimisation automatique des itinéraires
• Interface parents avec notifications
• Facturation et abonnements
• Analytics et reporting avancés
• Sécurité et gestion d'urgences
• Applications mobiles intégrées

Le module permet une gestion complète du transport scolaire avec des outils modernes d'IA et de géolocalisation pour optimiser les coûts et améliorer la sécurité des étudiants.
""",
    'author': 'École Extraordinaire',
    'website': 'https://www.ecole-extraordinaire.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'openeducat_core',
        'fleet',
        'account',
        'stock',
        'hr',
        'calendar',
        'website',
        'mail',
        'sms',
        'contacts',
    ],
    'external_dependencies': {
        'python': [
            'geopy',
            'googlemaps', 
            'gpxpy',
            'folium',
            'polyline',
            'qrcode',
            'pillow',
            'requests',
            'beautifulsoup4',
        ],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/transport_actions.xml',
        'views/menu.xml',
        'views/transport_menu.xml',
        'views/transport_vehicle_views.xml',
        'views/driver_views.xml',
        'views/route_views.xml',
        'views/trip_views.xml',
        'views/maintenance_views.xml',
        'views/billing_views.xml',
        'views/tracking_views.xml',
        'views/student_views.xml',
        'views/transport_views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'edu_transport_manager/static/src/css/*.css',
            'edu_transport_manager/static/src/js/*.js',
        ],
        'web.assets_frontend': [
            'edu_transport_manager/static/src/css/frontend.css',
            'edu_transport_manager/static/src/js/frontend.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
}
