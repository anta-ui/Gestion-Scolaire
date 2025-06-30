# -*- coding: utf-8 -*-

from . import models
from . import wizards
from . import controllers

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Hook exécuté après l'installation du module"""
    try:
        _logger.info("=== Initialisation du module Education Accounting Pro ===")
        
        # Création des comptes comptables par défaut si nécessaire
        _create_default_accounts(env)
        
        # Configuration des séquences
        _setup_sequences(env)
        
        # Création des données de démonstration si demandé
        _setup_demo_data(env)
        
        _logger.info("Module Education Accounting Pro initialisé avec succès")
        
    except Exception as e:
        _logger.error(f"Erreur lors de l'initialisation du module: {e}")


def uninstall_hook(env):
    """Hook exécuté avant la désinstallation du module"""
    try:
        _logger.info("=== Désinstallation du module Education Accounting Pro ===")
        
        # Nettoyage des données si nécessaire
        _cleanup_data(env)
        
        _logger.info("Module Education Accounting Pro désinstallé avec succès")
        
    except Exception as e:
        _logger.error(f"Erreur lors de la désinstallation du module: {e}")


def _create_default_accounts(env):
    """Création des comptes comptables par défaut"""
    # Vérifier si les comptes existent déjà
    AccountAccount = env['account.account']
    
    # Compte créances étudiants
    if not AccountAccount.search([('code', '=', '411000')]):
        AccountAccount.create({
            'code': '411000',
            'name': 'Créances Étudiants',
            'account_type': 'asset_receivable',
            'reconcile': True,
        })
    
    # Compte produits scolarité
    if not AccountAccount.search([('code', '=', '706000')]):
        AccountAccount.create({
            'code': '706000',
            'name': 'Produits de Scolarité',
            'account_type': 'income',
        })
    
    # Compte bourses et aides
    if not AccountAccount.search([('code', '=', '658000')]):
        AccountAccount.create({
            'code': '658000',
            'name': 'Bourses et Aides Financières',
            'account_type': 'expense',
        })
    
    # Compte frais de retard
    if not AccountAccount.search([('code', '=', '758000')]):
        AccountAccount.create({
            'code': '758000',
            'name': 'Produits Frais de Retard',
            'account_type': 'income',
        })
    
    _logger.info("Comptes comptables par défaut créés")


def _setup_sequences(env):
    """Configuration des séquences"""
    # Les séquences sont créées via les données XML
    # Ici on peut faire des ajustements si nécessaire
    
    _logger.info("Séquences configurées")


def _setup_demo_data(env):
    """Configuration des données de démonstration"""
    # Vérifier si on est en mode démo
    if not env.registry.test_cr:
        return
    
    _logger.info("Données de démonstration configurées")


def _cleanup_data(env):
    """Nettoyage des données lors de la désinstallation"""
    # Supprimer les tâches cron spécifiques au module
    cron_jobs = env['ir.cron'].search([
        ('model_id.model', 'in', [
            'edu.accounting.config',
            'edu.student.invoice',
        ])
    ])
    if cron_jobs:
        cron_jobs.unlink()
    
    _logger.info("Données nettoyées")
