# -*- coding: utf-8 -*-

import json
import logging
import base64
import hashlib
from datetime import datetime, timedelta
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError, UserError
from odoo.http import serialize_exception

_logger = logging.getLogger(__name__)


class EduBiometricDataController(http.Controller):
    """Contrôleur API pour la gestion des données biométriques"""

    @http.route('/api/biometric/data', type='json', auth='user', methods=['GET'])
    def get_biometric_data(self, **kwargs):
        """Récupère toutes les données biométriques (sans contenu sensible)"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('partner_id'):
                domain.append(('partner_id', '=', kwargs['partner_id']))
            
            if kwargs.get('biometric_type'):
                domain.append(('biometric_type', '=', kwargs['biometric_type']))
                
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
                
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))

            # Pagination
            limit = kwargs.get('limit', 100)
            offset = kwargs.get('offset', 0)
            
            biometric_records = request.env['edu.biometric.data'].search(
                domain, 
                limit=limit, 
                offset=offset,
                order='create_date desc, id desc'
            )
            
            total_count = request.env['edu.biometric.data'].search_count(domain)
            
            return {
                'status': 'success',
                'data': [self._format_biometric_data(record) for record in biometric_records],
                'count': len(biometric_records),
                'total_count': total_count
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des données biométriques: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/biometric/data/<int:biometric_id>', type='json', auth='user', methods=['GET'])
    def get_biometric_record(self, biometric_id, **kwargs):
        """Récupère une donnée biométrique spécifique"""
        try:
            biometric_record = request.env['edu.biometric.data'].browse(biometric_id)
            if not biometric_record.exists():
                return {
                    'status': 'error',
                    'message': _('Donnée biométrique non trouvée')
                }
            
            return {
                'status': 'success',
                'data': self._format_biometric_data(biometric_record, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la donnée biométrique {biometric_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/biometric/data/person/<int:partner_id>', type='json', auth='user', methods=['GET'])
    def get_person_biometric_data(self, partner_id, **kwargs):
        """Récupère toutes les données biométriques d'une personne"""
        try:
            domain = [('partner_id', '=', partner_id)]
            
            # Filtres optionnels
            if kwargs.get('biometric_type'):
                domain.append(('biometric_type', '=', kwargs['biometric_type']))
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))

            biometric_records = request.env['edu.biometric.data'].search(domain)
            
            # Vérifier que la personne existe
            partner = request.env['res.partner'].browse(partner_id)
            if not partner.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            return {
                'status': 'success',
                'data': {
                    'person': {
                        'id': partner.id,
                        'name': partner.name,
                        'email': partner.email
                    },
                    'biometric_data': [self._format_biometric_data(record) for record in biometric_records],
                    'count': len(biometric_records)
                }
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des données biométriques de la personne {partner_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/biometric/data', type='json', auth='user', methods=['POST'])
    def create_biometric_data(self, **kwargs):
        """Crée une nouvelle donnée biométrique"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des données obligatoires
            required_fields = ['name', 'partner_id', 'biometric_type', 'biometric_data']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'status': 'error',
                        'message': _('Le champ %s est obligatoire') % field
                    }

            # Vérifier que la personne existe
            partner = request.env['res.partner'].browse(data['partner_id'])
            if not partner.exists():
                return {
                    'status': 'error',
                    'message': _('Personne non trouvée')
                }

            # Vérifier qu'il n'y a pas déjà une donnée biométrique active du même type
            existing = request.env['edu.biometric.data'].search([
                ('partner_id', '=', data['partner_id']),
                ('biometric_type', '=', data['biometric_type']),
                ('state', '=', 'active')
            ])
            
            if existing:
                return {
                    'status': 'error',
                    'message': _('Une donnée biométrique active de ce type existe déjà pour cette personne')
                }

            # Validation et traitement des données biométriques
            try:
                # Décoder les données base64 si nécessaire
                biometric_data = data['biometric_data']
                if isinstance(biometric_data, str):
                    # Vérifier si c'est du base64 valide
                    try:
                        base64.b64decode(biometric_data)
                    except Exception:
                        return {
                            'status': 'error',
                            'message': _('Format de données biométriques invalide')
                        }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': _('Erreur lors du traitement des données biométriques: %s') % str(e)
                }

            # Préparation des données
            biometric_record_data = self._prepare_biometric_data(data)
            biometric_record = request.env['edu.biometric.data'].create(biometric_record_data)

            # Log de sécurité
            self._log_biometric_action('create', biometric_record, data.get('source', 'api'))

            return {
                'status': 'success',
                'data': self._format_biometric_data(biometric_record, detailed=True),
                'message': _('Donnée biométrique créée avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la donnée biométrique: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/biometric/data/<int:biometric_id>', type='json', auth='user', methods=['PUT'])
    def update_biometric_data(self, biometric_id, **kwargs):
        """Met à jour une donnée biométrique existante"""
        try:
            biometric_record = request.env['edu.biometric.data'].browse(biometric_id)
            if not biometric_record.exists():
                return {
                    'status': 'error',
                    'message': _('Donnée biométrique non trouvée')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Ne permettre que certaines modifications pour des raisons de sécurité
            allowed_updates = ['name', 'state', 'active']
            update_data = {}
            
            for field in allowed_updates:
                if field in data:
                    update_data[field] = data[field]

            # Mise à jour spéciale pour les données biométriques (nécessite confirmation)
            if 'biometric_data' in data:
                if not data.get('confirm_update', False):
                    return {
                        'status': 'error',
                        'message': _('La mise à jour des données biométriques nécessite une confirmation explicite')
                    }
                update_data['biometric_data'] = data['biometric_data']

            if not update_data:
                return {
                    'status': 'error',
                    'message': _('Aucune donnée à mettre à jour')
                }

            # Log de sécurité avant modification
            old_state = biometric_record.state
            
            biometric_record.write(update_data)

            # Log de sécurité après modification
            self._log_biometric_action('update', biometric_record, data.get('source', 'api'), 
                                     extra_info=f"old_state: {old_state}, new_state: {biometric_record.state}")

            return {
                'status': 'success',
                'data': self._format_biometric_data(biometric_record, detailed=True),
                'message': _('Donnée biométrique mise à jour avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour de la donnée biométrique {biometric_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/biometric/data/<int:biometric_id>', type='json', auth='user', methods=['DELETE'])
    def delete_biometric_data(self, biometric_id, **kwargs):
        """Supprime une donnée biométrique"""
        try:
            biometric_record = request.env['edu.biometric.data'].browse(biometric_id)
            if not biometric_record.exists():
                return {
                    'status': 'error',
                    'message': _('Donnée biométrique non trouvée')
                }

            data = request.get_json_data() or {}
            
            # Exiger une confirmation pour la suppression
            if not data.get('confirm_delete', False):
                return {
                    'status': 'error',
                    'message': _('La suppression des données biométriques nécessite une confirmation explicite')
                }

            # Log de sécurité avant suppression
            person_name = biometric_record.partner_id.name
            biometric_type = biometric_record.biometric_type
            
            self._log_biometric_action('delete', biometric_record, data.get('source', 'api'))

            biometric_record.unlink()

            return {
                'status': 'success',
                'message': _('Donnée biométrique supprimée avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la suppression de la donnée biométrique {biometric_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/biometric/data/<int:biometric_id>/activate', type='json', auth='user', methods=['POST'])
    def activate_biometric_data(self, biometric_id, **kwargs):
        """Active une donnée biométrique"""
        try:
            biometric_record = request.env['edu.biometric.data'].browse(biometric_id)
            if not biometric_record.exists():
                return {
                    'status': 'error',
                    'message': _('Donnée biométrique non trouvée')
                }

            # Désactiver les autres données du même type pour la même personne
            existing_active = request.env['edu.biometric.data'].search([
                ('partner_id', '=', biometric_record.partner_id.id),
                ('biometric_type', '=', biometric_record.biometric_type),
                ('state', '=', 'active'),
                ('id', '!=', biometric_record.id)
            ])
            
            if existing_active:
                existing_active.write({'state': 'inactive'})

            biometric_record.write({'state': 'active', 'active': True})

            # Log de sécurité
            self._log_biometric_action('activate', biometric_record, 'api')

            return {
                'status': 'success',
                'data': self._format_biometric_data(biometric_record),
                'message': _('Donnée biométrique activée avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de l'activation de la donnée biométrique {biometric_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/biometric/data/<int:biometric_id>/deactivate', type='json', auth='user', methods=['POST'])
    def deactivate_biometric_data(self, biometric_id, **kwargs):
        """Désactive une donnée biométrique"""
        try:
            biometric_record = request.env['edu.biometric.data'].browse(biometric_id)
            if not biometric_record.exists():
                return {
                    'status': 'error',
                    'message': _('Donnée biométrique non trouvée')
                }

            biometric_record.write({'state': 'inactive', 'active': False})

            # Log de sécurité
            self._log_biometric_action('deactivate', biometric_record, 'api')

            return {
                'status': 'success',
                'data': self._format_biometric_data(biometric_record),
                'message': _('Donnée biométrique désactivée avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la désactivation de la donnée biométrique {biometric_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/biometric/verify', type='json', auth='user', methods=['POST'])
    def verify_biometric_data(self, **kwargs):
        """Vérifie une donnée biométrique contre la base de données"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            required_fields = ['biometric_type', 'biometric_data']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'status': 'error',
                        'message': _('Le champ %s est obligatoire') % field
                    }

            biometric_type = data['biometric_type']
            biometric_data = data['biometric_data']

            # Rechercher des correspondances actives
            active_records = request.env['edu.biometric.data'].search([
                ('biometric_type', '=', biometric_type),
                ('state', '=', 'active'),
                ('active', '=', True)
            ])

            # Pour la démonstration, on fait une comparaison simple
            # Dans un vrai système, on utiliserait des algorithmes de correspondance biométrique
            matches = []
            for record in active_records:
                if self._compare_biometric_data(biometric_data, record.biometric_data, biometric_type):
                    matches.append({
                        'person': {
                            'id': record.partner_id.id,
                            'name': record.partner_id.name,
                            'email': record.partner_id.email
                        },
                        'biometric_id': record.id,
                        'confidence': 95.0  # Score de confiance simulé
                    })

            # Log de sécurité pour tentative de vérification
            self._log_biometric_verification(biometric_type, len(matches) > 0, data.get('source', 'api'))

            return {
                'status': 'success',
                'data': {
                    'verified': len(matches) > 0,
                    'matches': matches,
                    'match_count': len(matches),
                    'biometric_type': biometric_type
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la vérification biométrique: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/biometric/statistics', type='json', auth='user', methods=['GET'])
    def get_biometric_statistics(self, **kwargs):
        """Récupère les statistiques des données biométriques"""
        try:
            # Statistiques par type
            stats_by_type = {}
            for btype, label in request.env['edu.biometric.data']._fields['biometric_type'].selection:
                total = request.env['edu.biometric.data'].search_count([('biometric_type', '=', btype)])
                active = request.env['edu.biometric.data'].search_count([
                    ('biometric_type', '=', btype), 
                    ('state', '=', 'active')
                ])
                stats_by_type[btype] = {
                    'label': label,
                    'total': total,
                    'active': active,
                    'inactive': total - active
                }

            # Statistiques par état
            stats_by_state = {}
            for state, label in request.env['edu.biometric.data']._fields['state'].selection:
                count = request.env['edu.biometric.data'].search_count([('state', '=', state)])
                stats_by_state[state] = {
                    'label': label,
                    'count': count
                }

            # Statistiques générales
            total_records = request.env['edu.biometric.data'].search_count([])
            total_persons = request.env['edu.biometric.data'].search_count([('partner_id', '!=', False)])
            unique_persons = len(request.env['edu.biometric.data'].search([]).mapped('partner_id'))

            return {
                'status': 'success',
                'data': {
                    'total_records': total_records,
                    'total_persons_with_biometric': unique_persons,
                    'by_type': stats_by_type,
                    'by_state': stats_by_state,
                    'coverage': {
                        'persons_with_data': unique_persons,
                        'total_persons': total_persons
                    }
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des statistiques biométriques: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/biometric/options', type='json', auth='user', methods=['GET'])
    def get_biometric_options(self, **kwargs):
        """Récupère les options disponibles pour les données biométriques"""
        try:
            biometric_types = request.env['edu.biometric.data']._fields['biometric_type'].selection
            states = request.env['edu.biometric.data']._fields['state'].selection
            
            return {
                'status': 'success',
                'data': {
                    'biometric_types': [{'value': value, 'label': label} for value, label in biometric_types],
                    'states': [{'value': value, 'label': label} for value, label in states]
                }
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des options biométriques: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _format_biometric_data(self, record, detailed=False):
        """Formate les données biométriques pour l'API (sans exposer les données sensibles)"""
        data = {
            'id': record.id,
            'name': record.name,
            'person': {
                'id': record.partner_id.id,
                'name': record.partner_id.name,
                'email': record.partner_id.email
            },
            'biometric_type': record.biometric_type,
            'state': record.state,
            'active': record.active,
            'create_date': record.create_date.isoformat() if record.create_date else None
        }

        if detailed:
            data.update({
                'has_data': bool(record.biometric_data),
                'data_size': len(record.biometric_data) if record.biometric_data else 0,
                'write_date': record.write_date.isoformat() if record.write_date else None,
                'write_uid': {
                    'id': record.write_uid.id if record.write_uid else None,
                    'name': record.write_uid.name if record.write_uid else None
                }
            })

        return data

    def _prepare_biometric_data(self, data):
        """Prépare les données pour la création/mise à jour"""
        allowed_fields = ['name', 'partner_id', 'biometric_type', 'biometric_data', 'state', 'active']
        
        biometric_data = {}
        for field in allowed_fields:
            if field in data:
                biometric_data[field] = data[field]
        
        return biometric_data

    def _compare_biometric_data(self, data1, data2, biometric_type):
        """Compare deux données biométriques (implémentation simplifiée)"""
        try:
            # Dans un vrai système, on utiliserait des algorithmes spécialisés
            # Pour la démonstration, on fait une comparaison simple
            if biometric_type == 'fingerprint':
                # Simulation de comparaison d'empreintes
                return self._simple_hash_compare(data1, data2)
            elif biometric_type == 'face':
                # Simulation de reconnaissance faciale
                return self._simple_hash_compare(data1, data2)
            elif biometric_type == 'iris':
                # Simulation de reconnaissance iris
                return self._simple_hash_compare(data1, data2)
            
            return False
        except Exception as e:
            _logger.error(f"Erreur lors de la comparaison biométrique: {e}")
            return False

    def _simple_hash_compare(self, data1, data2):
        """Comparaison simple par hash (pour démonstration uniquement)"""
        try:
            # Convertir en bytes si nécessaire
            if isinstance(data1, str):
                data1 = base64.b64decode(data1)
            if isinstance(data2, bytes):
                data2_decoded = data2
            else:
                data2_decoded = base64.b64decode(data2) if isinstance(data2, str) else data2

            # Comparaison par hash MD5 (uniquement pour démonstration)
            hash1 = hashlib.md5(data1).hexdigest()
            hash2 = hashlib.md5(data2_decoded).hexdigest()
            
            return hash1 == hash2
        except Exception:
            return False

    def _log_biometric_action(self, action, record, source='api', extra_info=''):
        """Log des actions sur les données biométriques pour audit de sécurité"""
        try:
            log_message = f"Biometric {action}: {record.biometric_type} for {record.partner_id.name} (ID: {record.id}) via {source}"
            if extra_info:
                log_message += f" - {extra_info}"
            
            _logger.info(log_message)
            
            # Optionnel: Créer un enregistrement d'audit dans une table dédiée
            # request.env['edu.biometric.audit'].sudo().create({
            #     'action': action,
            #     'biometric_id': record.id,
            #     'user_id': request.env.user.id,
            #     'source': source,
            #     'details': extra_info,
            #     'timestamp': fields.Datetime.now()
            # })
            
        except Exception as e:
            _logger.error(f"Erreur lors du logging biométrique: {e}")

    def _log_biometric_verification(self, biometric_type, success, source='api'):
        """Log des tentatives de vérification biométrique"""
        try:
            result = "SUCCESS" if success else "FAILED"
            log_message = f"Biometric verification {result}: {biometric_type} via {source} by user {request.env.user.name}"
            _logger.info(log_message)
        except Exception as e:
            _logger.error(f"Erreur lors du logging de vérification: {e}")


class EduBiometricDataPublicController(http.Controller):
    """Contrôleur API public pour les données biométriques (accès très limité)"""

    @http.route('/api/public/biometric/verify', type='json', auth='public', methods=['POST'])
    def public_verify_biometric(self, **kwargs):
        """Endpoint public pour vérification biométrique (avec authentification par token)"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Vérification du token d'authentification
            if not data.get('auth_token'):
                return {
                    'status': 'error',
                    'message': _('Token d\'authentification requis')
                }

            # Valider le token (à implémenter selon votre système de sécurité)
            if not self._validate_auth_token(data['auth_token']):
                return {
                    'status': 'error',
                    'message': _('Token d\'authentification invalide')
                }

            # Validation des données biométriques
            if not data.get('biometric_type') or not data.get('biometric_data'):
                return {
                    'status': 'error',
                    'message': _('Type et données biométriques requis')
                }

            # Utiliser sudo pour accéder aux données avec permissions élevées
            controller = EduBiometricDataController()
            
            # Effectuer la vérification
            result = controller.verify_biometric_data(**{'json_data': {
                'biometric_type': data['biometric_type'],
                'biometric_data': data['biometric_data'],
                'source': 'public_api'
            }})

            # Limiter les informations retournées en mode public
            if result['status'] == 'success':
                return {
                    'status': 'success',
                    'data': {
                        'verified': result['data']['verified'],
                        'match_count': result['data']['match_count'],
                        'person_id': result['data']['matches'][0]['person']['id'] if result['data']['matches'] else None
                    }
                }
            else:
                return result

        except Exception as e:
            _logger.error(f"Erreur lors de la vérification biométrique publique: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la vérification')
            }

    def _validate_auth_token(self, token):
        """Valide le token d'authentification pour l'API publique"""
        try:
            # Implémentation de validation de token à personnaliser
            # Exemple simple: vérifier contre une liste de tokens valides
            valid_tokens = request.env['ir.config_parameter'].sudo().get_param('biometric.api.tokens', '').split(',')
            return token.strip() in [t.strip() for t in valid_tokens if t.strip()]
        except Exception:
            return False