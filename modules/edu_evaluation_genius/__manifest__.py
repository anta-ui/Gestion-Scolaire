# -*- coding: utf-8 -*-
{
    'name': 'Évaluation Genius - Système d\'évaluation intelligent',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Système d\'évaluation ultra-complet avec analyses avancées',
    'description': """
Système d'évaluation révolutionnaire pour établissements scolaires
================================================================

Fonctionnalités principales:
---------------------------
* Évaluations multi-critères et multi-types
* Évaluation par compétences avancée  
* Calculs automatiques de moyennes intelligentes
* Bulletins personnalisables et professionnels
* Analytics et statistiques avancées
* Historique complet des évaluations
* Interface moderne et intuitive
* Tableaux de bord interactifs

Compatible avec OpenEduCat et Odoo 17.0
    """,
    'author': 'École Extraordinaire Dev Team',
    'website': 'https://www.ecole-extraordinaire.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
        'openeducat_core',
    ],
    'data': [
        # Sécurité
        'security/ir.model.access.csv',
        
        # Vues (avant les menus)
        'views/edu_evaluation_type_views.xml',
        'views/edu_grade_scale_views.xml',
        'views/edu_competency_views.xml',
        'views/edu_evaluation_period_views.xml',
        'views/edu_evaluation_criteria_views.xml',
        'views/edu_evaluation_views.xml',
        
        # Menus (après les vues)
        'views/edu_evaluation_menus.xml',
        
        # Données de base (en dernier)
        'data/evaluation_types_data.xml',
        'data/grade_scales_data.xml', 
        'data/competencies_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
}
