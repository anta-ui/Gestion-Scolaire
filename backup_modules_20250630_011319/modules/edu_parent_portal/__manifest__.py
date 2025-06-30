# -*- coding: utf-8 -*-
{
    'name': 'Parent Portal - Portail parents moderne et interactif',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Interface complète pour les parents : suivi scolaire, communication, planning',
    'description': """
Portail parents révolutionnaire pour établissements scolaires
==========================================================

Fonctionnalités principales:
---------------------------
* 📱 Interface responsive et application mobile PWA
* 👨‍👩‍👧‍👦 Gestion multi-enfants pour les familles
* 📊 Tableau de bord personnalisé et intuitif
* 📚 Suivi des notes et évaluations en temps réel
* 📅 Planning et emploi du temps interactif
* ✅ Présences et absences avec historique
* 📝 Devoirs et travaux à rendre
* 💬 Messagerie directe avec les enseignants
* 📢 Notifications et annonces ciblées
* 📄 Documents scolaires et bulletins
* 💰 Facturation et paiements en ligne
* 🏥 Suivi médical et autorisations
* 🚌 Transport scolaire et géolocalisation
* 📅 Rendez-vous et réunions parents
* 🎯 Objectifs pédagogiques et progression
* 📊 Rapports et analyses personnalisés
* 🔐 Sécurité renforcée et authentification 2FA
* 🌍 Interface multilingue complète

Modules d'intégration:
--------------------
* Intégration avec tous les modules edu_*
* Synchronisation temps réel
* API REST complète
* Webhooks pour notifications
* Export PDF personnalisable
* Système de favoris et raccourcis

Compatible avec OpenEduCat et Odoo 17.0
    """,
    'author': 'École Extraordinaire Dev Team',
    'website': 'https://www.ecole-extraordinaire.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'portal',
        'website',
        'mail',
        'calendar',
        'account',
        'payment',
        'openeducat_core',
    ],
    'data': [
        # Sécurité
        # 'security/parent_portal_security.xml',
        'security/ir.model.access.csv',
        
        # Données de base
        'data/portal_menu_data.xml',
        'data/notification_preferences_data.xml',
        'data/portal_sequences.xml',
        'data/ir_cron_data.xml',
        
        # Configuration et vues modèles (avec actions)
        'views/edu_parent_portal_config_views.xml',
        'views/edu_portal_menu_views.xml',
        'views/edu_notification_preference_views.xml',
        'views/edu_parent_notification_views.xml',
        'views/edu_parent_dashboard_views.xml',
        'views/edu_parent_profile_views.xml',
        'views/edu_student_follow_views.xml',
        'views/edu_parent_appointment_views.xml',
        'views/edu_parent_document_views.xml',
        'views/edu_parent_payment_views.xml',
        
        # Menus (doivent être chargés après les actions)
        'views/edu_parent_portal_menus.xml',
        
        # Vues portail (temporairement commentées)
        # 'templates/portal_layout.xml',
        # 'templates/portal_dashboard.xml',
        # 'templates/portal_student_profile.xml',
        # 'templates/portal_grades.xml',
        # 'templates/portal_attendance.xml',
        # 'templates/portal_homework.xml',
        # 'templates/portal_schedule.xml',
        # 'templates/portal_messages.xml',
        # 'templates/portal_documents.xml',
        # 'templates/portal_payments.xml',
        # 'templates/portal_appointments.xml',
        # 'templates/portal_mobile.xml',
        
        # Rapports (temporairement commentés)
        # 'reports/report_student_summary.xml',
        # 'reports/report_attendance_summary.xml',
        # 'reports/report_grade_summary.xml',
        
        # Wizards (temporairement commentés)
        # 'wizard/parent_report_wizard_views.xml',
        # 'wizard/appointment_booking_wizard_views.xml',
        # 'wizard/document_request_wizard_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # CSS
            'edu_parent_portal/static/src/css/portal_style.css',
            'edu_parent_portal/static/src/css/portal_dashboard.css',
            'edu_parent_portal/static/src/css/portal_mobile.css',
            'edu_parent_portal/static/src/css/portal_responsive.css',
            
            # JavaScript
            'edu_parent_portal/static/src/js/portal_main.js',
        ],
        'web.assets_backend': [
            'edu_parent_portal/static/src/css/portal_style.css',
        ],
    },
    'external_dependencies': {
        'python': [
            'qrcode',
            'reportlab',
            'xlsxwriter',
            'icalendar',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 13,
    'post_init_hook': 'post_init_hook',
}
