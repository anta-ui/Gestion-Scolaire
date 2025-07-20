# -*- coding: utf-8 -*-

import json
import logging
import base64
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError

_logger = logging.getLogger(__name__)

class StudentDocumentController(http.Controller):
    """API Controller pour StudentDocument"""

    @http.route('/api/student-documents', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_documents(self, **kwargs):
        """Récupérer la liste des documents d'élèves"""
        try:
            domain = []
            
            # Filtres optionnels
            if kwargs.get('student_id'):
                domain.append(('student_id', '=', int(kwargs['student_id'])))
            
            if kwargs.get('document_type_id'):
                domain.append(('document_type_id', '=', int(kwargs['document_type_id'])))
            
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            
            # Pagination
            limit = int(kwargs.get('limit', 20))
            offset = int(kwargs.get('offset', 0))
            
            documents = request.env['student.document'].search(domain, limit=limit, offset=offset)
            total_count = request.env['student.document'].search_count(domain)
            
            data = []
            for document in documents:
                data.append({
                    'id': document.id,
                    'name': document.name,
                    'student_id': document.student_id.id,
                    'student_name': document.student_id.name,
                    'document_type_id': document.document_type_id.id if document.document_type_id else None,
                    'document_type_name': document.document_type_id.name if document.document_type_id else None,
                    'date_created': document.date_created.isoformat() if document.date_created else None,
                    'state': document.state,
                    'is_validated': document.is_validated,
                    'has_file': bool(document.file_data)
                })
            
            return {
                'success': True,
                'data': data,
                'total': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des documents: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/student-documents/get', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_document(self, **kwargs):
        """Récupérer les détails d'un document"""
        try:
            document_id = kwargs.get('document_id')
            if not document_id:
                return {'success': False, 'error': 'Le paramètre document_id est requis'}
            document = request.env['student.document'].browse(document_id)
            if not document.exists():
                return {'success': False, 'error': 'Document non trouvé'}
            
            data = {
                'id': document.id,
                'name': document.name,
                'student_id': document.student_id.id,
                'student_name': document.student_id.name,
                'document_type_id': document.document_type_id.id if document.document_type_id else None,
                'document_type_name': document.document_type_id.name if document.document_type_id else None,
                'date_created': document.date_created.isoformat() if document.date_created else None,
                'state': document.state,
                'is_validated': document.is_validated
            }
            
            # Inclure le fichier si demandé
            if kwargs.get('include_file') and document.file_data:
                data['file_data'] = document.file_data.decode('utf-8')
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération du document {document_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/student-documents/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_student_document(self, **kwargs):
        """Créer un nouveau document d'élève"""
        try:
            # Validation des données requises
            required_fields = ['student_id', 'name']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Le champ {field} est requis'}
            
            # Préparer les données
            data = {
                'student_id': int(kwargs['student_id']),
                'name': kwargs['name'],
                'document_type_id': int(kwargs['document_type_id']) if kwargs.get('document_type_id') else None,
                'date_created': kwargs.get('date_created')
            }
            
            # Traiter le fichier s'il est fourni
            if kwargs.get('file_data'):
                data['file_data'] = kwargs['file_data']
            
            document = request.env['student.document'].create(data)
            
            return {
                'success': True,
                'message': 'Document créé avec succès',
                'data': {
                    'id': document.id,
                    'name': document.name,
                    'state': document.state
                }
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la création du document: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/student-documents/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_student_document(self, **kwargs):
        """Mettre à jour un document"""
        try:
            document_id = kwargs.get('document_id')
            if not document_id:
                return {'success': False, 'error': 'Le paramètre document_id est requis'}
            document = request.env['student.document'].browse(document_id)
            if not document.exists():
                return {'success': False, 'error': 'Document non trouvé'}
            
            # Préparer les données de mise à jour
            update_data = {}
            allowed_fields = ['name', 'document_type_id', 'state', 'file_data']
            
            for field in allowed_fields:
                if field in kwargs:
                    if field == 'document_type_id' and kwargs[field]:
                        update_data[field] = int(kwargs[field])
                    else:
                        update_data[field] = kwargs[field]
            
            if update_data:
                document.write(update_data)
            
            return {
                'success': True,
                'message': 'Document mis à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour du document: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/student-documents/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_student_document(self, **kwargs):
        """Supprimer un document"""
        try:
            document_id = kwargs.get('document_id')
            if not document_id:
                return {'success': False, 'error': 'Le paramètre document_id est requis'}
            document = request.env['student.document'].browse(document_id)
            if not document.exists():
                return {'success': False, 'error': 'Document non trouvé'}
            
            name = document.name
            document.unlink()
            
            return {
                'success': True,
                'message': f'Document {name} supprimé avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression du document: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/student-documents/approve', type='json', auth='user', methods=['POST'], csrf=False)
    def approve_document(self, **kwargs):
        """Approuver un document"""
        try:
            document_id = kwargs.get('document_id')
            if not document_id:
                return {'success': False, 'error': 'Le paramètre document_id est requis'}
            document = request.env['student.document'].browse(document_id)
            if not document.exists():
                return {'success': False, 'error': 'Document non trouvé'}
            
            document.write({'state': 'approved'})
            
            return {
                'success': True,
                'message': 'Document approuvé avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de l'approbation du document: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/student-documents/reject', type='json', auth='user', methods=['POST'], csrf=False)
    def reject_document(self, **kwargs):
        """Rejeter un document"""
        try:
            document_id = kwargs.get('document_id')
            if not document_id:
                return {'success': False, 'error': 'Le paramètre document_id est requis'}
            document = request.env['student.document'].browse(document_id)
            if not document.exists():
                return {'success': False, 'error': 'Document non trouvé'}
            
            document.write({'state': 'rejected'})
            
            return {
                'success': True,
                'message': 'Document rejeté'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors du rejet du document: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/students/document-checklist', type='json', auth='user', methods=['POST'], csrf=False)
    def get_student_document_checklist(self, **kwargs):
        """Récupérer la checklist des documents d'un élève"""
        try:
            student_id = kwargs.get('student_id')
            if not student_id:
                return {'success': False, 'error': 'Le paramètre student_id est requis'}
            student = request.env['op.student'].browse(student_id)
            if not student.exists():
                return {'success': False, 'error': 'Élève non trouvé'}
            
            # Récupérer tous les types de documents
            document_types = request.env['student.document.type'].search([('active', '=', True)])
            
            # Récupérer les documents existants de l'élève
            existing_docs = request.env['student.document'].search([('student_id', '=', student_id)])
            
            checklist = []
            for doc_type in document_types:
                # Vérifier si l'élève a ce type de document
                matching_docs = existing_docs.filtered(lambda d: d.document_type_id.id == doc_type.id)
                
                status = 'missing'
                document_info = None
                
                if matching_docs:
                    latest_doc = matching_docs[0]  # Le plus récent
                    if latest_doc.state == 'approved':
                        status = 'complete'
                    elif latest_doc.state == 'rejected':
                        status = 'rejected'
                    else:
                        status = 'pending'
                    
                    document_info = {
                        'id': latest_doc.id,
                        'name': latest_doc.name,
                        'state': latest_doc.state,
                        'date_created': latest_doc.date_created.isoformat() if latest_doc.date_created else None
                    }
                
                checklist.append({
                    'document_type_id': doc_type.id,
                    'document_type_name': doc_type.name,
                    'document_type_code': doc_type.code,
                    'category': doc_type.category,
                    'is_mandatory': doc_type.is_mandatory,
                    'status': status,
                    'document': document_info
                })
            
            # Calculer les statistiques
            total_types = len(document_types)
            mandatory_types = len(document_types.filtered(lambda t: t.is_mandatory))
            complete_docs = len([item for item in checklist if item['status'] == 'complete'])
            complete_mandatory = len([item for item in checklist 
                                    if item['status'] == 'complete' and item['is_mandatory']])
            
            return {
                'success': True,
                'data': {
                    'student_id': student_id,
                    'student_name': student.name,
                    'checklist': checklist,
                    'statistics': {
                        'total_document_types': total_types,
                        'mandatory_types': mandatory_types,
                        'complete_documents': complete_docs,
                        'complete_mandatory': complete_mandatory,
                        'completion_rate': (complete_docs / total_types * 100) if total_types > 0 else 0,
                        'mandatory_completion_rate': (complete_mandatory / mandatory_types * 100) if mandatory_types > 0 else 0
                    }
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération de la checklist: {str(e)}")
            return {'success': False, 'error': str(e)}


class StudentDocumentTypeController(http.Controller):
    """API Controller pour StudentDocumentType"""

    @http.route('/api/document-types', type='json', auth='user', methods=['POST'], csrf=False)
    def get_document_types(self, **kwargs):
        """Récupérer la liste des types de documents"""
        try:
            domain = []
            
            if kwargs.get('category'):
                domain.append(('category', '=', kwargs['category']))
            
            if kwargs.get('active') is not None:
                domain.append(('active', '=', kwargs['active']))
            
            document_types = request.env['student.document.type'].search(domain, order='sequence, name')
            
            data = []
            for doc_type in document_types:
                data.append({
                    'id': doc_type.id,
                    'name': doc_type.name,
                    'code': doc_type.code,
                    'category': doc_type.category,
                    'is_mandatory': doc_type.is_mandatory,
                    'requires_validation': doc_type.requires_validation,
                    'allowed_file_types': doc_type.allowed_file_types,
                    'icon': doc_type.icon,
                    'sequence': doc_type.sequence,
                    'active': doc_type.active,
                    'has_expiry': doc_type.has_expiry,
                    'default_validity_days': doc_type.default_validity_days
                })
            
            return {
                'success': True,
                'data': data
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la récupération des types de documents: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/document-types/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_document_type(self, **kwargs):
        """Créer un nouveau type de document"""
        try:
            # Validation des données requises
            required_fields = ['name', 'code', 'category']
            for field in required_fields:
                if not kwargs.get(field):
                    return {'success': False, 'error': f'Le champ {field} est requis'}
            
            data = {
                'name': kwargs['name'],
                'code': kwargs['code'],
                'category': kwargs['category'],
                'is_mandatory': kwargs.get('is_mandatory', False),
                'requires_validation': kwargs.get('requires_validation', False),
                'allowed_file_types': kwargs.get('allowed_file_types'),
                'icon': kwargs.get('icon'),
                'sequence': int(kwargs.get('sequence', 10)),
                'has_expiry': kwargs.get('has_expiry', False),
                'default_validity_days': int(kwargs.get('default_validity_days', 365))
            }
            
            doc_type = request.env['student.document.type'].create(data)
            
            return {
                'success': True,
                'message': 'Type de document créé avec succès',
                'data': {
                    'id': doc_type.id,
                    'name': doc_type.name,
                    'code': doc_type.code
                }
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la création du type de document: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/document-types/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_document_type(self, **kwargs):
        """Mettre à jour un type de document"""
        try:
            type_id = kwargs.get('type_id')
            if not type_id:
                return {'success': False, 'error': 'Le paramètre type_id est requis'}
            doc_type = request.env['student.document.type'].browse(type_id)
            if not doc_type.exists():
                return {'success': False, 'error': 'Type de document non trouvé'}
            
            # Préparer les données de mise à jour
            update_data = {}
            allowed_fields = [
                'name', 'code', 'category', 'is_mandatory', 'requires_validation',
                'allowed_file_types', 'icon', 'sequence', 'active', 'has_expiry', 
                'default_validity_days'
            ]
            
            for field in allowed_fields:
                if field in kwargs:
                    if field in ['sequence', 'default_validity_days']:
                        update_data[field] = int(kwargs[field])
                    else:
                        update_data[field] = kwargs[field]
            
            if update_data:
                doc_type.write(update_data)
            
            return {
                'success': True,
                'message': 'Type de document mis à jour avec succès'
            }
            
        except ValidationError as e:
            return {'success': False, 'error': e.args[0]}
        except Exception as e:
            _logger.error(f"Erreur lors de la mise à jour du type de document: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/api/document-types/delete', type='json', auth='user', methods=['POST'], csrf=False)
    def delete_document_type(self, **kwargs):
        """Supprimer un type de document"""
        try:
            type_id = kwargs.get('type_id')
            if not type_id:
                return {'success': False, 'error': 'Le paramètre type_id est requis'}
            doc_type = request.env['student.document.type'].browse(type_id)
            if not doc_type.exists():
                return {'success': False, 'error': 'Type de document non trouvé'}
            
            # Vérifier s'il y a des documents liés
            linked_docs = request.env['student.document'].search_count([('document_type_id', '=', type_id)])
            if linked_docs > 0:
                return {
                    'success': False,
                    'error': f'Impossible de supprimer: {linked_docs} documents utilisent ce type'
                }
            
            name = doc_type.name
            doc_type.unlink()
            
            return {
                'success': True,
                'message': f'Type de document {name} supprimé avec succès'
            }
            
        except Exception as e:
            _logger.error(f"Erreur lors de la suppression du type de document: {str(e)}")
            return {'success': False, 'error': str(e)} 