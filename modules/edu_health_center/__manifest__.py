# -*- coding: utf-8 -*-
{
    'name': "Centre de Santé Éducatif",
    'summary': """
        Gestion complète du centre de santé pour les établissements éducatifs""",
    'description': """
        Module complet pour la gestion du centre de santé dans les établissements éducatifs.
        
        Fonctionnalités principales:
        - Tableau de bord de santé
        - Gestion des dossiers médicaux des étudiants
        - Alertes et notifications de santé
        - Analyses et rapports de santé
        - Suivi des vaccinations
        - Gestion des consultations médicales
        - Inventaire médical
    """,
    'author': "Votre Entreprise",
    'website': "http://www.yourcompany.com",
    'category': 'Education',
    'version': '17.0.1.0.1',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/health_actions.xml',
        'data/dashboard_data.xml',
        'views/menu.xml',
        'views/health_dashboard_views.xml',
        'views/health_record_views.xml',
        'views/consultation_views.xml',
        'views/health_alert_views.xml',
        'views/analytics_views.xml',
        'views/emergency_views.xml',
        'views/insurance_views.xml',
        'views/staff_views.xml',
        'views/medication_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
