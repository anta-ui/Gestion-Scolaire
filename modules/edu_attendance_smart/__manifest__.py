# -*- coding: utf-8 -*-
{
    'name': 'Attendance Smart - Gestion intelligente des présences',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Système de présences ultra-moderne avec QR codes, biométrie et analyses',
    'description': """
Système de présences révolutionnaire pour établissements scolaires
================================================================

Fonctionnalités principales:
---------------------------
* Pointage par QR code personnel et salle
* Interface biométrique (empreintes digitales)
* Pointage par badge RFID/NFC
* Application mobile pour enseignants
* Gestion automatique des retards et absences
* Notifications en temps réel aux parents
* Justificatifs d'absence numériques
* Rapports et statistiques avancés
* Alertes automatiques
* Géolocalisation pour sorties scolaires
* Interface élève moderne et intuitive
* Tableaux de bord en temps réel

Compatible avec Odoo 17.0
    """,
    'author': 'École Extraordinaire Dev Team',
    'website': 'https://www.ecole-extraordinaire.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
        'hr_attendance',
        'contacts',
        'website',
        # 'openeducat_core',  # Temporairement commenté
        # 'openeducat_attendance',  # Temporairement commenté
    ],
    'data': [
        'security/attendance_security.xml',
        'security/ir.model.access.csv',
        'views/edu_attendance_device_views.xml',
        'views/edu_attendance_session_views.xml',
        'views/edu_attendance_record_views.xml',
        'views/edu_qr_code_views.xml',
        'views/edu_attendance_mobile_views.xml',
        'wizard/attendance_bulk_action_views.xml',
        'wizard/attendance_report_wizard_views.xml',
        'views/edu_attendance_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'edu_attendance_smart/static/src/css/attendance_style.css',
            'edu_attendance_smart/static/src/js/attendance_dashboard.js',
            'edu_attendance_smart/static/src/js/qr_scanner.js',
            'edu_attendance_smart/static/src/js/biometric_scanner.js',
            'edu_attendance_smart/static/src/xml/attendance_templates.xml',
        ],
        'web.assets_frontend': [
            'edu_attendance_smart/static/src/css/mobile_attendance.css',
            'edu_attendance_smart/static/src/js/mobile_scanner.js',
        ],
    },
    'external_dependencies': {
        'python': ['qrcode', 'PIL', 'pyzbar', 'cv2'],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 11,
}
