# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class LibraryRecommendation(models.Model):
    _name = 'library.recommendation'
    _description = 'Recommandation de Livre'
    _order = 'create_date desc'

    name = fields.Char(
        string='Nom',
        compute='_compute_name',
        store=True
    )
    
    member_id = fields.Many2one(
        'op.student',
        string='Étudiant',
        required=True
    )
    
    book_id = fields.Many2one(
        'library.book',
        string='Livre Recommandé',
        required=True
    )
    
    recommended_by = fields.Selection([
        ('system', 'Système IA'),
        ('librarian', 'Bibliothécaire'),
        ('member', 'Autre Membre'),
        ('algorithm', 'Algorithme')
    ], string='Recommandé par', default='system')
    
    recommendation_score = fields.Float(
        string='Score de Recommandation',
        default=0.0,
        help='Score de 0 à 1 indiquant la pertinence'
    )
    
    reason = fields.Text(
        string='Raison de la Recommandation'
    )
    
    status = fields.Selection([
        ('pending', 'En Attente'),
        ('viewed', 'Consulté'),
        ('accepted', 'Accepté'),
        ('rejected', 'Rejeté'),
        ('loaned', 'Emprunté')
    ], string='Statut', default='pending')
    
    viewed_date = fields.Datetime(
        string='Date de Consultation'
    )
    
    response_date = fields.Datetime(
        string='Date de Réponse'
    )
    
    notes = fields.Text(
        string='Notes'
    )
    
    @api.depends('member_id', 'book_id')
    def _compute_name(self):
        for rec in self:
            if rec.member_id and rec.book_id:
                rec.name = f"Recommandation pour {rec.member_id.name} - {rec.book_id.title}"
            else:
                rec.name = "Nouvelle Recommandation"
    
    def action_mark_viewed(self):
        """Marquer comme consulté"""
        self.status = 'viewed'
        self.viewed_date = fields.Datetime.now()
    
    def action_accept(self):
        """Accepter la recommandation"""
        self.status = 'accepted'
        self.response_date = fields.Datetime.now()
    
    def action_reject(self):
        """Rejeter la recommandation"""
        self.status = 'rejected'
        self.response_date = fields.Datetime.now()
    
    def action_loan_book(self):
        """Emprunter le livre recommandé"""
        self.ensure_one()
        
        # Marquer comme emprunté
        self.status = 'loaned'
        self.response_date = fields.Datetime.now()
        
        # Rediriger vers l'emprunt
        return self.book_id.action_loan_book()


class LibraryRecommendationEngine(models.Model):
    _name = 'library.recommendation.engine'
    _description = 'Moteur de Recommandation'

    name = fields.Char(
        string='Nom de l\'Algorithme',
        required=True
    )
    
    algorithm_type = fields.Selection([
        ('collaborative', 'Filtrage Collaboratif'),
        ('content_based', 'Basé sur le Contenu'),
        ('hybrid', 'Hybride'),
        ('popularity', 'Popularité'),
        ('random', 'Aléatoire')
    ], string='Type d\'Algorithme', required=True)
    
    description = fields.Text(
        string='Description'
    )
    
    is_active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    weight = fields.Float(
        string='Poids',
        default=1.0,
        help='Poids de cet algorithme dans les recommandations hybrides'
    )
    
    def generate_recommendations(self, member_id, limit=10):
        """Générer des recommandations pour un membre"""
        self.ensure_one()
        
        if self.algorithm_type == 'popularity':
            return self._popularity_based_recommendations(member_id, limit)
        elif self.algorithm_type == 'content_based':
            return self._content_based_recommendations(member_id, limit)
        elif self.algorithm_type == 'collaborative':
            return self._collaborative_filtering(member_id, limit)
        elif self.algorithm_type == 'random':
            return self._random_recommendations(member_id, limit)
        else:
            return []
    
    def _popularity_based_recommendations(self, member_id, limit):
        """Recommandations basées sur la popularité"""
        member = self.env['op.student'].browse(member_id)
        
        # Livres déjà empruntés par l'étudiant
        loaned_books = self.env['library.loan'].search([
            ('member_id', '=', member_id),
            ('state', 'in', ['active', 'returned'])
        ]).mapped('book_id.id')
        
        # Livres populaires non empruntés
        popular_books = self.env['library.book'].search([
            ('id', 'not in', loaned_books),
            ('state', '=', 'available'),
            ('is_available', '=', True)
        ], order='total_loans desc', limit=limit)
        
        recommendations = []
        for book in popular_books:
            recommendations.append({
                'book_id': book.id,
                'score': min(book.total_loans / 100.0, 1.0),  # Normaliser le score
                'reason': f'Livre populaire avec {book.total_loans} emprunts'
            })
        
        return recommendations
    
    def _content_based_recommendations(self, member_id, limit):
        """Recommandations basées sur le contenu"""
        member = self.env['op.student'].browse(member_id)
        
        # Analyser les préférences de l'étudiant basées sur ses emprunts
        loan_records = self.env['library.loan'].search([
            ('member_id', '=', member_id),
            ('state', 'in', ['active', 'returned'])
        ])
        loaned_books = loan_records.mapped('book_id')
        loaned_book_ids = loaned_books.ids
        
        if not loaned_books:
            return self._popularity_based_recommendations(member_id, limit)
        
        # Catégories préférées
        preferred_categories = loaned_books.mapped('category_id.id')
        
        # Auteurs préférés
        preferred_authors = loaned_books.mapped('author_ids.id')
        
        # Rechercher des livres similaires
        domain = [
            ('id', 'not in', loaned_book_ids),
            ('state', '=', 'available'),
            ('is_available', '=', True)
        ]
        
        if preferred_categories:
            domain.append(('category_id', 'in', preferred_categories))
        
        similar_books = self.env['library.book'].search(domain, limit=limit * 2)
        
        recommendations = []
        for book in similar_books[:limit]:
            score = 0.0
            reason_parts = []
            
            # Score basé sur la catégorie
            if book.category_id and book.category_id.id in preferred_categories:
                score += 0.5
                reason_parts.append(f'catégorie {book.category_id.name}')
            
            # Score basé sur l'auteur
            common_authors = set(book.author_ids.ids) & set(preferred_authors)
            if common_authors:
                score += 0.5
                author_names = [a.name for a in book.author_ids if a.id in common_authors]
                reason_parts.append(f'auteur(s) {", ".join(author_names)}')
            
            if score > 0:
                recommendations.append({
                    'book_id': book.id,
                    'score': score,
                    'reason': f'Similaire par {" et ".join(reason_parts)}'
                })
        
        return sorted(recommendations, key=lambda x: x['score'], reverse=True)
    
    def _collaborative_filtering(self, member_id, limit):
        """Filtrage collaboratif simple"""
        member = self.env['op.student'].browse(member_id)
        
        # Livres empruntés par cet étudiant
        member_loans = self.env['library.loan'].search([
            ('member_id', '=', member_id),
            ('state', 'in', ['active', 'returned'])
        ])
        loaned_books = member_loans.mapped('book_id.id')
        
        # Trouver des étudiants avec des goûts similaires
        similar_students = self.env['op.student'].search([
            ('id', '!=', member_id)
        ])
        
        # Filtrer les étudiants qui ont emprunté des livres similaires
        similar_student_ids = []
        for student in similar_students:
            student_loans = self.env['library.loan'].search([
                ('member_id', '=', student.id),
                ('book_id', 'in', loaned_books),
                ('state', 'in', ['active', 'returned'])
            ])
            if student_loans:
                similar_student_ids.append(student.id)
        
        # Livres empruntés par des étudiants similaires
        recommended_loans = self.env['library.loan'].search([
            ('member_id', 'in', similar_student_ids),
            ('book_id', 'not in', loaned_books),
            ('state', 'in', ['active', 'returned'])
        ])
        
        recommended_books = recommended_loans.mapped('book_id').filtered(
            lambda b: b.state == 'available' and b.is_available
        )
        
        recommendations = []
        for book in recommended_books[:limit]:
            # Compter combien d'étudiants similaires ont emprunté ce livre
            count = len(recommended_loans.filtered(lambda l: l.book_id.id == book.id))
            recommendations.append({
                'book_id': book.id,
                'score': min(count / 10.0, 1.0),  # Normaliser
                'reason': f'Apprécié par {count} étudiants aux goûts similaires'
            })
        
        return sorted(recommendations, key=lambda x: x['score'], reverse=True)
    
    def _random_recommendations(self, member_id, limit):
        """Recommandations aléatoires"""
        member = self.env['op.student'].browse(member_id)
        
        # Livres déjà empruntés
        member_loans = self.env['library.loan'].search([
            ('member_id', '=', member_id),
            ('state', 'in', ['active', 'returned'])
        ])
        loaned_books = member_loans.mapped('book_id.id')
        
        random_books = self.env['library.book'].search([
            ('id', 'not in', loaned_books),
            ('state', '=', 'available'),
            ('is_available', '=', True)
        ], limit=limit)
        
        recommendations = []
        for book in random_books:
            recommendations.append({
                'book_id': book.id,
                'score': 0.5,  # Score neutre
                'reason': 'Découverte aléatoire'
            })
        
        return recommendations
