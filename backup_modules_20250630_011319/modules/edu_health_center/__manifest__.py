# -*- coding: utf-8 -*-
{
    'name': 'École Extraordinaire - Centre de Santé & Infirmerie',
    'version': '17.0.1.0.0',
    'category': 'Education/Health',
    'summary': 'Gestion complète de la santé scolaire avec infirmerie intelligente',
    'description': """
Centre de Santé Scolaire
========================

Module de gestion complète du centre de santé pour établissements éducatifs.

Fonctionnalités principales:
- Dossiers médicaux étudiants
- Consultations médicales
- Gestion des urgences
- Pharmacie et médicaments
- Suivi vaccinal
- Personnel médical
    """,
    'author': 'École Extraordinaire Dev Team',
    'website': 'https://ecole-extraordinaire.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'mail',
        'openeducat_core',
    ],
    'external_dependencies': {
        'python': [],
    },
    'data': [
        # Sécurité
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # Données de base
        'data/demo_data.xml',
        
        # Menu principal
        'views/menu.xml',
    ],
    'assets': {
    },
    'demo': [
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 9,
    'price': 599.00,
    'currency': 'EUR',
}
