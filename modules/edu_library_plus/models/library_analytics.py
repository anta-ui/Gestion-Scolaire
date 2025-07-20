# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from datetime import datetime, timedelta


class LibraryAnalytics(models.Model):
    _name = 'library.analytics'
    _description = 'Analyses de Bibliothèque'
    _auto = False

    name = fields.Char(string='Nom')
    book_id = fields.Many2one('library.book', string='Livre')
    member_id = fields.Many2one('op.student', string='Étudiant')
    loan_count = fields.Integer(string='Nombre de Prêts')
    reservation_count = fields.Integer(string='Nombre de Réservations')
    date = fields.Date(string='Date')
    
    def init(self):
        """Créer la vue SQL pour les analyses"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    row_number() OVER () AS id,
                    'loan_' || l.id AS name,
                    l.book_id,
                    l.member_id,
                    1 AS loan_count,
                    0 AS reservation_count,
                    l.loan_date::date AS date
                FROM library_loan l
                WHERE l.state != 'cancelled'
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 10000 AS id,
                    'reservation_' || r.id AS name,
                    r.book_id,
                    r.member_id,
                    0 AS loan_count,
                    1 AS reservation_count,
                    r.reservation_date::date AS date
                FROM library_reservation r
                WHERE r.state != 'cancelled'
            )
        """ % self._table)


class LibraryReport(models.TransientModel):
    _name = 'library.report'
    _description = 'Rapport de Bibliothèque'

    date_from = fields.Date(
        string='Date de début',
        default=lambda self: fields.Date.today() - timedelta(days=30)
    )
    
    date_to = fields.Date(
        string='Date de fin',
        default=fields.Date.today
    )
    
    report_type = fields.Selection([
        ('loans', 'Prêts'),
        ('reservations', 'Réservations'),
        ('members', 'Membres'),
        ('books', 'Livres'),
        ('popular', 'Livres Populaires')
    ], string='Type de Rapport', default='loans')
    
    def generate_report(self):
        """Générer le rapport selon le type sélectionné"""
        if self.report_type == 'loans':
            return self._generate_loans_report()
        elif self.report_type == 'reservations':
            return self._generate_reservations_report()
        elif self.report_type == 'members':
            return self._generate_members_report()
        elif self.report_type == 'books':
            return self._generate_books_report()
        elif self.report_type == 'popular':
            return self._generate_popular_books_report()
    
    def _generate_loans_report(self):
        """Générer le rapport des prêts"""
        domain = [
            ('loan_date', '>=', self.date_from),
            ('loan_date', '<=', self.date_to)
        ]
        return {
            'name': 'Rapport des Prêts',
            'type': 'ir.actions.act_window',
            'res_model': 'library.loan',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'create': False}
        }
    
    def _generate_reservations_report(self):
        """Générer le rapport des réservations"""
        domain = [
            ('reservation_date', '>=', self.date_from),
            ('reservation_date', '<=', self.date_to)
        ]
        return {
            'name': 'Rapport des Réservations',
            'type': 'ir.actions.act_window',
            'res_model': 'library.reservation',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'create': False}
        }
    
    def _generate_popular_books_report(self):
        """Générer le rapport des livres populaires"""
        return {
            'name': 'Livres Populaires',
            'type': 'ir.actions.act_window',
            'res_model': 'library.book',
            'view_mode': 'tree,form',
            'context': {'create': False}
        }
