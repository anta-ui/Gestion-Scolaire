# -*- coding: utf-8 -*-
{
    'name': 'École Extraordinaire - Bibliothèque Numérique Plus',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Système de gestion de bibliothèque avancé pour OpenEduCat',
    'description': '''
        Système de Gestion de Bibliothèque Avancé
        =========================================
        
        Ce module étend les fonctionnalités de bibliothèque avec :
        
        * Gestion complète des livres avec métadonnées
        * Système de prêts et retours automatisés
        * Réservations de livres
        * Bibliothèque numérique avec accès sécurisé
        * Système de recommandations basé sur l'IA
        * Analyses et statistiques détaillées
        * QR codes pour la gestion physique
        * Notifications automatiques
        * Interface moderne et intuitive
        
        Compatible avec OpenEduCat pour une intégration parfaite.
    ''',
    'author': 'École Extraordinaire',
    'website': 'https://www.ecole-extraordinaire.com',
    'depends': [
        'base',
        'mail',
        'web',
        'openeducat_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/demo_data.xml',
        'views/library_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'external_dependencies': {
        'python': ['qrcode', 'PIL', 'requests', 'bs4'],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 95,
    'license': 'LGPL-3',
}
