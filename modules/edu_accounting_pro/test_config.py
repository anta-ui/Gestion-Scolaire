# -*- coding: utf-8 -*-

"""
Configuration pour les tests API du module edu_accounting_pro
Modifiez ces valeurs selon votre environnement
"""

# Configuration de connexion Odoo
ODOO_CONFIG = {
    'BASE_URL': 'http://172.16.209.129:80',
    'DATABASE': 'school_management_new',
    'USERNAME': 'admin',
    'PASSWORD': 'admin'
}

# Configuration des tests
TEST_CONFIG = {
    # IDs de test (assurez-vous qu'ils existent dans votre base de données)
    'ACADEMIC_YEAR_ID': 1,
    'COURSE_ID': 1,
    'STUDENT_ID': 1,
    'FEE_TYPE_ID': 1,
    'PAYMENT_METHOD_ID': 1,
    'BATCH_ID': 1,
    
    # Données de test
    'TEST_STRUCTURE_NAME': 'Structure Test API',
    'TEST_STRUCTURE_CODE': 'ST_API_001',
    'TEST_FEE_TYPE_NAME': 'Type Test API',
    'TEST_FEE_TYPE_CODE': 'TT_API_001',
    'TEST_PAYMENT_REFERENCE': 'PAY_API_001',
    'TEST_AMOUNT': 1000.0,
    
    # Options de test
    'VERBOSE': True,
    'SAVE_REPORTS': True,
    'CLEANUP_TEST_DATA': True,
    'TIMEOUT': 30,  # secondes
}

# Endpoints à tester
ENDPOINTS_TO_TEST = [
    # Fee Structure
    {
        'name': 'Fee Structure - Liste',
        'endpoint': '/api/fee-structures',
        'method': 'GET',
        'data': {'limit': 10}
    },
    {
        'name': 'Fee Structure - Création',
        'endpoint': '/api/fee-structures/create',
        'method': 'POST',
        'data': {
            'name': TEST_CONFIG['TEST_STRUCTURE_NAME'],
            'code': TEST_CONFIG['TEST_STRUCTURE_CODE'],
            'academic_year_id': TEST_CONFIG['ACADEMIC_YEAR_ID'],
            'course_id': TEST_CONFIG['COURSE_ID'],
            'billing_type': 'annual',
            'active': True
        }
    },
    # Fee Type
    {
        'name': 'Fee Type - Liste',
        'endpoint': '/api/fee-types',
        'method': 'GET',
        'data': {'limit': 10}
    },
    {
        'name': 'Fee Type - Création',
        'endpoint': '/api/fee-types/create',
        'method': 'POST',
        'data': {
            'name': TEST_CONFIG['TEST_FEE_TYPE_NAME'],
            'code': TEST_CONFIG['TEST_FEE_TYPE_CODE'],
            'default_amount': TEST_CONFIG['TEST_AMOUNT'],
            'is_mandatory': True,
            'active': True
        }
    },
    # Student Invoice
    {
        'name': 'Student Invoice - Liste',
        'endpoint': '/api/student-invoices',
        'method': 'GET',
        'data': {'limit': 10}
    },
    # Student Payment
    {
        'name': 'Student Payment - Liste',
        'endpoint': '/api/student-payments',
        'method': 'GET',
        'data': {'limit': 10}
    },
    # Dashboard
    {
        'name': 'Dashboard - Statistiques',
        'endpoint': '/api/accounting-dashboard/stats',
        'method': 'GET',
        'data': {}
    },
    # Configuration
    {
        'name': 'Configuration - Liste',
        'endpoint': '/api/accounting-config',
        'method': 'GET',
        'data': {}
    }
]

# Messages d'erreur courants
ERROR_MESSAGES = {
    'AUTH_FAILED': 'Échec de l\'authentification',
    'ENDPOINT_NOT_FOUND': 'Endpoint non trouvé',
    'INVALID_DATA': 'Données invalides',
    'SERVER_ERROR': 'Erreur serveur',
    'TIMEOUT': 'Timeout de la requête',
    'CONNECTION_ERROR': 'Erreur de connexion'
} 