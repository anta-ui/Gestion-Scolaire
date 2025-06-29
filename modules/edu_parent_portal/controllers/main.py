# -*- coding: utf-8 -*-

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
import json
import base64


class ParentPortalController(CustomerPortal):
    """Contrôleur principal du portail parents"""
    
    def _prepare_home_portal_values(self, counters):
        """Prépare les valeurs pour la page d'accueil du portail"""
        values = super()._prepare_home_portal_values(counters)
        
        # Vérifier si l'utilisateur est un parent
        if request.env.user.partner_id.is_parent:
            # Récupérer les enfants
            children = request.env['op.student'].search([
                ('parent_ids', 'in', [request.env.user.partner_id.id])
            ])
            
            if 'children_count' in counters:
                values['children_count'] = len(children)
            
            if 'messages_count' in counters:
                values['messages_count'] = request.env['edu.chat.message'].search_count([
                    ('chat_id.participant_ids', '=', request.env.user.partner_id.id),
                    ('is_read', '=', False),
                    ('sender_id', '!=', request.env.user.partner_id.id)
                ])
            
            if 'homework_count' in counters:
                today = fields.Date.context_today(request.env['op.assignment'])
                values['homework_count'] = request.env['op.assignment'].search_count([
                    ('batch_id.student_ids', 'in', children.ids),
                    ('submission_date', '>=', today)
                ])
        
        return values
    
    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        """Page d'accueil du portail"""
        values = self._prepare_home_portal_values(['children_count', 'messages_count', 'homework_count'])
        
        # Vérifier si l'utilisateur est un parent
        if not request.env.user.partner_id.is_parent:
            return request.redirect('/web')
        
        # Vérifier si le portail est disponible
        config = request.env['edu.parent.portal.config'].get_active_config()
        if not config.is_portal_available():
            return request.render('edu_parent_portal.portal_maintenance', {
                'message': config.maintenance_message
            })
        
        # Récupérer les données du tableau de bord
        dashboard_data = request.env['edu.parent.dashboard'].get_dashboard_data()
        values.update(dashboard_data)
        values['config'] = config
        
        return request.render("edu_parent_portal.portal_my_home", values)
    
    @http.route(['/my/children'], type='http', auth="user", website=True)
    def portal_my_children(self, **kw):
        """Liste des enfants"""
        children = request.env['op.student'].search([
            ('parent_ids', 'in', [request.env.user.partner_id.id])
        ])
        
        values = {
            'children': children,
            'page_name': 'children',
        }
        return request.render("edu_parent_portal.portal_my_children", values)
    
    @http.route(['/my/child/<int:student_id>'], type='http', auth="user", website=True)
    def portal_child_detail(self, student_id, **kw):
        """Détail d'un enfant"""
        try:
            student = self._document_check_access('op.student', student_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        # Vérifier que l'utilisateur est bien parent de cet enfant
        if request.env.user.partner_id not in student.parent_ids:
            return request.redirect('/my')
        
        # Récupérer les données récentes
        recent_grades = request.env['edu.evaluation'].search([
            ('student_id', '=', student_id),
            ('state', '=', 'published')
        ], order='date desc', limit=5)
        
        recent_attendance = request.env['edu.attendance.record'].search([
            ('student_id', '=', student_id)
        ], order='expected_check_in desc', limit=10)
        
        upcoming_homework = request.env['op.assignment'].search([
            ('batch_id.student_ids', 'in', [student_id]),
            ('submission_date', '>=', fields.Date.context_today(request.env['op.assignment']))
        ], order='submission_date', limit=5)
        
        values = {
            'student': student,
            'recent_grades': recent_grades,
            'recent_attendance': recent_attendance,
            'upcoming_homework': upcoming_homework,
            'page_name': 'child_detail',
        }
        return request.render("edu_parent_portal.portal_child_detail", values)
    
    @http.route(['/my/grades'], type='http', auth="user", website=True)
    def portal_my_grades(self, **kw):
        """Notes et évaluations"""
        children = request.env['op.student'].search([
            ('parent_ids', 'in', [request.env.user.partner_id.id])
        ])
        
        domain = [
            ('student_id', 'in', children.ids),
            ('state', '=', 'published')
        ]
        
        # Filtres
        if kw.get('student_id'):
            domain.append(('student_id', '=', int(kw.get('student_id'))))
        
        if kw.get('course_id'):
            domain.append(('course_id', '=', int(kw.get('course_id'))))
        
        if kw.get('period_id'):
            domain.append(('period_id', '=', int(kw.get('period_id'))))
        
        grades = request.env['edu.evaluation'].search(domain, order='date desc')
        
        # Données pour les filtres
        courses = request.env['op.course'].search([])
        periods = request.env['edu.evaluation.period'].search([])
        
        values = {
            'grades': grades,
            'children': children,
            'courses': courses,
            'periods': periods,
            'page_name': 'grades',
        }
        return request.render("edu_parent_portal.portal_my_grades", values)
    
    @http.route(['/my/attendance'], type='http', auth="user", website=True)
    def portal_my_attendance(self, **kw):
        """Présences et absences"""
        children = request.env['op.student'].search([
            ('parent_ids', 'in', [request.env.user.partner_id.id])
        ])
        
        domain = [('student_id', 'in', children.ids)]
        
        # Filtres
        if kw.get('student_id'):
            domain.append(('student_id', '=', int(kw.get('student_id'))))
        
        if kw.get('date_from'):
            domain.append(('expected_check_in', '>=', kw.get('date_from')))
        
        if kw.get('date_to'):
            domain.append(('expected_check_in', '<=', kw.get('date_to')))
        
        attendance_records = request.env['edu.attendance.record'].search(
            domain, order='expected_check_in desc'
        )
        
        values = {
            'attendance_records': attendance_records,
            'children': children,
            'page_name': 'attendance',
        }
        return request.render("edu_parent_portal.portal_my_attendance", values)
    
    @http.route(['/my/homework'], type='http', auth="user", website=True)
    def portal_my_homework(self, **kw):
        """Devoirs et travaux"""
        children = request.env['op.student'].search([
            ('parent_ids', 'in', [request.env.user.partner_id.id])
        ])
        
        domain = [('batch_id.student_ids', 'in', children.ids)]
        
        # Filtres
        if kw.get('student_id'):
            student_batches = request.env['op.student'].browse(int(kw.get('student_id'))).course_detail_ids.mapped('batch_id')
            domain.append(('batch_id', 'in', student_batches.ids))
        
        if kw.get('subject_id'):
            domain.append(('subject_id', '=', int(kw.get('subject_id'))))
        
        if kw.get('status') == 'pending':
            domain.append(('submission_date', '>=', fields.Date.context_today(request.env['op.assignment'])))
        elif kw.get('status') == 'overdue':
            domain.append(('submission_date', '<', fields.Date.context_today(request.env['op.assignment'])))
        
        homework = request.env['op.assignment'].search(domain, order='submission_date desc')
        
        # Données pour les filtres
        subjects = request.env['op.subject'].search([])
        
        values = {
            'homework': homework,
            'children': children,
            'subjects': subjects,
            'page_name': 'homework',
        }
        return request.render("edu_parent_portal.portal_my_homework", values)
    
    @http.route(['/my/schedule'], type='http', auth="user", website=True)
    def portal_my_schedule(self, **kw):
        """Planning et emploi du temps"""
        children = request.env['op.student'].search([
            ('parent_ids', 'in', [request.env.user.partner_id.id])
        ])
        
        # Date par défaut : cette semaine
        from datetime import datetime, timedelta
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Récupérer les sessions de la semaine
        sessions = request.env['edu.attendance.session'].search([
            ('student_ids', 'in', children.ids),
            ('start_datetime', '>=', week_start),
            ('start_datetime', '<=', week_end)
        ], order='start_datetime')
        
        values = {
            'sessions': sessions,
            'children': children,
            'week_start': week_start,
            'week_end': week_end,
            'page_name': 'schedule',
        }
        return request.render("edu_parent_portal.portal_my_schedule", values)
    
    @http.route(['/my/messages'], type='http', auth="user", website=True)
    def portal_my_messages(self, **kw):
        """Messages et conversations"""
        # Récupérer les conversations de l'utilisateur
        chats = request.env['edu.chat'].search([
            ('participant_ids', '=', request.env.user.partner_id.id)
        ], order='last_message_date desc')
        
        values = {
            'chats': chats,
            'page_name': 'messages',
        }
        return request.render("edu_parent_portal.portal_my_messages", values)
    
    @http.route(['/my/chat/<int:chat_id>'], type='http', auth="user", website=True)
    def portal_chat_detail(self, chat_id, **kw):
        """Détail d'une conversation"""
        try:
            chat = self._document_check_access('edu.chat', chat_id)
        except (AccessError, MissingError):
            return request.redirect('/my/messages')
        
        # Vérifier que l'utilisateur participe à cette conversation
        if request.env.user.partner_id not in chat.participant_ids:
            return request.redirect('/my/messages')
        
        # Marquer les messages comme lus
        unread_messages = chat.message_ids.filtered(
            lambda m: not m.is_read and m.sender_id != request.env.user.partner_id
        )
        unread_messages.write({'is_read': True})
        
        values = {
            'chat': chat,
            'page_name': 'chat_detail',
        }
        return request.render("edu_parent_portal.portal_chat_detail", values)
    
    @http.route(['/my/documents'], type='http', auth="user", website=True)
    def portal_my_documents(self, **kw):
        """Documents scolaires"""
        children = request.env['op.student'].search([
            ('parent_ids', 'in', [request.env.user.partner_id.id])
        ])
        
        # Récupérer les documents des enfants
        documents = request.env['edu.parent.document'].search([
            ('student_ids', 'in', children.ids),
            ('state', '=', 'available')
        ], order='create_date desc')
        
        # Grouper par type de document
        document_types = documents.mapped('document_type')
        
        values = {
            'documents': documents,
            'document_types': document_types,
            'children': children,
            'page_name': 'documents',
        }
        return request.render("edu_parent_portal.portal_my_documents", values)
    
    @http.route(['/my/document/<int:document_id>/download'], type='http', auth="user")
    def portal_document_download(self, document_id, **kw):
        """Télécharger un document"""
        try:
            document = self._document_check_access('edu.parent.document', document_id)
        except (AccessError, MissingError):
            return request.redirect('/my/documents')
        
        # Vérifier que l'utilisateur peut accéder à ce document
        children = request.env['op.student'].search([
            ('parent_ids', 'in', [request.env.user.partner_id.id])
        ])
        
        if not any(child in document.student_ids for child in children):
            return request.redirect('/my/documents')
        
        if document.file_content:
            filename = document.filename or f"document_{document.id}.pdf"
            return request.make_response(
                base64.b64decode(document.file_content),
                headers=[
                    ('Content-Type', 'application/octet-stream'),
                    ('Content-Disposition', f'attachment; filename="{filename}"')
                ]
            )
        
        return request.redirect('/my/documents')
    
    @http.route(['/my/payments'], type='http', auth="user", website=True)
    def portal_my_payments(self, **kw):
        """Paiements et factures"""
        children = request.env['op.student'].search([
            ('parent_ids', 'in', [request.env.user.partner_id.id])
        ])
        
        # Récupérer les paiements des enfants
        payments = request.env['edu.parent.payment'].search([
            ('student_ids', 'in', children.ids)
        ], order='due_date desc')
        
        values = {
            'payments': payments,
            'children': children,
            'page_name': 'payments',
        }
        return request.render("edu_parent_portal.portal_my_payments", values)
    
    @http.route(['/my/appointments'], type='http', auth="user", website=True)
    def portal_my_appointments(self, **kw):
        """Rendez-vous et réunions"""
        appointments = request.env['edu.parent.appointment'].search([
            ('parent_id', '=', request.env.user.partner_id.id)
        ], order='appointment_date desc')
        
        values = {
            'appointments': appointments,
            'page_name': 'appointments',
        }
        return request.render("edu_parent_portal.portal_my_appointments", values)
    
    @http.route(['/my/profile'], type='http', auth="user", website=True)
    def portal_my_profile(self, **kw):
        """Profil utilisateur"""
        # Récupérer les préférences de notification
        preferences = request.env['edu.notification.preference'].search([
            ('user_id', '=', request.env.user.id)
        ])
        
        # Récupérer les enfants
        children = request.env['op.student'].search([
            ('parent_ids', 'in', [request.env.user.partner_id.id])
        ])
        
        values = {
            'preferences': preferences,
            'children': children,
            'page_name': 'profile',
        }
        return request.render("edu_parent_portal.portal_my_profile", values)
    
    # Routes AJAX
    @http.route(['/my/dashboard/data'], type='json', auth="user")
    def get_dashboard_data(self, **kw):
        """Récupère les données du tableau de bord via AJAX"""
        try:
            data = request.env['edu.parent.dashboard'].get_dashboard_data()
            return {'success': True, 'data': data}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route(['/my/chat/send'], type='json', auth="user")
    def send_chat_message(self, chat_id, message, **kw):
        """Envoie un message dans une conversation"""
        try:
            chat = request.env['edu.chat'].browse(chat_id)
            
            # Vérifier l'accès
            if request.env.user.partner_id not in chat.participant_ids:
                return {'success': False, 'error': 'Accès refusé'}
            
            # Créer le message
            new_message = request.env['edu.chat.message'].create({
                'chat_id': chat_id,
                'sender_id': request.env.user.partner_id.id,
                'content': message,
                'message_type': 'text'
            })
            
            return {
                'success': True,
                'message_id': new_message.id,
                'timestamp': new_message.create_date.isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route(['/my/notifications/mark_read'], type='json', auth="user")
    def mark_notifications_read(self, notification_ids, **kw):
        """Marque les notifications comme lues"""
        try:
            notifications = request.env['edu.parent.notification'].browse(notification_ids)
            notifications.write({'is_read': True, 'read_date': fields.Datetime.now()})
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @http.route(['/my/preferences/update'], type='json', auth="user")
    def update_preferences(self, preferences, **kw):
        """Met à jour les préférences utilisateur"""
        try:
            for pref_data in preferences:
                pref = request.env['edu.notification.preference'].browse(pref_data['id'])
                if pref.user_id == request.env.user:
                    pref.write({
                        'email_enabled': pref_data.get('email_enabled', False),
                        'sms_enabled': pref_data.get('sms_enabled', False),
                        'push_enabled': pref_data.get('push_enabled', False)
                    })
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Méthodes utilitaires
    def _document_check_access(self, model_name, document_id, access_token=None):
        """Vérifie l'accès à un document"""
        document = request.env[model_name].browse([document_id])
        document_sudo = document.with_user(request.env.user).exists()
        if not document_sudo:
            raise MissingError(_("Ce document n'existe pas."))
        
        try:
            document.check_access_rights('read')
            document.check_access_rule('read')
        except AccessError:
            raise AccessError(_("Vous n'avez pas accès à ce document."))
        
        return document_sudo
