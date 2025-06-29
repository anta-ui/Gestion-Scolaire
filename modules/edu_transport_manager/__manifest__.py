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

Le module permet une gestion complète et intelligente du transport scolaire
avec des fonctionnalités avancées de géolocalisation, d'optimisation
d'itinéraires et de communication avec les familles.
    """,
    'author': 'École Extraordinaire Dev Team',
    'website': 'https://ecole-extraordinaire.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
        'portal',
        'calendar',
        'hr',
        'fleet',
        'account',
        'stock',
        'website',
        'website_sale',
        'openeducat_core',
        'edu_student_enhanced',
        'edu_parent_portal',
    ],
    'external_dependencies': {
        'python': ['geopy', 'googlemaps', 'gpxpy', 'folium', 'polyline'],
    },
    'data': [
        # Sécurité
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Données de base
        'data/data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'edu_transport_manager/static/src/js/transport_dashboard.js',
            'edu_transport_manager/static/src/js/gps_tracking.js',
            'edu_transport_manager/static/src/js/route_optimizer.js',
            'edu_transport_manager/static/src/js/mobile_tracker.js',
            'edu_transport_manager/static/src/css/transport_style.css',
        ],
        'web.assets_frontend': [
            'edu_transport_manager/static/src/css/mobile_transport.css',
            'edu_transport_manager/static/src/js/transport_public.js',
        ],
        'web.assets_qweb': [
            'edu_transport_manager/static/src/xml/transport_templates.xml',
        ],
    },
    'demo': [
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
    'price': 799.00,
    'currency': 'EUR',
}
