# -*- coding: utf-8 -*-
{
    'name': 'Education Student Enhanced',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Module éducation avancé pour la gestion des élèves du primaire au lycée',
    'description': """
Module de gestion éducative extraordinaire
=========================================

Ce module étend OpenEduCat avec des fonctionnalités avancées :

* 🆔 Identité étendue avec QR codes
* 👨‍👩‍👧‍👦 Gestion familiale complète
* 🏥 Dossier médical détaillé
* 📊 Suivi comportemental avec IA
* 📄 Gestion documentaire
* 📈 Analytics et prédictions
* 🚌 Transport et localisation

Parfait pour les établissements scolaires modernes !
    """,
    'author': 'Votre Nom',
    'website': 'https://www.exemple.com',
    'depends': [
        'base',
        'mail',
        'web',
        'openeducat_core',
    ],
    'external_dependencies': {
        'python': ['qrcode', 'PIL'],  # Dépendances Python
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/student_categories.xml',
        'views/student_enhanced_views.xml',
        'views/student_family_views.xml',
        'views/student_medical_views.xml',
        'views/student_behavior_views.xml',
        'views/student_document_views.xml',
        'views/menus.xml',
        'wizards/parent_alert_wizard.xml',
        'reports/student_card_report.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'edu_student_enhanced/static/src/css/student_enhanced.css',
            'edu_student_enhanced/static/src/js/student_enhanced.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}