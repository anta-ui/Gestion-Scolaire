# -*- coding: utf-8 -*-
{
    'name': 'Communication Hub - Système de communication 360°',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Plateforme de communication complète : SMS, Email, Push, Chat en temps réel',
    'description': """
Système de communication révolutionnaire pour établissements scolaires
===================================================================

Fonctionnalités principales:
---------------------------
* 📱 SMS automatiques et manuels (Twilio, AWS SNS)
* 📧 Emails personnalisés avec templates avancés
* 🔔 Notifications push mobiles (Firebase)
* 💬 Chat en temps réel (enseignants ↔ parents)
* 📢 Annonces générales et ciblées
* 🎯 Campagnes de communication automatisées
* 📊 Rapports de diffusion et engagement
* 🌐 Interface multilingue complète
* 🔐 Système de permissions granulaires
* 📋 Modèles de messages prédéfinis
* ⏰ Programmation et automation intelligente
* 📱 Application mobile dédiée
* 🎨 Interface moderne et intuitive

Intégrations supportées:
-----------------------
* Twilio (SMS)
* SendGrid (Email)
* Firebase (Push notifications)
* WhatsApp Business API
* Telegram Bot API
* Microsoft Teams
* Slack

Compatible avec OpenEduCat et Odoo 17.0
    """,
    'author': 'École Extraordinaire Dev Team',
    'website': 'https://www.ecole-extraordinaire.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
        'sms',
        'portal',
        'website',
        'openeducat_core',               # Module principal OpenEduCat
        'openeducat_parent',             # Pour communication avec les parents
        'openeducat_activity',           # Pour les activités et événements
        'openeducat_admission',          # Pour les communications d'admission
        'edu_student_enhanced',          # Module étendu des étudiants
        'edu_evaluation_genius',         # Module d'évaluation
        'edu_attendance_smart',          # Module de présence intelligent
    ],
    'data': [
        # Sécurité
        'security/communication_security.xml',
        'security/ir.model.access.csv',
        
        # Données de base
        'data/message_templates_data.xml',
        'data/sms_providers_data.xml',
        'data/ir_cron_data.xml',
        
        # Vues
        'views/edu_communication_menus.xml',
        'views/edu_message_views.xml',
        'views/edu_message_template_views.xml',
        'views/edu_communication_config_views.xml',
    ],
    'external_dependencies': {
        'python': [
            'twilio', 
            'sendgrid', 
            'firebase-admin', 
            'pyfcm',
            'requests',
            'html2text',
            'markdown',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 12,
    'post_init_hook': 'post_init_hook',
}
