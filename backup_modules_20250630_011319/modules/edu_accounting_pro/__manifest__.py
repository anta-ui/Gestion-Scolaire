# -*- coding: utf-8 -*-
{
    'name': 'Education Accounting Pro',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Système comptable complet pour institutions éducatives',
    'description': """
Système de Comptabilité Éducative Professionnel
=============================================

Ce module fournit une solution comptable complète pour les institutions éducatives :

Fonctionnalités principales :
* Gestion des structures de frais par classe et année
* Facturation automatique des étudiants
* Gestion des paiements et échéanciers
* Système de bourses et remises
* Paiements en ligne (Stripe, PayPal, Mobile Money)
* Rapports financiers détaillés
* Tableau de bord comptable
* Portail étudiant pour consultation des factures
* Sélection automatique de devise par pays

Compatible avec OpenEduCat pour une intégration complète.
    """,
    'author': 'Education Pro Team',
    'website': 'https://www.education-pro.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'mail',
        'portal',
        'web',
        'product',
        'sale',
        'payment',
        'openeducat_core',
        # 'openeducat_fees',  # Temporairement désactivé
    ],
    'data': [
        # Sécurité
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Données de base
        'data/fee_types_data.xml',
        'data/accounting_config_data.xml',
        
        # Vues
        'views/edu_accounting_config_views.xml',
        'views/edu_fee_type_views.xml',
        'views/edu_fee_structure_views.xml',
        'views/edu_student_invoice_views.xml',
        'views/edu_accounting_menus.xml',
        
        # Rapports - temporairement désactivés
        # 'reports/invoice_report_templates.xml',
        # 'reports/payment_receipt_templates.xml',
        # 'reports/financial_reports.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'edu_accounting_pro/static/src/css/accounting_dashboard.css',
            'edu_accounting_pro/static/src/js/accounting_dashboard.js',
            'edu_accounting_pro/static/src/js/payment_widget.js',
        ],
        'web.assets_frontend': [
            'edu_accounting_pro/static/src/css/portal_styles.css',
            'edu_accounting_pro/static/src/js/portal_payment.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
