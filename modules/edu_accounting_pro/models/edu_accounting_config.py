# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduAccountingConfig(models.Model):
    """Configuration globale du système comptable éducatif"""
    _name = 'edu.accounting.config'
    _description = 'Configuration Comptabilité Éducative'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom de la configuration',
        required=True,
        help="Nom de la configuration comptable"
    )
    
    active = fields.Boolean(
        string='Configuration active',
        default=True,
        help="Configuration actuellement utilisée"
    )
    
    # Configuration générale
    country_id = fields.Many2one(
        'res.country',
        string='Pays de l\'école',
        required=True,
        default=lambda self: self.env.company.country_id,
        help="Pays où se situe l'institution éducative"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        required=True,
        compute='_compute_currency_from_country',
        store=True,
        readonly=False,
        help="Devise principale utilisée (automatiquement définie selon le pays)"
    )
    
    manual_currency_override = fields.Boolean(
        string='Forcer la devise manuellement',
        default=False,
        help="Permet de choisir une devise différente de celle du pays"
    )
    
    fiscal_year_start = fields.Selection([
        ('january', 'Janvier'),
        ('april', 'Avril'),
        ('july', 'Juillet'),
        ('september', 'Septembre'),
        ('october', 'Octobre')
    ], string='Début année fiscale', default='september', help="Mois de début de l'année fiscale")
    
    academic_year_id = fields.Many2one(
        'op.academic.year',
        string='Année scolaire courante',
        help="Année scolaire actuellement active"
    )
    
    # Configuration facturation
    auto_generate_invoices = fields.Boolean(
        string='Génération automatique des factures',
        default=True,
        help="Générer automatiquement les factures selon les structures de frais"
    )
    
    invoice_due_days = fields.Integer(
        string='Délai de paiement (jours)',
        default=30,
        help="Délai par défaut pour le paiement des factures"
    )
    
    invoice_template_id = fields.Many2one(
        'ir.ui.view',
        string='Modèle de facture',
        help="Modèle par défaut pour les factures étudiants"
    )
    
    invoice_prefix = fields.Char(
        string='Préfixe factures',
        default='FAC',
        help="Préfixe des numéros de facture"
    )
    
    # Pénalités et frais de retard
    enable_late_fees = fields.Boolean(
        string='Frais de retard',
        default=True,
        help="Activer les frais de retard"
    )
    
    late_payment_fee_rate = fields.Float(
        string='Taux frais de retard (%)',
        default=5.0,
        digits=(5, 2),
        help="Pourcentage de frais de retard par mois"
    )
    
    grace_period_days = fields.Integer(
        string='Période de grâce (jours)',
        default=5,
        help="Nombre de jours de grâce avant application des frais de retard"
    )
    
    # Paiements en ligne
    enable_online_payments = fields.Boolean(
        string='Paiements en ligne',
        default=True,
        help="Activer les paiements en ligne"
    )
    
    stripe_publishable_key = fields.Char(
        string='Clé publique Stripe',
        help="Clé publique pour Stripe"
    )
    
    stripe_secret_key = fields.Char(
        string='Clé secrète Stripe',
        help="Clé secrète pour Stripe"
    )
    
    paypal_client_id = fields.Char(
        string='Client ID PayPal',
        help="Identifiant client PayPal"
    )
    
    paypal_client_secret = fields.Char(
        string='Secret client PayPal',
        help="Secret client PayPal"
    )
    
    # Mobile Money (Orange Money, MTN, etc.)
    enable_mobile_money = fields.Boolean(
        string='Mobile Money',
        default=True,
        help="Activer les paiements Mobile Money"
    )
    
    orange_money_merchant_id = fields.Char(
        string='ID marchand Orange Money',
        help="Identifiant marchand Orange Money"
    )
    
    orange_money_api_key = fields.Char(
        string='Clé API Orange Money',
        help="Clé API Orange Money"
    )
    
    # Remises et bourses
    enable_scholarships = fields.Boolean(
        string='Bourses et aides',
        default=True,
        help="Activer le système de bourses"
    )
    
    auto_apply_scholarships = fields.Boolean(
        string='Application automatique des bourses',
        default=True,
        help="Appliquer automatiquement les bourses éligibles"
    )
    
    max_scholarship_percentage = fields.Float(
        string='Pourcentage max de bourse (%)',
        default=100.0,
        digits=(5, 2),
        help="Pourcentage maximum de bourse accordable"
    )
    
    # Rapports et notifications
    enable_payment_reminders = fields.Boolean(
        string='Rappels de paiement',
        default=True,
        help="Envoyer des rappels de paiement automatiques"
    )
    
    reminder_days_before = fields.Integer(
        string='Rappel avant échéance (jours)',
        default=7,
        help="Nombre de jours avant échéance pour envoyer un rappel"
    )
    
    reminder_days_after = fields.Integer(
        string='Rappel après échéance (jours)',
        default=3,
        help="Nombre de jours après échéance pour envoyer un rappel"
    )
    
    generate_monthly_reports = fields.Boolean(
        string='Rapports mensuels automatiques',
        default=True,
        help="Générer automatiquement les rapports mensuels"
    )
    
    # Comptes comptables par défaut
    student_receivable_account_id = fields.Many2one(
        'account.account',
        string='Compte créances étudiants',
        domain="[('account_type', '=', 'asset_receivable')]",
        help="Compte de créances pour les étudiants"
    )
    
    tuition_income_account_id = fields.Many2one(
        'account.account',
        string='Compte produits scolarité',
        domain="[('account_type', '=', 'income')]",
        help="Compte de produits pour les frais de scolarité"
    )
    
    scholarship_expense_account_id = fields.Many2one(
        'account.account',
        string='Compte charges bourses',
        domain="[('account_type', '=', 'expense')]",
        help="Compte de charges pour les bourses"
    )
    
    late_fee_income_account_id = fields.Many2one(
        'account.account',
        string='Compte produits frais de retard',
        domain="[('account_type', '=', 'income')]",
        help="Compte de produits pour les frais de retard"
    )
    
    # Options avancées
    multi_currency_support = fields.Boolean(
        string='Support multi-devises',
        default=False,
        help="Activer le support des paiements en plusieurs devises"
    )
    
    auto_reconcile_payments = fields.Boolean(
        string='Rapprochement automatique',
        default=True,
        help="Rapprocher automatiquement les paiements avec les factures"
    )
    
    require_payment_validation = fields.Boolean(
        string='Validation des paiements obligatoire',
        default=False,
        help="Exiger une validation manuelle des paiements"
    )
    
    enable_payment_plans = fields.Boolean(
        string='Plans de paiement',
        default=True,
        help="Activer les plans de paiement échelonnés"
    )
    
    # Intégration bancaire
    enable_bank_synchronization = fields.Boolean(
        string='Synchronisation bancaire',
        default=False,
        help="Synchroniser automatiquement avec les comptes bancaires"
    )
    
    bank_sync_frequency = fields.Selection([
        ('daily', 'Quotidienne'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuelle')
    ], string='Fréquence synchronisation', default='daily')
    
    # Statistiques (calculées)
    total_invoiced_current_year = fields.Monetary(
        string='Total facturé cette année',
        compute='_compute_financial_stats',
        currency_field='currency_id',
        help="Montant total facturé cette année"
    )
    
    total_collected_current_year = fields.Monetary(
        string='Total encaissé cette année',
        compute='_compute_financial_stats',
        currency_field='currency_id',
        help="Montant total encaissé cette année"
    )
    
    outstanding_amount = fields.Monetary(
        string='En attente de paiement',
        compute='_compute_financial_stats',
        currency_field='currency_id',
        help="Montant en attente de paiement"
    )
    
    collection_rate = fields.Float(
        string='Taux de recouvrement (%)',
        compute='_compute_financial_stats',
        digits=(5, 2),
        help="Pourcentage de recouvrement"
    )
    
    # Calculs
    def _compute_financial_stats(self):
        """Calcule les statistiques financières"""
        for record in self:
            # Année académique courante
            if record.academic_year_id:
                year_start = record.academic_year_id.start_date
                year_end = record.academic_year_id.end_date
            else:
                # Utiliser l'année civile courante
                import datetime
                today = datetime.date.today()
                year_start = datetime.date(today.year, 1, 1)
                year_end = datetime.date(today.year, 12, 31)
            
            # Factures de l'année
            invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('invoice_date', '>=', year_start),
                ('invoice_date', '<=', year_end),
                ('student_id', '!=', False)
            ])
            
            record.total_invoiced_current_year = sum(invoices.mapped('amount_total'))
            record.total_collected_current_year = sum(invoices.mapped('amount_paid'))
            record.outstanding_amount = record.total_invoiced_current_year - record.total_collected_current_year
            
            if record.total_invoiced_current_year > 0:
                record.collection_rate = (record.total_collected_current_year / record.total_invoiced_current_year) * 100
            else:
                record.collection_rate = 0.0
    
    # Contraintes
    @api.constrains('late_payment_fee_rate')
    def _check_late_fee_rate(self):
        """Vérifie le taux des frais de retard"""
        for record in self:
            if record.late_payment_fee_rate < 0 or record.late_payment_fee_rate > 50:
                raise ValidationError(_("Le taux de frais de retard doit être entre 0% et 50%"))
    
    @api.constrains('max_scholarship_percentage')
    def _check_scholarship_percentage(self):
        """Vérifie le pourcentage maximum de bourse"""
        for record in self:
            if record.max_scholarship_percentage < 0 or record.max_scholarship_percentage > 100:
                raise ValidationError(_("Le pourcentage de bourse doit être entre 0% et 100%"))
    
    @api.constrains('invoice_due_days')
    def _check_due_days(self):
        """Vérifie le délai de paiement"""
        for record in self:
            if record.invoice_due_days < 1 or record.invoice_due_days > 365:
                raise ValidationError(_("Le délai de paiement doit être entre 1 et 365 jours"))
    
    # Actions
    def action_test_stripe_connection(self):
        """Teste la connexion Stripe"""
        self.ensure_one()
        if not (self.stripe_publishable_key and self.stripe_secret_key):
            raise ValidationError(_("Veuillez configurer les clés Stripe"))
        
        try:
            import stripe
            stripe.api_key = self.stripe_secret_key
            
            # Test simple
            stripe.Account.retrieve()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Connexion Stripe testée avec succès"),
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': _("Erreur Stripe: %s") % str(e),
                    'type': 'danger',
                }
            }
    
    def action_generate_monthly_invoices(self):
        """Génère les factures mensuelles"""
        self.ensure_one()
        if not self.auto_generate_invoices:
            raise ValidationError(_("La génération automatique n'est pas activée"))
        
        # Lancer le wizard de génération
        return {
            'type': 'ir.actions.act_window',
            'name': _('Génération des factures mensuelles'),
            'res_model': 'edu.fee.generation.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_send_payment_reminders(self):
        """Envoie les rappels de paiement"""
        self.ensure_one()
        count = 0
        
        if self.enable_payment_reminders:
            # Rappels avant échéance
            import datetime
            reminder_date = datetime.date.today() + datetime.timedelta(days=self.reminder_days_before)
            
            overdue_invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '!=', 'paid'),
                ('invoice_date_due', '=', reminder_date),
                ('student_id', '!=', False)
            ])
            
            for invoice in overdue_invoices:
                # Envoyer rappel (intégration avec edu_communication_hub)
                count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("%d rappels envoyés") % count,
                'type': 'success',
            }
        }
    
    def action_financial_dashboard(self):
        """Ouvre le tableau de bord financier"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tableau de bord financier'),
            'res_model': 'edu.accounting.analytics',
            'view_mode': 'kanban,tree,form',
            'target': 'current',
        }
    
    @api.model
    def get_active_config(self):
        """Retourne la configuration active"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            # Créer une configuration par défaut
            config = self.create({
                'name': 'Configuration par défaut',
                'active': True,
            })
        return config

    @api.depends('country_id', 'manual_currency_override')
    def _compute_currency_from_country(self):
        """Calcule automatiquement la devise selon le pays"""
        for record in self:
            if not record.manual_currency_override and record.country_id:
                # Mapping des pays vers leurs devises principales
                currency_mapping = self._get_country_currency_mapping()
                
                if record.country_id.code in currency_mapping:
                    currency_code = currency_mapping[record.country_id.code]
                    currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
                    if currency:
                        record.currency_id = currency
                    else:
                        # Fallback vers la devise de la société
                        record.currency_id = self.env.company.currency_id
                else:
                    # Utiliser la devise du pays si disponible, sinon celle de la société
                    if record.country_id.currency_id:
                        record.currency_id = record.country_id.currency_id
                    else:
                        record.currency_id = self.env.company.currency_id
            elif not record.currency_id:
                # Fallback par défaut
                record.currency_id = self.env.company.currency_id

    @api.model
    def _get_country_currency_mapping(self):
        """Retourne le mapping des codes pays vers les devises"""
        return {
            # Afrique de l'Ouest (CFA)
            'SN': 'XOF',  # Sénégal - Franc CFA
            'CI': 'XOF',  # Côte d'Ivoire - Franc CFA
            'BF': 'XOF',  # Burkina Faso - Franc CFA
            'ML': 'XOF',  # Mali - Franc CFA
            'NE': 'XOF',  # Niger - Franc CFA
            'TG': 'XOF',  # Togo - Franc CFA
            'BJ': 'XOF',  # Bénin - Franc CFA
            'GW': 'XOF',  # Guinée-Bissau - Franc CFA
            
            # Afrique Centrale (CFA)
            'CM': 'XAF',  # Cameroun - Franc CFA Central
            'GA': 'XAF',  # Gabon - Franc CFA Central
            'CG': 'XAF',  # Congo - Franc CFA Central
            'CF': 'XAF',  # République Centrafricaine - Franc CFA Central
            'TD': 'XAF',  # Tchad - Franc CFA Central
            'GQ': 'XAF',  # Guinée Équatoriale - Franc CFA Central
            
            # Europe (Euro)
            'FR': 'EUR',  # France - Euro
            'DE': 'EUR',  # Allemagne - Euro
            'ES': 'EUR',  # Espagne - Euro
            'IT': 'EUR',  # Italie - Euro
            'PT': 'EUR',  # Portugal - Euro
            'BE': 'EUR',  # Belgique - Euro
            'NL': 'EUR',  # Pays-Bas - Euro
            'AT': 'EUR',  # Autriche - Euro
            'IE': 'EUR',  # Irlande - Euro
            'FI': 'EUR',  # Finlande - Euro
            'GR': 'EUR',  # Grèce - Euro
            'LU': 'EUR',  # Luxembourg - Euro
            'MT': 'EUR',  # Malte - Euro
            'CY': 'EUR',  # Chypre - Euro
            'SK': 'EUR',  # Slovaquie - Euro
            'SI': 'EUR',  # Slovénie - Euro
            'EE': 'EUR',  # Estonie - Euro
            'LV': 'EUR',  # Lettonie - Euro
            'LT': 'EUR',  # Lituanie - Euro
            
            # Autres devises principales
            'US': 'USD',  # États-Unis - Dollar américain
            'CA': 'CAD',  # Canada - Dollar canadien
            'GB': 'GBP',  # Royaume-Uni - Livre sterling
            'CH': 'CHF',  # Suisse - Franc suisse
            'JP': 'JPY',  # Japon - Yen
            'CN': 'CNY',  # Chine - Yuan
            'IN': 'INR',  # Inde - Roupie indienne
            'BR': 'BRL',  # Brésil - Réal brésilien
            'MX': 'MXN',  # Mexique - Peso mexicain
            'AU': 'AUD',  # Australie - Dollar australien
            'NZ': 'NZD',  # Nouvelle-Zélande - Dollar néo-zélandais
            'ZA': 'ZAR',  # Afrique du Sud - Rand
            'EG': 'EGP',  # Égypte - Livre égyptienne
            'NG': 'NGN',  # Nigeria - Naira
            'KE': 'KES',  # Kenya - Shilling kenyan
            'GH': 'GHS',  # Ghana - Cedi ghanéen
            'MA': 'MAD',  # Maroc - Dirham marocain
            'TN': 'TND',  # Tunisie - Dinar tunisien
            'DZ': 'DZD',  # Algérie - Dinar algérien
            'RU': 'RUB',  # Russie - Rouble russe
            'TR': 'TRY',  # Turquie - Livre turque
            'AE': 'AED',  # Émirats Arabes Unis - Dirham
            'SA': 'SAR',  # Arabie Saoudite - Riyal saoudien
            'QA': 'QAR',  # Qatar - Riyal qatarien
            'KW': 'KWD',  # Koweït - Dinar koweïtien
            'BH': 'BHD',  # Bahreïn - Dinar bahreïni
            'OM': 'OMR',  # Oman - Rial omanais
            'JO': 'JOD',  # Jordanie - Dinar jordanien
            'LB': 'LBP',  # Liban - Livre libanaise
            'SY': 'SYP',  # Syrie - Livre syrienne
            'IQ': 'IQD',  # Irak - Dinar irakien
            'IR': 'IRR',  # Iran - Rial iranien
            'AF': 'AFN',  # Afghanistan - Afghani
            'PK': 'PKR',  # Pakistan - Roupie pakistanaise
            'BD': 'BDT',  # Bangladesh - Taka
            'LK': 'LKR',  # Sri Lanka - Roupie sri-lankaise
            'TH': 'THB',  # Thaïlande - Baht thaïlandais
            'VN': 'VND',  # Vietnam - Dong vietnamien
            'MY': 'MYR',  # Malaisie - Ringgit malaisien
            'SG': 'SGD',  # Singapour - Dollar singapourien
            'ID': 'IDR',  # Indonésie - Roupie indonésienne
            'PH': 'PHP',  # Philippines - Peso philippin
            'KR': 'KRW',  # Corée du Sud - Won sud-coréen
            'TW': 'TWD',  # Taïwan - Dollar taïwanais
            'HK': 'HKD',  # Hong Kong - Dollar de Hong Kong
            'MO': 'MOP',  # Macao - Pataca de Macao
        }

    @api.onchange('country_id')
    def _onchange_country_id(self):
        """Met à jour la devise quand le pays change"""
        if self.country_id and not self.manual_currency_override:
            self._compute_currency_from_country()

    @api.onchange('manual_currency_override')
    def _onchange_manual_currency_override(self):
        """Recalcule la devise quand l'override manuel change"""
        if not self.manual_currency_override:
            self._compute_currency_from_country()

    def action_suggest_currency_by_country(self):
        """Action pour suggérer la devise selon le pays"""
        self.ensure_one()
        if self.country_id:
            currency_mapping = self._get_country_currency_mapping()
            suggested_currency = None
            
            if self.country_id.code in currency_mapping:
                currency_code = currency_mapping[self.country_id.code]
                suggested_currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
            elif self.country_id.currency_id:
                suggested_currency = self.country_id.currency_id
            
            if suggested_currency:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Devise suggérée'),
                        'message': _('Pour %s, nous suggérons : %s (%s)') % (
                            self.country_id.name, 
                            suggested_currency.name, 
                            suggested_currency.full_name or suggested_currency.name
                        ),
                        'type': 'info',
                        'sticky': False,
                    }
                }
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Aucune suggestion'),
                'message': _('Aucune devise spécifique suggérée pour ce pays.'),
                'type': 'warning',
                'sticky': False,
            }
        }

