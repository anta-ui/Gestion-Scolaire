# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduAccountingConfigController(http.Controller):
    """Controller pour la gestion de la configuration comptable éducative"""

    @http.route('/api/accounting-config', type='json', auth='user', methods=['POST'], csrf=False)
    def get_accounting_configs(self, **kwargs):
        """Récupère la liste des configurations comptables"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
            if kwargs.get('company_id'):
                domain.append(('company_id', '=', kwargs['company_id']))
            if kwargs.get('config_type'):
                domain.append(('config_type', '=', kwargs['config_type']))
            
            # Recherche par nom
            if kwargs.get('search'):
                domain.append('|', ('name', 'ilike', kwargs['search']), ('code', 'ilike', kwargs['search']))
            
            # Pagination 
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            configs = request.env['edu.accounting.config'].search(domain, limit=limit, offset=offset)
            
            result = []
            for config in configs:
                result.append({
                    'id': config.id,
                    'name': config.name,
                    'code': config.code if hasattr(config, 'code') else '',
                    'description': config.description if hasattr(config, 'description') else '',
                    'config_type': config.config_type if hasattr(config, 'config_type') else '',
                    'config_type_display': dict(config._fields['config_type'].selection).get(config.config_type, '') if hasattr(config, 'config_type') else '',
                    'company_id': config.company_id.id if hasattr(config, 'company_id') and config.company_id else None,
                    'company_name': config.company_id.name if hasattr(config, 'company_id') and config.company_id else '',
                    'is_default': config.is_default if hasattr(config, 'is_default') else False,
                    'sequence': config.sequence if hasattr(config, 'sequence') else 0,
                    'active': config.active if hasattr(config, 'active') else True,
                    'create_date': config.create_date.isoformat() if config.create_date else None,
                    'write_date': config.write_date.isoformat() if config.write_date else None,
                })
            
            total_count = request.env['edu.accounting.config'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des configurations: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-config/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_accounting_config(self, **kwargs):
        """Récupère une configuration comptable spécifique"""
        try:
            config_id = kwargs.get('config_id')
            if not config_id:
                return {'success': False, 'error': 'ID de configuration requis'}
            
            config = request.env['edu.accounting.config'].browse(config_id)
            
            if not config.exists():
                return {'success': False, 'error': 'Configuration non trouvée'}
            
            data = {
                'id': config.id,
                'name': config.name,
                'code': config.code if hasattr(config, 'code') else '',
                'description': config.description if hasattr(config, 'description') else '',
                'config_type': config.config_type if hasattr(config, 'config_type') else '',
                'company_id': config.company_id.id if hasattr(config, 'company_id') and config.company_id else None,
                'company_name': config.company_id.name if hasattr(config, 'company_id') and config.company_id else '',
                'is_default': config.is_default if hasattr(config, 'is_default') else False,
                'auto_create_accounts': config.auto_create_accounts if hasattr(config, 'auto_create_accounts') else False,
                'auto_reconcile': config.auto_reconcile if hasattr(config, 'auto_reconcile') else False,
                'default_receivable_account_id': config.default_receivable_account_id.id if hasattr(config, 'default_receivable_account_id') and config.default_receivable_account_id else None,
                'default_receivable_account_name': config.default_receivable_account_id.name if hasattr(config, 'default_receivable_account_id') and config.default_receivable_account_id else '',
                'default_income_account_id': config.default_income_account_id.id if hasattr(config, 'default_income_account_id') and config.default_income_account_id else None,
                'default_income_account_name': config.default_income_account_id.name if hasattr(config, 'default_income_account_id') and config.default_income_account_id else '',
                'default_journal_id': config.default_journal_id.id if hasattr(config, 'default_journal_id') and config.default_journal_id else None,
                'default_journal_name': config.default_journal_id.name if hasattr(config, 'default_journal_id') and config.default_journal_id else '',
                'sequence': config.sequence if hasattr(config, 'sequence') else 0,
                'active': config.active if hasattr(config, 'active') else True,
                'settings': config.settings if hasattr(config, 'settings') else {},
                'create_date': config.create_date.isoformat() if config.create_date else None,
                'write_date': config.write_date.isoformat() if config.write_date else None,
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la configuration: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-config/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_accounting_config(self, **kwargs):
        """Crée une nouvelle configuration comptable"""
        try:
            # Validation des champs requis
            required_fields = ['name', 'config_type']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Champ requis manquant: {field}'}
            
            # Préparation des données
            vals = {
                'name': kwargs['name'],
                'config_type': kwargs['config_type'],
            }
            
            # Champs optionnels
            optional_fields = [
                'code', 'description', 'company_id', 'is_default', 'auto_create_accounts',
                'auto_reconcile', 'default_receivable_account_id', 'default_income_account_id',
                'default_journal_id', 'sequence', 'active', 'settings'
            ]
            
            for field in optional_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Si pas de company_id fourni, utiliser la compagnie par défaut
            if not vals.get('company_id'):
                vals['company_id'] = request.env.company.id
            
            # Si cette configuration est définie par défaut, désactiver les autres du même type
            if vals.get('is_default'):
                request.env['edu.accounting.config'].search([
                    ('is_default', '=', True),
                    ('config_type', '=', vals['config_type']),
                    ('company_id', '=', vals['company_id'])
                ]).write({'is_default': False})
            
            # Création de la configuration
            config = request.env['edu.accounting.config'].create(vals)
            
            return {
                'success': True,
                'data': {
                    'id': config.id,
                    'name': config.name,
                    'code': config.code if hasattr(config, 'code') else ''
                },
                'message': 'Configuration comptable créée avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la création: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-config/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_accounting_config(self, **kwargs):
        """Met à jour une configuration comptable"""
        try:
            config_id = kwargs.get('config_id')
            if not config_id:
                return {'success': False, 'error': 'ID de configuration requis'}
            
            config = request.env['edu.accounting.config'].browse(config_id)
            
            if not config.exists():
                return {'success': False, 'error': 'Configuration non trouvée'}
            
            # Préparation des données à mettre à jour
            vals = {}
            updatable_fields = [
                'name', 'code', 'description', 'config_type', 'company_id', 'is_default',
                'auto_create_accounts', 'auto_reconcile', 'default_receivable_account_id',
                'default_income_account_id', 'default_journal_id', 'sequence', 'active', 'settings'
            ]
            
            for field in updatable_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Si cette configuration est définie par défaut, désactiver les autres du même type
            if vals.get('is_default'):
                request.env['edu.accounting.config'].search([
                    ('is_default', '=', True),
                    ('config_type', '=', vals.get('config_type', config.config_type)),
                    ('company_id', '=', vals.get('company_id', config.company_id.id if hasattr(config, 'company_id') and config.company_id else None)),
                    ('id', '!=', config.id)
                ]).write({'is_default': False})
            
            # Mise à jour
            config.write(vals)
            
            return {
                'success': True,
                'message': 'Configuration comptable mise à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-config/set-default', type='json', auth='user', methods=['POST'], csrf=False)
    def set_default_config(self, **kwargs):
        """Définit une configuration comme configuration par défaut"""
        try:
            config_id = kwargs.get('config_id')
            if not config_id:
                return {'success': False, 'error': 'ID de configuration requis'}
            
            config = request.env['edu.accounting.config'].browse(config_id)
            
            if not config.exists():
                return {'success': False, 'error': 'Configuration non trouvée'}
            
            # Désactiver toutes les autres configurations par défaut du même type
            request.env['edu.accounting.config'].search([
                ('is_default', '=', True),
                ('config_type', '=', config.config_type if hasattr(config, 'config_type') else ''),
                ('company_id', '=', config.company_id.id if hasattr(config, 'company_id') and config.company_id else None)
            ]).write({'is_default': False})
            
            # Activer cette configuration comme défaut
            config.write({'is_default': True})
            
            return {
                'success': True,
                'message': f'Configuration "{config.name}" définie par défaut'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la définition par défaut: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-config/validate', type='json', auth='user', methods=['POST'], csrf=False)
    def validate_config(self, **kwargs):
        """Valide une configuration comptable"""
        try:
            config_id = kwargs.get('config_id')
            if not config_id:
                return {'success': False, 'error': 'ID de configuration requis'}
            
            config = request.env['edu.accounting.config'].browse(config_id)
            
            if not config.exists():
                return {'success': False, 'error': 'Configuration non trouvée'}
            
            # Validation de base
            errors = []
            warnings = []
            
            # Vérifier les comptes par défaut
            if hasattr(config, 'default_receivable_account_id') and not config.default_receivable_account_id:
                warnings.append('Aucun compte de créances par défaut défini')
            
            if hasattr(config, 'default_income_account_id') and not config.default_income_account_id:
                warnings.append('Aucun compte de revenus par défaut défini')
            
            if hasattr(config, 'default_journal_id') and not config.default_journal_id:
                warnings.append('Aucun journal par défaut défini')
            
            # Vérifier la cohérence des comptes
            if (hasattr(config, 'default_receivable_account_id') and config.default_receivable_account_id and 
                hasattr(config, 'default_income_account_id') and config.default_income_account_id):
                if config.default_receivable_account_id.company_id != config.default_income_account_id.company_id:
                    errors.append('Les comptes par défaut doivent appartenir à la même compagnie')
            
            # Appeler une méthode de validation personnalisée si elle existe
            if hasattr(config, 'validate_configuration'):
                try:
                    config.validate_configuration()
                except ValidationError as e:
                    errors.append(str(e))
            
            data = {
                'is_valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'validation_status': 'valid' if len(errors) == 0 else 'invalid',
                'total_issues': len(errors) + len(warnings)
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la validation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-config/duplicate', type='json', auth='user', methods=['POST'], csrf=False)
    def duplicate_config(self, **kwargs):
        """Duplique une configuration comptable"""
        try:
            config_id = kwargs.get('config_id')
            new_name = kwargs.get('new_name')
            
            if not config_id:
                return {'success': False, 'error': 'ID de configuration requis'}
            if not new_name:
                return {'success': False, 'error': 'Nouveau nom requis'}
            
            config = request.env['edu.accounting.config'].browse(config_id)
            
            if not config.exists():
                return {'success': False, 'error': 'Configuration non trouvée'}
            
            # Préparation des données pour la duplication
            vals = config.copy_data()[0]
            vals.update({
                'name': new_name,
                'code': f"{vals.get('code', '')}_copy" if vals.get('code') else '',
                'is_default': False,  # La copie ne peut pas être par défaut
            })
            
            # Création de la copie
            new_config = request.env['edu.accounting.config'].create(vals)
            
            return {
                'success': True,
                'data': {
                    'id': new_config.id,
                    'name': new_config.name,
                    'code': new_config.code if hasattr(new_config, 'code') else ''
                },
                'message': f'Configuration dupliquée sous le nom "{new_name}"'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la duplication: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-config/types', type='json', auth='user', methods=['POST'], csrf=False)
    def get_config_types(self, **kwargs):
        """Récupère la liste des types de configuration disponibles"""
        try:
            # Récupération des types depuis la sélection du modèle
            config_model = request.env['edu.accounting.config']
            
            if hasattr(config_model, '_fields') and 'config_type' in config_model._fields:
                types = config_model._fields['config_type'].selection
                result = [{'key': key, 'label': label} for key, label in types]
            else:
                result = [
                    {'key': 'general', 'label': 'Général'},
                    {'key': 'student', 'label': 'Étudiant'},
                    {'key': 'fee', 'label': 'Frais'},
                    {'key': 'payment', 'label': 'Paiement'},
                    {'key': 'invoice', 'label': 'Facturation'},
                ]
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des types: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/accounting-config/statistics', type='json', auth='user', methods=['POST'], csrf=False)
    def get_config_statistics(self, **kwargs):
        """Récupère les statistiques des configurations comptables"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('company_id'):
                domain.append(('company_id', '=', kwargs['company_id']))
            
            configs = request.env['edu.accounting.config'].search(domain)
            
            # Calculs des statistiques
            total_configs = len(configs)
            active_configs = len(configs.filtered(lambda c: c.active if hasattr(c, 'active') else True))
            default_configs = len(configs.filtered(lambda c: c.is_default if hasattr(c, 'is_default') else False))
            
            # Statistiques par type
            by_type = {}
            for config in configs:
                config_type = config.config_type if hasattr(config, 'config_type') else 'general'
                if config_type not in by_type:
                    by_type[config_type] = {'total': 0, 'active': 0, 'default': 0}
                by_type[config_type]['total'] += 1
                if hasattr(config, 'active') and config.active:
                    by_type[config_type]['active'] += 1
                if hasattr(config, 'is_default') and config.is_default:
                    by_type[config_type]['default'] += 1
            
            # Statistiques par compagnie
            by_company = {}
            for config in configs:
                company_name = config.company_id.name if hasattr(config, 'company_id') and config.company_id else 'Sans compagnie'
                if company_name not in by_company:
                    by_company[company_name] = 0
                by_company[company_name] += 1
            
            data = {
                'total_configs': total_configs,
                'active_configs': active_configs,
                'inactive_configs': total_configs - active_configs,
                'default_configs': default_configs,
                'by_type': by_type,
                'by_company': by_company,
                'most_used_type': max(by_type.keys(), key=lambda k: by_type[k]['total']) if by_type else '',
                'completion_rate': (active_configs / total_configs * 100) if total_configs > 0 else 0,
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
