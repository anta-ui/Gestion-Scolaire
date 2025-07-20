# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import qrcode
import base64
from io import BytesIO
import logging
import requests
from datetime import datetime, timedelta
import json

_logger = logging.getLogger(__name__)

class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Livre de bibliothèque'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'title, author_ids'

    # Informations de base
    title = fields.Char(
        string='Titre',
        required=True,
        tracking=True,
        translate=True
    )
    
    subtitle = fields.Char(
        string='Sous-titre',
        translate=True
    )
    
    isbn = fields.Char(
        string='ISBN',
        help='Numéro ISBN du livre',
        tracking=True
    )
    
    isbn13 = fields.Char(
        string='ISBN-13',
        help='Numéro ISBN-13 du livre'
    )
    
    barcode = fields.Char(
        string='Code-barres',
        help='Code-barres interne',
        copy=False
    )
    
    # Relations
    author_ids = fields.Many2many(
        'library.book.author',
        'library_book_author_rel',
        'book_id',
        'author_id',
        string='Auteurs',
        required=True
    )
    
    publisher_id = fields.Many2one(
        'library.book.publisher',
        string='Éditeur'
    )
    
    category_id = fields.Many2one(
        'library.book.category',
        string='Catégorie'
    )
    
    # Détails du livre
    description = fields.Html(
        string='Description',
        translate=True
    )
    
    summary = fields.Text(
        string='Résumé',
        translate=True
    )
    
    publication_date = fields.Date(
        string='Date de publication'
    )
    
    edition = fields.Char(
        string='Édition'
    )
    
    pages = fields.Integer(
        string='Nombre de pages'
    )
    
    language_id = fields.Many2one(
        'res.lang',
        string='Langue',
        default=lambda self: self.env.ref('base.lang_fr')
    )
    
    # Informations physiques
    format_type = fields.Selection([
        ('physical', 'Livre physique'),
        ('digital', 'Livre numérique'),
        ('audio', 'Livre audio'),
        ('hybrid', 'Hybride'),
    ], string='Type de format', default='physical', required=True, tracking=True)
    
    physical_format = fields.Selection([
        ('hardcover', 'Couverture rigide'),
        ('paperback', 'Broché'),
        ('pocket', 'Format poche'),
        ('large_print', 'Gros caractères'),
    ], string='Format physique')
    
    digital_format = fields.Selection([
        ('pdf', 'PDF'),
        ('epub', 'EPUB'),
        ('mobi', 'MOBI'),
        ('audiobook', 'Livre audio'),
        ('online', 'Lecture en ligne'),
    ], string='Format numérique')
    
    # Localisation et stock
    location = fields.Char(
        string='Emplacement',
        help='Emplacement physique dans la bibliothèque'
    )
    
    shelf_number = fields.Char(
        string='Numéro de rayon'
    )
    
    dewey_decimal = fields.Char(
        string='Classification Dewey',
        help='Numéro de classification décimale Dewey'
    )
    
    # Gestion des exemplaires
    total_copies = fields.Integer(
        string='Nombre total d\'exemplaires',
        default=1,
        tracking=True
    )
    
    available_copies = fields.Integer(
        string='Exemplaires disponibles',
        compute='_compute_available_copies',
        store=True
    )
    
    loaned_copies = fields.Integer(
        string='Exemplaires prêtés',
        compute='_compute_loaned_copies',
        store=True
    )
    
    reserved_copies = fields.Integer(
        string='Exemplaires réservés',
        compute='_compute_reserved_copies',
        store=True
    )
    
    damaged_copies = fields.Integer(
        string='Exemplaires endommagés',
        default=0
    )
    
    lost_copies = fields.Integer(
        string='Exemplaires perdus',
        default=0
    )
    
    # États et statuts
    state = fields.Selection([
        ('available', 'Disponible'),
        ('loaned', 'Prêté'),
        ('reserved', 'Réservé'),
        ('maintenance', 'En maintenance'),
        ('lost', 'Perdu'),
        ('damaged', 'Endommagé'),
        ('archived', 'Archivé'),
    ], string='État', default='available', tracking=True)
    
    is_digital = fields.Boolean(
        string='Numérique',
        compute='_compute_is_digital',
        store=True
    )
    
    is_available = fields.Boolean(
        string='Disponible',
        compute='_compute_is_available',
        store=True
    )
    
    can_be_loaned = fields.Boolean(
        string='Peut être emprunté',
        default=True,
        help='Ce livre peut-il être emprunté?'
    )
    
    # Informations financières
    purchase_price = fields.Float(
        string='Prix d\'achat',
        help='Prix d\'achat du livre'
    )
    
    current_value = fields.Float(
        string='Valeur actuelle',
        help='Valeur actuelle estimée'
    )
    
    replacement_cost = fields.Float(
        string='Coût de remplacement',
        help='Coût pour remplacer ce livre'
    )
    
    # Dates importantes
    acquisition_date = fields.Date(
        string='Date d\'acquisition',
        default=fields.Date.today
    )
    
    last_inventory_date = fields.Date(
        string='Dernier inventaire'
    )
    
    # Fichiers numériques
    digital_file = fields.Binary(
        string='Fichier numérique',
        help='Fichier du livre numérique'
    )
    
    digital_file_name = fields.Char(
        string='Nom du fichier'
    )
    
    digital_file_size = fields.Float(
        string='Taille du fichier (MB)'
    )
    
    preview_file = fields.Binary(
        string='Aperçu',
        help='Aperçu ou extrait du livre'
    )
    
    # URLs et liens
    external_url = fields.Char(
        string='URL externe',
        help='Lien vers une version en ligne'
    )
    
    publisher_url = fields.Char(
        string='URL éditeur'
    )
    
    # Métadonnées et tags
    tags = fields.Char(
        string='Mots-clés',
        help='Mots-clés séparés par des virgules'
    )
    
    age_range = fields.Selection([
        ('children', 'Enfants (0-12 ans)'),
        ('young_adult', 'Jeunes adultes (13-17 ans)'),
        ('adult', 'Adultes (18+ ans)'),
        ('all_ages', 'Tous âges'),
    ], string='Tranche d\'âge', default='all_ages')
    
    difficulty_level = fields.Selection([
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert'),
    ], string='Niveau de difficulté')
    
    # Relations avec les emprunts
    loan_ids = fields.One2many(
        'library.loan',
        'book_id',
        string='Emprunts'
    )
    
    reservation_ids = fields.One2many(
        'library.reservation',
        'book_id',
        string='Réservations'
    )
    
    # Statistiques
    total_loans = fields.Integer(
        string='Total emprunts',
        compute='_compute_statistics'
    )
    
    popularity_score = fields.Float(
        string='Score de popularité',
        compute='_compute_popularity_score',
        store=True
    )
    
    average_rating = fields.Float(
        string='Note moyenne',
        compute='_compute_average_rating'
    )
    
    rating_count = fields.Integer(
        string='Nombre d\'évaluations',
        compute='_compute_rating_count'
    )
    
    # QR Code et code-barres
    qr_code = fields.Binary(
        string='QR Code',
        compute='_compute_qr_code'
    )
    
    barcode_image = fields.Binary(
        string='Image code-barres',
        compute='_compute_barcode_image'
    )
    
    # Recommandations IA
    recommended_books = fields.Many2many(
        'library.book',
        'book_recommendation_rel',
        'book_id',
        'recommended_id',
        string='Livres recommandés'
    )
    
    # Métadonnées système
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    
    @api.depends('format_type')
    def _compute_is_digital(self):
        """Déterminer si le livre est numérique"""
        for book in self:
            book.is_digital = book.format_type in ['digital', 'audio', 'hybrid']
    
    @api.depends('total_copies', 'loaned_copies', 'damaged_copies', 'lost_copies', 'state')
    def _compute_available_copies(self):
        """Calculer le nombre d'exemplaires disponibles"""
        for book in self:
            if book.is_digital:
                book.available_copies = 999  # Illimité pour les livres numériques
            else:
                book.available_copies = max(0, 
                    book.total_copies - book.loaned_copies - 
                    book.damaged_copies - book.lost_copies
                )
    
    @api.depends('loan_ids')
    def _compute_loaned_copies(self):
        """Calculer le nombre d'exemplaires prêtés"""
        for book in self:
            active_loans = book.loan_ids.filtered(
                lambda x: x.state in ['loaned', 'overdue']
            )
            book.loaned_copies = len(active_loans)
    
    @api.depends('reservation_ids')
    def _compute_reserved_copies(self):
        """Calculer le nombre d'exemplaires réservés"""
        for book in self:
            active_reservations = book.reservation_ids.filtered(
                lambda x: x.state == 'active'
            )
            book.reserved_copies = len(active_reservations)
    
    @api.depends('available_copies', 'can_be_loaned', 'state')
    def _compute_is_available(self):
        """Déterminer si le livre est disponible"""
        for book in self:
            book.is_available = (
                book.available_copies > 0 and 
                book.can_be_loaned and 
                book.state == 'available'
            )
    
    @api.depends('loan_ids')
    def _compute_statistics(self):
        """Calculer les statistiques du livre"""
        for book in self:
            book.total_loans = len(book.loan_ids.filtered(
                lambda x: x.state != 'cancelled'
            ))
    
    @api.depends('total_loans', 'average_rating', 'acquisition_date')
    def _compute_popularity_score(self):
        """Calculer le score de popularité"""
        for book in self:
            # Algorithme simple de popularité
            loans_score = book.total_loans * 10
            rating_score = book.average_rating * 20 if book.average_rating else 0
            
            # Facteur de récence (livres récents ont un bonus)
            if book.acquisition_date:
                days_since_acquisition = (fields.Date.today() - book.acquisition_date).days
                recency_score = max(0, 100 - (days_since_acquisition / 365) * 10)
            else:
                recency_score = 0
            
            book.popularity_score = loans_score + rating_score + recency_score
    
    def _compute_average_rating(self):
        """Calculer la note moyenne"""
        # TODO: Implémenter le système de notation
        for book in self:
            book.average_rating = 0.0
    
    def _compute_rating_count(self):
        """Calculer le nombre d'évaluations"""
        # TODO: Implémenter le système de notation
        for book in self:
            book.rating_count = 0
    
    def _compute_qr_code(self):
        """Générer le QR code du livre"""
        for book in self:
            if book.id:
                # Créer l'URL pour le livre
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                book_url = f"{base_url}/library/book/{book.id}"
                
                # Générer le QR code
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(book_url)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convertir en base64
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                book.qr_code = base64.b64encode(buffer.getvalue())
            else:
                book.qr_code = False
    
    def _compute_barcode_image(self):
        """Générer l'image du code-barres"""
        for book in self:
            if book.barcode:
                try:
                    from barcode import Code128
                    from barcode.writer import ImageWriter
                    
                    code = Code128(book.barcode, writer=ImageWriter())
                    buffer = BytesIO()
                    code.write(buffer)
                    book.barcode_image = base64.b64encode(buffer.getvalue())
                except ImportError:
                    _logger.warning("Module 'python-barcode' non installé")
                    book.barcode_image = False
            else:
                book.barcode_image = False
    
    @api.model
    def create(self, vals):
        """Créer un livre avec code-barres automatique"""
        if not vals.get('barcode'):
            vals['barcode'] = self.env['ir.sequence'].next_by_code('edu.library.book') or '/'
        
        return super().create(vals)
    
    @api.constrains('isbn')
    def _check_isbn(self):
        """Valider l'ISBN"""
        for book in self:
            if book.isbn and len(book.isbn.replace('-', '').replace(' ', '')) not in [10, 13]:
                raise ValidationError(_('L\'ISBN doit contenir 10 ou 13 chiffres.'))
    
    @api.constrains('total_copies')
    def _check_total_copies(self):
        """Valider le nombre total d'exemplaires"""
        for book in self:
            if book.total_copies < 0:
                raise ValidationError(_('Le nombre total d\'exemplaires ne peut pas être négatif.'))
    
    def action_loan_book(self):
        """Emprunter le livre"""
        self.ensure_one()
        
        if not self.is_available:
            raise UserError(_('Ce livre n\'est pas disponible pour l\'emprunt.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Emprunter le livre'),
            'res_model': 'edu.library.loan.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_book_id': self.id,
            },
        }
    
    def action_reserve_book(self):
        """Réserver le livre"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Réserver le livre'),
            'res_model': 'edu.library.reservation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_book_id': self.id,
            },
        }
    
    def action_view_loans(self):
        """Voir les emprunts du livre"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Emprunts - %s') % self.title,
            'res_model': 'edu.library.loan',
            'view_mode': 'tree,form',
            'domain': [('book_id', '=', self.id)],
            'context': {'default_book_id': self.id},
        }
    
    def action_view_reservations(self):
        """Voir les réservations du livre"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Réservations - %s') % self.title,
            'res_model': 'edu.library.reservation',
            'view_mode': 'tree,form',
            'domain': [('book_id', '=', self.id)],
            'context': {'default_book_id': self.id},
        }
    
    def action_inventory_check(self):
        """Effectuer un contrôle d'inventaire"""
        self.ensure_one()
        
        self.write({
            'last_inventory_date': fields.Date.today(),
        })
        
        self.message_post(
            body=_('Contrôle d\'inventaire effectué. Exemplaires comptés: %d') % self.total_copies
        )
    
    def action_mark_damaged(self):
        """Marquer comme endommagé"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Marquer comme endommagé'),
            'res_model': 'edu.library.damage.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_book_id': self.id,
            },
        }
    
    def action_mark_lost(self):
        """Marquer comme perdu"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Marquer comme perdu'),
            'res_model': 'edu.library.lost.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_book_id': self.id,
            },
        }
    
    def fetch_book_metadata(self):
        """Récupérer les métadonnées du livre depuis une API externe"""
        self.ensure_one()
        
        if not self.isbn:
            raise UserError(_('ISBN requis pour récupérer les métadonnées.'))
        
        try:
            # Utiliser l'API Google Books
            isbn_clean = self.isbn.replace('-', '').replace(' ', '')
            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_clean}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('totalItems', 0) > 0:
                book_info = data['items'][0]['volumeInfo']
                
                # Mettre à jour les informations
                update_vals = {}
                
                if not self.title and book_info.get('title'):
                    update_vals['title'] = book_info['title']
                
                if not self.subtitle and book_info.get('subtitle'):
                    update_vals['subtitle'] = book_info['subtitle']
                
                if not self.description and book_info.get('description'):
                    update_vals['description'] = book_info['description']
                
                if not self.pages and book_info.get('pageCount'):
                    update_vals['pages'] = book_info['pageCount']
                
                if not self.publication_date and book_info.get('publishedDate'):
                    try:
                        pub_date = book_info['publishedDate']
                        if len(pub_date) == 4:  # Année seulement
                            update_vals['publication_date'] = f"{pub_date}-01-01"
                        else:
                            update_vals['publication_date'] = pub_date
                    except:
                        pass
                
                if update_vals:
                    self.write(update_vals)
                    
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Succès'),
                        'message': _('Métadonnées récupérées avec succès'),
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Aucune information trouvée pour cet ISBN.'))
                
        except requests.RequestException as e:
            _logger.error(f"Erreur lors de la récupération des métadonnées: {e}")
            raise UserError(_('Erreur lors de la récupération des métadonnées. Vérifiez votre connexion internet.'))
        except Exception as e:
            _logger.error(f"Erreur inattendue: {e}")
            raise UserError(_('Une erreur inattendue s\'est produite.'))
