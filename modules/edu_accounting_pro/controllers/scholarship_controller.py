# -*- coding: utf-8 -*-

import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)


class EduScholarshipController(http.Controller):
    """Controller pour la gestion des bourses d'études"""

    @http.route('/api/scholarships', type='json', auth='user', methods=['POST'], csrf=False)
    def get_scholarships(self, **kwargs):
        """Récupère la liste des bourses d'études"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
            if kwargs.get('scholarship_type'):
                domain.append(('scholarship_type', '=', kwargs['scholarship_type']))
            if kwargs.get('academic_year_id'):
                domain.append(('academic_year_id', '=', kwargs['academic_year_id']))
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            
            # Recherche par nom
            if kwargs.get('search'):
                domain.append(('name', 'ilike', kwargs['search']))
            
            # Pagination
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            scholarships = request.env['edu.scholarship'].search(domain, limit=limit, offset=offset)
            
            result = []
            for scholarship in scholarships:
                result.append({
                    'id': scholarship.id,
                    'name': scholarship.name,
                    'code': scholarship.code if hasattr(scholarship, 'code') else '',
                    'description': scholarship.description if hasattr(scholarship, 'description') else '',
                    'scholarship_type': scholarship.scholarship_type if hasattr(scholarship, 'scholarship_type') else '',
                    'scholarship_type_display': dict(scholarship._fields['scholarship_type'].selection).get(scholarship.scholarship_type, '') if hasattr(scholarship, 'scholarship_type') else '',
                    'academic_year_id': scholarship.academic_year_id.id if hasattr(scholarship, 'academic_year_id') and scholarship.academic_year_id else None,
                    'academic_year_name': scholarship.academic_year_id.name if hasattr(scholarship, 'academic_year_id') and scholarship.academic_year_id else '',
                    'amount': scholarship.amount if hasattr(scholarship, 'amount') else 0,
                    'percentage': scholarship.percentage if hasattr(scholarship, 'percentage') else 0,
                    'max_recipients': scholarship.max_recipients if hasattr(scholarship, 'max_recipients') else 0,
                    'current_recipients': scholarship.current_recipients if hasattr(scholarship, 'current_recipients') else 0,
                    'start_date': scholarship.start_date.isoformat() if hasattr(scholarship, 'start_date') and scholarship.start_date else None,
                    'end_date': scholarship.end_date.isoformat() if hasattr(scholarship, 'end_date') and scholarship.end_date else None,
                    'state': scholarship.state if hasattr(scholarship, 'state') else 'draft',
                    'state_display': dict(scholarship._fields['state'].selection).get(scholarship.state, '') if hasattr(scholarship, 'state') else '',
                    'active': scholarship.active if hasattr(scholarship, 'active') else True,
                    'currency_symbol': scholarship.currency_id.symbol if hasattr(scholarship, 'currency_id') and scholarship.currency_id else '',
                })
            
            total_count = request.env['edu.scholarship'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des bourses: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/scholarships/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_scholarship(self, **kwargs):
        """Récupère une bourse d'études spécifique"""
        try:
            scholarship_id = kwargs.get('scholarship_id')
            if not scholarship_id:
                return {'success': False, 'error': 'ID de bourse requis'}
            
            scholarship = request.env['edu.scholarship'].browse(scholarship_id)
            
            if not scholarship.exists():
                return {'success': False, 'error': 'Bourse non trouvée'}
            
            # Récupération des bénéficiaires si disponible
            recipients = []
            if hasattr(scholarship, 'recipient_ids'):
                for recipient in scholarship.recipient_ids:
                    recipients.append({
                        'id': recipient.id,
                        'student_id': recipient.student_id.id if hasattr(recipient, 'student_id') and recipient.student_id else None,
                        'student_name': recipient.student_id.name if hasattr(recipient, 'student_id') and recipient.student_id else '',
                        'amount_awarded': recipient.amount_awarded if hasattr(recipient, 'amount_awarded') else 0,
                        'date_awarded': recipient.date_awarded.isoformat() if hasattr(recipient, 'date_awarded') and recipient.date_awarded else None,
                        'status': recipient.status if hasattr(recipient, 'status') else 'active',
                    })
            
            data = {
                'id': scholarship.id,
                'name': scholarship.name,
                'code': scholarship.code if hasattr(scholarship, 'code') else '',
                'description': scholarship.description if hasattr(scholarship, 'description') else '',
                'scholarship_type': scholarship.scholarship_type if hasattr(scholarship, 'scholarship_type') else '',
                'academic_year_id': scholarship.academic_year_id.id if hasattr(scholarship, 'academic_year_id') and scholarship.academic_year_id else None,
                'academic_year_name': scholarship.academic_year_id.name if hasattr(scholarship, 'academic_year_id') and scholarship.academic_year_id else '',
                'amount': scholarship.amount if hasattr(scholarship, 'amount') else 0,
                'percentage': scholarship.percentage if hasattr(scholarship, 'percentage') else 0,
                'max_recipients': scholarship.max_recipients if hasattr(scholarship, 'max_recipients') else 0,
                'current_recipients': scholarship.current_recipients if hasattr(scholarship, 'current_recipients') else 0,
                'start_date': scholarship.start_date.isoformat() if hasattr(scholarship, 'start_date') and scholarship.start_date else None,
                'end_date': scholarship.end_date.isoformat() if hasattr(scholarship, 'end_date') and scholarship.end_date else None,
                'criteria': scholarship.criteria if hasattr(scholarship, 'criteria') else '',
                'terms_conditions': scholarship.terms_conditions if hasattr(scholarship, 'terms_conditions') else '',
                'renewable': scholarship.renewable if hasattr(scholarship, 'renewable') else False,
                'renewal_criteria': scholarship.renewal_criteria if hasattr(scholarship, 'renewal_criteria') else '',
                'state': scholarship.state if hasattr(scholarship, 'state') else 'draft',
                'active': scholarship.active if hasattr(scholarship, 'active') else True,
                'currency_id': scholarship.currency_id.id if hasattr(scholarship, 'currency_id') and scholarship.currency_id else None,
                'currency_symbol': scholarship.currency_id.symbol if hasattr(scholarship, 'currency_id') and scholarship.currency_id else '',
                'recipients': recipients,
                'total_awarded': sum(r['amount_awarded'] for r in recipients),
                'remaining_slots': (scholarship.max_recipients - scholarship.current_recipients) if hasattr(scholarship, 'max_recipients') and hasattr(scholarship, 'current_recipients') else 0,
            }
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la bourse: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/scholarships/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_scholarship(self, **kwargs):
        """Crée une nouvelle bourse d'études"""
        try:
            # Validation des champs requis
            required_fields = ['name']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Champ requis manquant: {field}'}
            
            # Préparation des données
            vals = {
                'name': kwargs['name'],
            }
            
            # Champs optionnels
            optional_fields = [
                'code', 'description', 'scholarship_type', 'academic_year_id',
                'amount', 'percentage', 'max_recipients', 'start_date', 'end_date',
                'criteria', 'terms_conditions', 'renewable', 'renewal_criteria',
                'currency_id', 'active'
            ]
            
            for field in optional_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Validation de cohérence
            if vals.get('amount') and vals.get('percentage'):
                return {'success': False, 'error': 'Spécifiez soit un montant fixe, soit un pourcentage, pas les deux'}
            
            if vals.get('end_date') and vals.get('start_date'):
                if vals['end_date'] < vals['start_date']:
                    return {'success': False, 'error': 'La date de fin doit être postérieure à la date de début'}
            
            # Création de la bourse
            scholarship = request.env['edu.scholarship'].create(vals)
            
            return {
                'success': True,
                'data': {
                    'id': scholarship.id,
                    'name': scholarship.name,
                    'code': scholarship.code if hasattr(scholarship, 'code') else ''
                },
                'message': 'Bourse créée avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la création de la bourse: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/scholarships/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_scholarship(self, **kwargs):
        """Met à jour une bourse d'études"""
        try:
            scholarship_id = kwargs.get('scholarship_id')
            if not scholarship_id:
                return {'success': False, 'error': 'ID de bourse requis'}
            
            scholarship = request.env['edu.scholarship'].browse(scholarship_id)
            
            if not scholarship.exists():
                return {'success': False, 'error': 'Bourse non trouvée'}
            
            # Préparation des données à mettre à jour
            vals = {}
            updatable_fields = [
                'name', 'code', 'description', 'scholarship_type', 'academic_year_id',
                'amount', 'percentage', 'max_recipients', 'start_date', 'end_date',
                'criteria', 'terms_conditions', 'renewable', 'renewal_criteria',
                'active'
            ]
            
            for field in updatable_fields:
                if kwargs.get(field) is not None:
                    vals[field] = kwargs[field]
            
            # Validation de cohérence
            final_amount = vals.get('amount', scholarship.amount if hasattr(scholarship, 'amount') else None)
            final_percentage = vals.get('percentage', scholarship.percentage if hasattr(scholarship, 'percentage') else None)
            
            if final_amount and final_percentage:
                return {'success': False, 'error': 'Spécifiez soit un montant fixe, soit un pourcentage, pas les deux'}
            
            # Mise à jour
            scholarship.write(vals)
            
            return {
                'success': True,
                'message': 'Bourse mise à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/scholarships/activate', type='json', auth='user', methods=['POST'], csrf=False)
    def activate_scholarship(self, **kwargs):
        """Active une bourse d'études"""
        try:
            scholarship_id = kwargs.get('scholarship_id')
            if not scholarship_id:
                return {'success': False, 'error': 'ID de bourse requis'}
            
            scholarship = request.env['edu.scholarship'].browse(scholarship_id)
            
            if not scholarship.exists():
                return {'success': False, 'error': 'Bourse non trouvée'}
            
            # Activation de la bourse
            if hasattr(scholarship, 'action_activate'):
                scholarship.action_activate()
            else:
                scholarship.write({'state': 'active'})
            
            return {
                'success': True,
                'message': f'Bourse "{scholarship.name}" activée avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'activation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/scholarships/applications', type='json', auth='user', methods=['POST'], csrf=False)
    def get_scholarship_applications(self, **kwargs):
        """Récupère les candidatures pour les bourses"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('scholarship_id'):
                domain.append(('scholarship_id', '=', kwargs['scholarship_id']))
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', kwargs['student_id']))
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            
            # Pagination
            limit = kwargs.get('limit', 20)
            offset = kwargs.get('offset', 0)
            
            applications = request.env['edu.scholarship.application'].search(domain, limit=limit, offset=offset)
            
            result = []
            for application in applications:
                result.append({
                    'id': application.id,
                    'reference': application.reference if hasattr(application, 'reference') else '',
                    'scholarship_id': application.scholarship_id.id if hasattr(application, 'scholarship_id') and application.scholarship_id else None,
                    'scholarship_name': application.scholarship_id.name if hasattr(application, 'scholarship_id') and application.scholarship_id else '',
                    'student_id': application.student_id.id if hasattr(application, 'student_id') and application.student_id else None,
                    'student_name': application.student_id.name if hasattr(application, 'student_id') and application.student_id else '',
                    'application_date': application.application_date.isoformat() if hasattr(application, 'application_date') and application.application_date else None,
                    'state': application.state if hasattr(application, 'state') else 'draft',
                    'state_display': dict(application._fields['state'].selection).get(application.state, '') if hasattr(application, 'state') else '',
                    'score': application.score if hasattr(application, 'score') else 0,
                    'amount_requested': application.amount_requested if hasattr(application, 'amount_requested') else 0,
                    'amount_approved': application.amount_approved if hasattr(application, 'amount_approved') else 0,
                })
            
            total_count = request.env['edu.scholarship.application'].search_count(domain)
            
            return {
                'success': True,
                'data': result,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des candidatures: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
