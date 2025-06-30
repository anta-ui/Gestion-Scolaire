# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import json


class EduParentDashboard(models.Model):
    """Tableau de bord personnalisé pour les parents"""
    _name = 'edu.parent.dashboard'
    _description = 'Tableau de bord parent'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom du tableau de bord',
        required=True,
        help="Nom du tableau de bord"
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Utilisateur',
        required=True,
        default=lambda self: self.env.user,
        help="Utilisateur propriétaire du tableau de bord"
    )
    
    is_default = fields.Boolean(
        string='Tableau de bord par défaut',
        default=True,
        help="Tableau de bord par défaut pour cet utilisateur"
    )
    
    # Configuration des widgets
    widget_config = fields.Text(
        string='Configuration des widgets',
        default='{}',
        help="Configuration JSON des widgets affichés"
    )
    
    layout = fields.Selection([
        ('grid', 'Grille'),
        ('list', 'Liste'),
        ('cards', 'Cartes'),
        ('compact', 'Compact')
    ], string='Disposition', default='grid', help="Type de disposition")
    
    columns = fields.Integer(
        string='Nombre de colonnes',
        default=3,
        help="Nombre de colonnes dans la grille"
    )
    
    # Widgets activés
    show_summary_widget = fields.Boolean(
        string='Résumé général',
        default=True,
        help="Afficher le widget de résumé"
    )
    
    show_grades_widget = fields.Boolean(
        string='Dernières notes',
        default=True,
        help="Afficher le widget des notes"
    )
    
    show_attendance_widget = fields.Boolean(
        string='Présences récentes',
        default=True,
        help="Afficher le widget de présence"
    )
    
    show_homework_widget = fields.Boolean(
        string='Devoirs à venir',
        default=True,
        help="Afficher le widget des devoirs"
    )
    
    show_schedule_widget = fields.Boolean(
        string='Planning du jour',
        default=True,
        help="Afficher le widget de planning"
    )
    
    show_messages_widget = fields.Boolean(
        string='Messages récents',
        default=True,
        help="Afficher le widget des messages"
    )
    
    show_announcements_widget = fields.Boolean(
        string='Annonces',
        default=True,
        help="Afficher le widget des annonces"
    )
    
    show_calendar_widget = fields.Boolean(
        string='Calendrier',
        default=True,
        help="Afficher le widget calendrier"
    )
    
    show_payments_widget = fields.Boolean(
        string='Paiements à venir',
        default=True,
        help="Afficher le widget des paiements"
    )
    
    show_progress_widget = fields.Boolean(
        string='Progression scolaire',
        default=True,
        help="Afficher le widget de progression"
    )
    
    # Paramètres d'affichage
    refresh_interval = fields.Integer(
        string='Intervalle de rafraîchissement (sec)',
        default=300,
        help="Intervalle de rafraîchissement automatique"
    )
    
    items_limit = fields.Integer(
        string='Limite d\'éléments par widget',
        default=5,
        help="Nombre maximum d'éléments affichés par widget"
    )
    
    date_range = fields.Selection([
        ('week', 'Cette semaine'),
        ('month', 'Ce mois'),
        ('quarter', 'Ce trimestre'),
        ('year', 'Cette année')
    ], string='Période d\'affichage', default='month', help="Période pour les données affichées")
    
    # Méta-données
    last_viewed = fields.Datetime(
        string='Dernière consultation',
        help="Date de dernière consultation"
    )
    
    view_count = fields.Integer(
        string='Nombre de vues',
        default=0,
        help="Nombre de fois consulté"
    )
    
    # Méthodes pour récupérer les données des widgets
    @api.model
    def get_dashboard_data(self, user_id=None):
        """Récupère toutes les données du tableau de bord"""
        if not user_id:
            user_id = self.env.user.id
        
        # Récupérer le tableau de bord par défaut
        dashboard = self.search([
            ('user_id', '=', user_id),
            ('is_default', '=', True)
        ], limit=1)
        
        if not dashboard:
            dashboard = self._create_default_dashboard(user_id)
        
        # Mettre à jour les statistiques de consultation
        dashboard.write({
            'last_viewed': fields.Datetime.now(),
            'view_count': dashboard.view_count + 1
        })
        
        # Récupérer les enfants de l'utilisateur
        children = self._get_user_children(user_id)
        
        data = {
            'dashboard_id': dashboard.id,
            'dashboard_name': dashboard.name,
            'children': children,
            'widgets': {}
        }
        
        # Récupérer les données de chaque widget activé
        if dashboard.show_summary_widget:
            data['widgets']['summary'] = self._get_summary_data(children)
        
        if dashboard.show_grades_widget:
            data['widgets']['grades'] = self._get_grades_data(children, dashboard.items_limit)
        
        if dashboard.show_attendance_widget:
            data['widgets']['attendance'] = self._get_attendance_data(children, dashboard.items_limit)
        
        if dashboard.show_homework_widget:
            data['widgets']['homework'] = self._get_homework_data(children, dashboard.items_limit)
        
        if dashboard.show_schedule_widget:
            data['widgets']['schedule'] = self._get_schedule_data(children)
        
        if dashboard.show_messages_widget:
            data['widgets']['messages'] = self._get_messages_data(user_id, dashboard.items_limit)
        
        if dashboard.show_announcements_widget:
            data['widgets']['announcements'] = self._get_announcements_data(dashboard.items_limit)
        
        if dashboard.show_calendar_widget:
            data['widgets']['calendar'] = self._get_calendar_data(children)
        
        if dashboard.show_payments_widget:
            data['widgets']['payments'] = self._get_payments_data(children, dashboard.items_limit)
        
        if dashboard.show_progress_widget:
            data['widgets']['progress'] = self._get_progress_data(children)
        
        return data
    
    def _get_user_children(self, user_id):
        """Récupère la liste des enfants de l'utilisateur"""
        user = self.env['res.users'].browse(user_id)
        partner = user.partner_id
        
        children = []
        if partner:
            # Chercher les étudiants liés à ce partenaire
            students = self.env['op.student'].search([
                ('partner_id', '=', partner.id)
            ])
            
            for student in students:
                children.append({
                    'id': student.id,
                    'name': student.name,
                    'class': student.course_detail_ids and student.course_detail_ids[0].standard_id.name or '',
                    'photo': student.image_1920,
                    'birth_date': student.birth_date,
                })
        
        return children
    
    def _get_summary_data(self, children):
        """Récupère les données de résumé"""
        if not children:
            return {}
        
        student_ids = [child['id'] for child in children]
        today = fields.Date.context_today(self)
        week_start = today - timedelta(days=today.weekday())
        
        # Statistiques basiques pour le moment (à adapter selon les modules disponibles)
        summary = {
            'children_count': len(children),
            'absences_this_week': 0,
            'new_grades_this_week': 0,
            'upcoming_homework': 0,
            'unread_messages': 0,
        }
        
        return summary
    
    def _get_grades_data(self, children, limit):
        """Récupère les dernières notes"""
        if not children:
            return []
        
        # Pour le moment, retourner des données vides
        # À adapter selon les modules d'évaluation disponibles
        return []
    
    def _get_attendance_data(self, children, limit):
        """Récupère les données de présence récentes"""
        if not children:
            return []
        
        # Pour le moment, retourner des données vides
        # À adapter selon les modules de présence disponibles
        return []
    
    def _get_homework_data(self, children, limit):
        """Récupère les devoirs à venir"""
        if not children:
            return []
        
        # Pour le moment, retourner des données vides
        # À adapter selon les modules de devoirs disponibles
        return []
    
    def _get_schedule_data(self, children):
        """Récupère le planning du jour"""
        if not children:
            return []
        
        # Pour le moment, retourner des données vides
        # À adapter selon les modules de planning disponibles
        return []
    
    def _get_messages_data(self, user_id, limit):
        """Récupère les messages récents"""
        # Pour le moment, retourner des données vides
        # À adapter selon les modules de messagerie disponibles
        return []
    
    def _get_announcements_data(self, limit):
        """Récupère les annonces récentes"""
        # Pour le moment, retourner des données vides
        # À adapter selon les modules d'annonces disponibles
        return []
    
    def _get_calendar_data(self, children):
        """Récupère les événements du calendrier"""
        # Pour le moment, retourner des données vides
        # À adapter selon les besoins spécifiques
        return []
    
    def _get_payments_data(self, children, limit):
        """Récupère les paiements à venir"""
        # Pour le moment, retourner des données vides
        # À adapter avec le module de comptabilité
        return []
    
    def _get_progress_data(self, children):
        """Récupère les données de progression scolaire"""
        # Pour le moment, retourner des données vides
        # À adapter avec des calculs de progression
        return []
    
    def _create_default_dashboard(self, user_id):
        """Crée un tableau de bord par défaut"""
        return self.create({
            'name': 'Mon tableau de bord',
            'user_id': user_id,
            'is_default': True,
        })
    
    # Actions
    def action_reset_layout(self):
        """Remet à zéro la disposition du tableau de bord"""
        self.ensure_one()
        self.write({
            'widget_config': '{}',
            'layout': 'grid',
            'columns': 3,
            'show_summary_widget': True,
            'show_grades_widget': True,
            'show_attendance_widget': True,
            'show_homework_widget': True,
            'show_schedule_widget': True,
            'show_messages_widget': True,
            'show_announcements_widget': True,
            'show_calendar_widget': True,
            'show_payments_widget': True,
            'show_progress_widget': True,
        })
    
    def action_duplicate(self):
        """Duplique le tableau de bord"""
        self.ensure_one()
        new_dashboard = self.copy({
            'name': f"{self.name} (Copie)",
            'is_default': False
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tableau de bord dupliqué'),
            'res_model': 'edu.parent.dashboard',
            'res_id': new_dashboard.id,
            'view_mode': 'form',
            'target': 'current',
        }
