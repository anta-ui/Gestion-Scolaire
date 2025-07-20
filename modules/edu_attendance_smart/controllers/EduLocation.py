# -*- coding: utf-8 -*-

import json
import logging
import math
from datetime import datetime, timedelta
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError, UserError
from odoo.http import serialize_exception

_logger = logging.getLogger(__name__)


class EduLocationController(http.Controller):
    """Contrôleur API pour la gestion des emplacements"""

    @http.route('/api/locations', type='json', auth='user', methods=['GET'])
    def get_locations(self, **kwargs):
        """Récupère tous les emplacements"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('location_type'):
                domain.append(('location_type', '=', kwargs['location_type']))
            
            if kwargs.get('building'):
                domain.append(('building', 'ilike', kwargs['building']))
                
            if kwargs.get('floor'):
                domain.append(('floor', '=', kwargs['floor']))
                
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
                
            if kwargs.get('has_gps'):
                if kwargs['has_gps']:
                    domain.extend([('latitude', '!=', False), ('longitude', '!=', False)])
                else:
                    domain.append('|')
                    domain.extend([('latitude', '=', False), ('longitude', '=', False)])
                    
            if kwargs.get('min_capacity'):
                domain.append(('capacity', '>=', kwargs['min_capacity']))
                
            if kwargs.get('max_capacity'):
                domain.append(('capacity', '<=', kwargs['max_capacity']))

            # Pagination
            limit = kwargs.get('limit', 100)
            offset = kwargs.get('offset', 0)
            
            locations = request.env['edu.location'].search(
                domain, 
                limit=limit, 
                offset=offset,
                order='name asc, code asc'
            )
            
            total_count = request.env['edu.location'].search_count(domain)
            
            return {
                'status': 'success',
                'data': [self._format_location(location) for location in locations],
                'count': len(locations),
                'total_count': total_count
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des emplacements: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations/<int:location_id>', type='json', auth='user', methods=['GET'])
    def get_location(self, location_id, **kwargs):
        """Récupère un emplacement spécifique"""
        try:
            location = request.env['edu.location'].browse(location_id)
            if not location.exists():
                return {
                    'status': 'error',
                    'message': _('Emplacement non trouvé')
                }
            
            return {
                'status': 'success',
                'data': self._format_location(location, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de l'emplacement {location_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations/by-code/<string:code>', type='json', auth='user', methods=['GET'])
    def get_location_by_code(self, code, **kwargs):
        """Récupère un emplacement par son code"""
        try:
            location = request.env['edu.location'].search([('code', '=', code)], limit=1)
            if not location:
                return {
                    'status': 'error',
                    'message': _('Emplacement non trouvé ou inactif')
                }

            # Retourner uniquement les données publiques
            return {
                'status': 'success',
                'data': {
                    'name': location.name,
                    'code': location.code,
                    'location_type': location.location_type,
                    'building': location.building,
                    'floor': location.floor,
                    'room_number': location.room_number,
                    'capacity': location.capacity,
                    'coordinates': {
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'gps_radius': location.gps_radius
                    } if location.latitude and location.longitude else None,
                    'has_devices': len(location.device_ids) > 0
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des infos publiques de l'emplacement {code}: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la récupération des informations')
            }

    @http.route('/api/public/locations/nearby', type='json', auth='public', methods=['POST'])
    def get_public_nearby_locations(self, **kwargs):
        """Trouve les emplacements publics à proximité d'une position GPS"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des paramètres obligatoires
            if not data.get('latitude') or not data.get('longitude'):
                return {
                    'status': 'error',
                    'message': _('Latitude et longitude requises')
                }

            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
            max_distance = float(data.get('max_distance', 500))  # Distance max en mètres
            
            # Validation des coordonnées
            controller = EduLocationController()
            if not controller._validate_gps_coordinates(latitude, longitude):
                return {
                    'status': 'error',
                    'message': _('Coordonnées GPS invalides')
                }

            # Limiter la distance de recherche pour l'API publique
            if max_distance > 2000:  # 2km max
                max_distance = 2000

            # Rechercher les emplacements avec coordonnées GPS
            locations_with_gps = request.env['edu.location'].sudo().search([
                ('latitude', '!=', False),
                ('longitude', '!=', False),
                ('active', '=', True)
            ])

            nearby_locations = []
            for location in locations_with_gps:
                distance = controller._calculate_distance(
                    latitude, longitude, 
                    location.latitude, location.longitude
                )
                
                if distance <= max_distance:
                    nearby_locations.append({
                        'code': location.code,
                        'name': location.name,
                        'location_type': location.location_type,
                        'building': location.building,
                        'distance': round(distance, 2),
                        'within_radius': distance <= location.gps_radius
                    })

            # Trier par distance et limiter à 10 résultats
            nearby_locations.sort(key=lambda x: x['distance'])
            nearby_locations = nearby_locations[:10]

            return {
                'status': 'success',
                'data': {
                    'max_distance': max_distance,
                    'locations': nearby_locations,
                    'count': len(nearby_locations)
                }
            }

        except ValueError as e:
            return {
                'status': 'error',
                'message': _('Valeurs numériques invalides')
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la recherche d'emplacements publics à proximité: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la recherche')
            }

    @http.route('/api/public/locations/validate-access', type='json', auth='public', methods=['POST'])
    def validate_location_access(self, **kwargs):
        """Valide l'accès à un emplacement depuis une position GPS"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            required_fields = ['location_code', 'latitude', 'longitude']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'status': 'error',
                        'message': _('Le champ %s est requis') % field
                    }

            location = request.env['edu.location'].sudo().search([
                ('code', '=', data['location_code']),
                ('active', '=', True)
            ], limit=1)

            if not location:
                return {
                    'status': 'error',
                    'message': _('Emplacement non trouvé')
                }

            if not location.latitude or not location.longitude:
                return {
                    'status': 'error',
                    'message': _('Emplacement sans coordonnées GPS')
                }

            user_lat = float(data['latitude'])
            user_lng = float(data['longitude'])

            # Validation des coordonnées
            controller = EduLocationController()
            if not controller._validate_gps_coordinates(user_lat, user_lng):
                return {
                    'status': 'error',
                    'message': _('Coordonnées GPS invalides')
                }

            # Calculer la distance
            distance = controller._calculate_distance(
                user_lat, user_lng,
                location.latitude, location.longitude
            )

            within_radius = distance <= location.gps_radius

            return {
                'status': 'success',
                'data': {
                    'location_name': location.name,
                    'location_code': location.code,
                    'distance': round(distance, 2),
                    'gps_radius': location.gps_radius,
                    'within_radius': within_radius,
                    'access_granted': within_radius
                }
            }

        except ValueError as e:
            return {
                'status': 'error',
                'message': _('Valeurs numériques invalides')
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la validation d'accès public: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la validation')
            }
            
            return {
                'status': 'success',
                'data': self._format_location(location, detailed=True)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de l'emplacement {code}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations', type='json', auth='user', methods=['POST'])
    def create_location(self, **kwargs):
        """Crée un nouvel emplacement"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des données obligatoires
            required_fields = ['name', 'code', 'location_type']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'status': 'error',
                        'message': _('Le champ %s est obligatoire') % field
                    }

            # Vérifier l'unicité du code
            existing = request.env['edu.location'].search([('code', '=', data['code'])])
            if existing:
                return {
                    'status': 'error',
                    'message': _('Le code %s existe déjà') % data['code']
                }

            # Validation des coordonnées GPS si fournies
            if data.get('latitude') is not None or data.get('longitude') is not None:
                if not self._validate_gps_coordinates(data.get('latitude'), data.get('longitude')):
                    return {
                        'status': 'error',
                        'message': _('Coordonnées GPS invalides')
                    }

            # Préparation des données
            location_data = self._prepare_location_data(data)
            location = request.env['edu.location'].create(location_data)

            return {
                'status': 'success',
                'data': self._format_location(location, detailed=True),
                'message': _('Emplacement créé avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la création de l'emplacement: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations/<int:location_id>', type='json', auth='user', methods=['PUT'])
    def update_location(self, location_id, **kwargs):
        """Met à jour un emplacement existant"""
        try:
            location = request.env['edu.location'].browse(location_id)
            if not location.exists():
                return {
                    'status': 'error',
                    'message': _('Emplacement non trouvé')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Vérifier l'unicité du code si modifié
            if 'code' in data and data['code'] != location.code:
                existing = request.env['edu.location'].search([
                    ('code', '=', data['code']),
                    ('id', '!=', location_id)
                ])
                if existing:
                    return {
                        'status': 'error',
                        'message': _('Le code %s existe déjà') % data['code']
                    }

            # Validation des coordonnées GPS si modifiées
            if 'latitude' in data or 'longitude' in data:
                new_lat = data.get('latitude', location.latitude)
                new_lng = data.get('longitude', location.longitude)
                if not self._validate_gps_coordinates(new_lat, new_lng):
                    return {
                        'status': 'error',
                        'message': _('Coordonnées GPS invalides')
                    }

            # Préparation des données
            location_data = self._prepare_location_data(data)
            location.write(location_data)

            return {
                'status': 'success',
                'data': self._format_location(location, detailed=True),
                'message': _('Emplacement mis à jour avec succès')
            }

        except ValidationError as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour de l'emplacement {location_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations/<int:location_id>', type='json', auth='user', methods=['DELETE'])
    def delete_location(self, location_id, **kwargs):
        """Supprime un emplacement"""
        try:
            location = request.env['edu.location'].browse(location_id)
            if not location.exists():
                return {
                    'status': 'error',
                    'message': _('Emplacement non trouvé')
                }

            # Vérifier s'il y a des dispositifs liés
            if location.device_ids:
                return {
                    'status': 'error',
                    'message': _('Impossible de supprimer un emplacement ayant des dispositifs associés')
                }

            # Vérifier s'il y a des sessions liées
            sessions_count = request.env['edu.attendance.session'].search_count([
                ('location_id', '=', location_id)
            ])
            
            if sessions_count > 0:
                return {
                    'status': 'error',
                    'message': _('Impossible de supprimer un emplacement ayant des sessions associées')
                }

            location.unlink()

            return {
                'status': 'success',
                'message': _('Emplacement supprimé avec succès')
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la suppression de l'emplacement {location_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations/<int:location_id>/devices', type='json', auth='user', methods=['GET'])
    def get_location_devices(self, location_id, **kwargs):
        """Récupère les dispositifs d'un emplacement"""
        try:
            location = request.env['edu.location'].browse(location_id)
            if not location.exists():
                return {
                    'status': 'error',
                    'message': _('Emplacement non trouvé')
                }

            devices = []
            for device in location.device_ids:
                devices.append({
                    'id': device.id,
                    'name': device.name,
                    'code': device.code,
                    'device_type': device.device_type,
                    'active': device.active,
                    'online': device.online if hasattr(device, 'online') else False,
                    'last_ping': device.last_ping.isoformat() if hasattr(device, 'last_ping') and device.last_ping else None
                })

            return {
                'status': 'success',
                'data': {
                    'location': {
                        'id': location.id,
                        'name': location.name,
                        'code': location.code
                    },
                    'devices': devices,
                    'device_count': len(devices)
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des dispositifs de l'emplacement {location_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations/nearby', type='json', auth='user', methods=['POST'])
    def get_nearby_locations(self, **kwargs):
        """Trouve les emplacements à proximité d'une position GPS"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            # Validation des paramètres obligatoires
            if not data.get('latitude') or not data.get('longitude'):
                return {
                    'status': 'error',
                    'message': _('Latitude et longitude requises')
                }

            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
            max_distance = float(data.get('max_distance', 1000))  # Distance max en mètres
            
            # Validation des coordonnées
            if not self._validate_gps_coordinates(latitude, longitude):
                return {
                    'status': 'error',
                    'message': _('Coordonnées GPS invalides')
                }

            # Rechercher les emplacements avec coordonnées GPS
            locations_with_gps = request.env['edu.location'].search([
                ('latitude', '!=', False),
                ('longitude', '!=', False),
                ('active', '=', True)
            ])

            nearby_locations = []
            for location in locations_with_gps:
                distance = self._calculate_distance(
                    latitude, longitude, 
                    location.latitude, location.longitude
                )
                
                if distance <= max_distance:
                    location_data = self._format_location(location)
                    location_data['distance'] = round(distance, 2)
                    location_data['within_radius'] = distance <= location.gps_radius
                    nearby_locations.append(location_data)

            # Trier par distance
            nearby_locations.sort(key=lambda x: x['distance'])

            return {
                'status': 'success',
                'data': {
                    'search_coordinates': {
                        'latitude': latitude,
                        'longitude': longitude
                    },
                    'max_distance': max_distance,
                    'locations': nearby_locations,
                    'count': len(nearby_locations)
                }
            }

        except ValueError as e:
            return {
                'status': 'error',
                'message': _('Valeurs numériques invalides')
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la recherche d'emplacements à proximité: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations/<int:location_id>/check-proximity', type='json', auth='user', methods=['POST'])
    def check_location_proximity(self, location_id, **kwargs):
        """Vérifie si une position est dans le rayon d'un emplacement"""
        try:
            location = request.env['edu.location'].browse(location_id)
            if not location.exists():
                return {
                    'status': 'error',
                    'message': _('Emplacement non trouvé')
                }

            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Données manquantes')
                }

            if not data.get('latitude') or not data.get('longitude'):
                return {
                    'status': 'error',
                    'message': _('Latitude et longitude requises')
                }

            if not location.latitude or not location.longitude:
                return {
                    'status': 'error',
                    'message': _('Emplacement sans coordonnées GPS')
                }

            user_lat = float(data['latitude'])
            user_lng = float(data['longitude'])

            # Validation des coordonnées
            if not self._validate_gps_coordinates(user_lat, user_lng):
                return {
                    'status': 'error',
                    'message': _('Coordonnées GPS invalides')
                }

            # Calculer la distance
            distance = self._calculate_distance(
                user_lat, user_lng,
                location.latitude, location.longitude
            )

            within_radius = distance <= location.gps_radius

            return {
                'status': 'success',
                'data': {
                    'location': {
                        'id': location.id,
                        'name': location.name,
                        'code': location.code
                    },
                    'user_coordinates': {
                        'latitude': user_lat,
                        'longitude': user_lng
                    },
                    'location_coordinates': {
                        'latitude': location.latitude,
                        'longitude': location.longitude
                    },
                    'distance': round(distance, 2),
                    'gps_radius': location.gps_radius,
                    'within_radius': within_radius,
                    'access_granted': within_radius
                }
            }

        except ValueError as e:
            return {
                'status': 'error',
                'message': _('Valeurs numériques invalides')
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la vérification de proximité {location_id}: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations/buildings', type='json', auth='user', methods=['GET'])
    def get_buildings(self, **kwargs):
        """Récupère la liste des bâtiments"""
        try:
            # Récupérer tous les bâtiments distincts
            locations = request.env['edu.location'].search([
                ('building', '!=', False),
                ('active', '=', True)
            ])
            
            buildings = {}
            for location in locations:
                building = location.building
                if building not in buildings:
                    buildings[building] = {
                        'name': building,
                        'location_count': 0,
                        'floors': set(),
                        'types': set()
                    }
                
                buildings[building]['location_count'] += 1
                if location.floor:
                    buildings[building]['floors'].add(location.floor)
                buildings[building]['types'].add(location.location_type)

            # Convertir les sets en listes pour la sérialisation JSON
            for building_name, building_data in buildings.items():
                building_data['floors'] = sorted(list(building_data['floors']))
                building_data['types'] = list(building_data['types'])

            return {
                'status': 'success',
                'data': list(buildings.values()),
                'count': len(buildings)
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des bâtiments: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations/search', type='json', auth='user', methods=['POST'])
    def search_locations(self, **kwargs):
        """Recherche avancée d'emplacements"""
        try:
            data = request.get_json_data()
            if not data:
                return {
                    'status': 'error',
                    'message': _('Critères de recherche manquants')
                }

            domain = []
            
            # Recherche par texte
            if data.get('search_term'):
                term = data['search_term']
                domain.append('|')
                domain.append('|')
                domain.append('|')
                domain.append(('name', 'ilike', term))
                domain.append(('code', 'ilike', term))
                domain.append(('description', 'ilike', term))
                domain.append(('building', 'ilike', term))

            # Filtres multiples
            if data.get('location_types'):
                domain.append(('location_type', 'in', data['location_types']))
                
            if data.get('buildings'):
                domain.append(('building', 'in', data['buildings']))
                
            if data.get('floors'):
                domain.append(('floor', 'in', data['floors']))

            # Filtres de capacité
            if data.get('min_capacity'):
                domain.append(('capacity', '>=', data['min_capacity']))
            if data.get('max_capacity'):
                domain.append(('capacity', '<=', data['max_capacity']))

            # Filtre GPS
            if data.get('has_gps'):
                domain.extend([('latitude', '!=', False), ('longitude', '!=', False)])

            # Filtre actif
            if data.get('active_only', True):
                domain.append(('active', '=', True))

            limit = data.get('limit', 50)
            locations = request.env['edu.location'].search(domain, limit=limit)

            return {
                'status': 'success',
                'data': [self._format_location(location) for location in locations],
                'count': len(locations)
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la recherche d'emplacements: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations/statistics', type='json', auth='user', methods=['GET'])
    def get_location_statistics(self, **kwargs):
        """Récupère les statistiques des emplacements"""
        try:
            # Statistiques par type
            stats_by_type = {}
            for loc_type, label in request.env['edu.location']._fields['location_type'].selection:
                count = request.env['edu.location'].search_count([('location_type', '=', loc_type)])
                active_count = request.env['edu.location'].search_count([
                    ('location_type', '=', loc_type),
                    ('active', '=', True)
                ])
                stats_by_type[loc_type] = {
                    'label': label,
                    'total': count,
                    'active': active_count
                }

            # Statistiques par bâtiment
            buildings = request.env['edu.location'].read_group(
                [('building', '!=', False), ('active', '=', True)],
                ['building'], ['building']
            )
            
            stats_by_building = {}
            for building in buildings:
                building_name = building['building']
                stats_by_building[building_name] = building['building_count']

            # Statistiques générales
            total_locations = request.env['edu.location'].search_count([])
            active_locations = request.env['edu.location'].search_count([('active', '=', True)])
            locations_with_gps = request.env['edu.location'].search_count([
                ('latitude', '!=', False),
                ('longitude', '!=', False)
            ])
            locations_with_devices = request.env['edu.location'].search_count([
                ('device_ids', '!=', False)
            ])

            # Capacité totale
            all_locations = request.env['edu.location'].search([('active', '=', True)])
            total_capacity = sum(all_locations.mapped('capacity'))
            avg_capacity = total_capacity / len(all_locations) if all_locations else 0

            return {
                'status': 'success',
                'data': {
                    'summary': {
                        'total_locations': total_locations,
                        'active_locations': active_locations,
                        'locations_with_gps': locations_with_gps,
                        'locations_with_devices': locations_with_devices,
                        'total_capacity': total_capacity,
                        'average_capacity': round(avg_capacity, 1)
                    },
                    'by_type': stats_by_type,
                    'by_building': stats_by_building,
                    'gps_coverage': {
                        'with_gps': locations_with_gps,
                        'without_gps': active_locations - locations_with_gps,
                        'coverage_rate': (locations_with_gps / active_locations * 100) if active_locations else 0
                    }
                }
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/locations/options', type='json', auth='user', methods=['GET'])
    def get_location_options(self, **kwargs):
        """Récupère les options disponibles pour les emplacements"""
        try:
            location_types = request.env['edu.location']._fields['location_type'].selection
            
            return {
                'status': 'success',
                'data': {
                    'location_types': [{'value': value, 'label': label} for value, label in location_types]
                }
            }
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des options: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _format_location(self, location, detailed=False):
        """Formate les données de l'emplacement pour l'API"""
        data = {
            'id': location.id,
            'name': location.name,
            'code': location.code,
            'location_type': location.location_type,
            'building': location.building,
            'floor': location.floor,
            'room_number': location.room_number,
            'capacity': location.capacity,
            'active': location.active,
            'coordinates': {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'gps_radius': location.gps_radius
            } if location.latitude and location.longitude else None,
            'device_count': len(location.device_ids),
            'create_date': location.create_date.isoformat() if location.create_date else None
        }

        if detailed:
            data.update({
                'description': location.description,
                'devices': [
                    {
                        'id': device.id,
                        'name': device.name,
                        'code': device.code,
                        'device_type': device.device_type,
                        'active': device.active
                    } for device in location.device_ids
                ],
                'write_date': location.write_date.isoformat() if location.write_date else None,
                'write_uid': {
                    'id': location.write_uid.id if location.write_uid else None,
                    'name': location.write_uid.name if location.write_uid else None
                }
            })

        return data

    def _prepare_location_data(self, data):
        """Prépare les données pour la création/mise à jour"""
        allowed_fields = [
            'name', 'code', 'description', 'location_type', 'building', 'floor',
            'room_number', 'capacity', 'latitude', 'longitude', 'gps_radius', 'active'
        ]
        
        location_data = {}
        for field in allowed_fields:
            if field in data:
                location_data[field] = data[field]
        
        return location_data

    def _validate_gps_coordinates(self, latitude, longitude):
        """Valide les coordonnées GPS"""
        try:
            if latitude is None and longitude is None:
                return True  # Pas de coordonnées, c'est valide
            
            if latitude is None or longitude is None:
                return False  # Une seule coordonnée fournie
            
            lat = float(latitude)
            lng = float(longitude)
            
            return (-90 <= lat <= 90) and (-180 <= lng <= 180)
        except (ValueError, TypeError):
            return False

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calcule la distance entre deux points GPS en mètres (formule de Haversine)"""
        try:
            # Convertir en radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            
            # Formule de Haversine
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Rayon de la Terre en mètres
            r = 6371000
            
            return r * c
        except Exception:
            return float('inf')


class EduLocationPublicController(http.Controller):
    """Contrôleur API public pour les emplacements (accès limité)"""

    @http.route('/api/public/locations/active', type='json', auth='public', methods=['GET'])
    def get_public_active_locations(self, **kwargs):
        """Récupère les emplacements actifs (informations publiques)"""
        try:
            # Filtres optionnels
            domain = [('active', '=', True)]
            
            if kwargs.get('location_type'):
                domain.append(('location_type', '=', kwargs['location_type']))
                
            if kwargs.get('building'):
                domain.append(('building', '=', kwargs['building']))

            locations = request.env['edu.location'].sudo().search(
                domain, 
                limit=50,
                order='name asc'
            )

            public_locations = []
            for location in locations:
                public_locations.append({
                    'code': location.code,
                    'name': location.name,
                    'location_type': location.location_type,
                    'building': location.building,
                    'floor': location.floor,
                    'capacity': location.capacity,
                    'has_gps': bool(location.latitude and location.longitude)
                })

            return {
                'status': 'success',
                'data': public_locations,
                'count': len(public_locations)
            }

        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des emplacements publics: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la récupération des emplacements')
            }

    @http.route('/api/public/locations/<string:code>/info', type='json', auth='public', methods=['GET'])
    def get_public_location_info(self, code, **kwargs):
        """Récupère les informations publiques d'un emplacement"""
        try:
            location = request.env['edu.location'].sudo().search([
                ('code', '=', code),
                ('active', '=', True)
            ], limit=1)
            
            if not location:
                return {
                    'status': 'error',
                    'message': _('Emplacement non trouvé')
                }
            
            return {
                'status': 'success',
                'data': {
                    'id': location.id,
                    'name': location.name,
                    'code': location.code,
                    'description': location.description,
                    'capacity': location.capacity,
                    'location_type': location.location_type,
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des informations publiques: {e}")
            return {
                'status': 'error',
                'message': _('Erreur lors de la récupération des informations')
            }
