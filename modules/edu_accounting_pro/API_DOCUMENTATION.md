# API REST Documentation - edu_accounting_pro

## Vue d'ensemble

Le module `edu_accounting_pro` fournit une suite complète d'APIs REST JSON pour la gestion comptable éducative. Toutes les APIs suivent les mêmes conventions :

- **Type de route** : `type='json'`
- **Authentification** : `auth='user'` (utilisateur connecté requis)
- **Méthode HTTP** : `POST` pour tous les endpoints
- **Format des données** : JSON dans le corps de la requête
- **CSRF** : Désactivé (`csrf=False`)

## Format de réponse standard

```json
{
  "success": true|false,
  "data": { ... },       // Si success=true
  "error": "message"     // Si success=false
}
```

## 1. Fee Structure Controller (`/api/fee-structure/*`)

### Endpoints disponibles
- `POST /api/fee-structure` - Liste des structures de frais
- `POST /api/fee-structure/get` - Détail d'une structure
- `POST /api/fee-structure/create` - Créer une structure
- `POST /api/fee-structure/update` - Mettre à jour une structure
- `POST /api/fee-structure/delete` - Supprimer une structure
- `POST /api/fee-structure/duplicate` - Dupliquer une structure
- `POST /api/fee-structure/activate` - Activer une structure
- `POST /api/fee-structure/stats` - Statistiques

### Paramètres principaux
- `structure_id` : ID de la structure (requis pour get/update/delete/duplicate/activate)
- `name` : Nom de la structure
- `code` : Code unique
- `academic_year_id` : Année académique
- `course_id` : Cours associé
- `total_amount` : Montant total

## 2. Fee Type Controller (`/api/fee-type/*`)

### Endpoints disponibles
- `POST /api/fee-type` - Liste des types de frais
- `POST /api/fee-type/get` - Détail d'un type
- `POST /api/fee-type/create` - Créer un type
- `POST /api/fee-type/update` - Mettre à jour un type
- `POST /api/fee-type/delete` - Supprimer un type
- `POST /api/fee-type/set-default` - Définir comme défaut
- `POST /api/fee-type/stats` - Statistiques

### Paramètres principaux
- `fee_type_id` : ID du type de frais
- `name` : Nom du type
- `code` : Code unique
- `amount` : Montant
- `is_mandatory` : Obligatoire (true/false)

## 3. Student Invoice Controller (`/api/student-invoice/*`)

### Endpoints disponibles
- `POST /api/student-invoice` - Liste des factures
- `POST /api/student-invoice/get` - Détail d'une facture
- `POST /api/student-invoice/create` - Créer une facture
- `POST /api/student-invoice/update` - Mettre à jour une facture
- `POST /api/student-invoice/delete` - Supprimer une facture
- `POST /api/student-invoice/confirm` - Confirmer une facture
- `POST /api/student-invoice/cancel` - Annuler une facture
- `POST /api/student-invoice/send-reminder` - Envoyer rappel
- `POST /api/student-invoice/stats` - Statistiques

### Paramètres principaux
- `invoice_id` : ID de la facture
- `student_id` : ID de l'étudiant (requis pour create)
- `amount_total` : Montant total
- `due_date` : Date d'échéance
- `state` : État (draft, open, paid, cancel)

## 4. Student Payment Controller (`/api/student-payment/*`)

### Endpoints disponibles
- `POST /api/student-payment` - Liste des paiements
- `POST /api/student-payment/get` - Détail d'un paiement
- `POST /api/student-payment/create` - Créer un paiement
- `POST /api/student-payment/update` - Mettre à jour un paiement
- `POST /api/student-payment/delete` - Supprimer un paiement
- `POST /api/student-payment/validate` - Valider un paiement
- `POST /api/student-payment/cancel` - Annuler un paiement
- `POST /api/student-payment/receipt` - Générer reçu
- `POST /api/student-payment/stats` - Statistiques

### Paramètres principaux
- `payment_id` : ID du paiement
- `student_id` : ID de l'étudiant (requis pour create)
- `amount` : Montant du paiement
- `payment_method_id` : Méthode de paiement
- `reference` : Référence du paiement

## 5. Fee Collection Controller (`/api/fee-collection/*`)

### Endpoints disponibles
- `POST /api/fee-collection` - Liste des collectes
- `POST /api/fee-collection/get` - Détail d'une collecte
- `POST /api/fee-collection/create` - Créer une collecte
- `POST /api/fee-collection/update` - Mettre à jour une collecte
- `POST /api/fee-collection/start` - Démarrer une collecte
- `POST /api/fee-collection/stats` - Statistiques

### Paramètres principaux
- `collection_id` : ID de la collecte
- `name` : Nom de la collecte
- `academic_year_id` : Année académique
- `course_id` : Cours
- `start_date` : Date de début
- `end_date` : Date de fin

## 6. Payment Plan Controller (`/api/payment-plan/*`)

### Endpoints disponibles
- `POST /api/payment-plan` - Liste des plans de paiement
- `POST /api/payment-plan/get` - Détail d'un plan
- `POST /api/payment-plan/create` - Créer un plan
- `POST /api/payment-plan/update` - Mettre à jour un plan
- `POST /api/payment-plan/delete` - Supprimer un plan
- `POST /api/payment-plan/activate` - Activer un plan
- `POST /api/payment-plan/calculate` - Calculer échéances
- `POST /api/payment-plan/stats` - Statistiques

### Paramètres principaux
- `plan_id` : ID du plan
- `student_id` : ID de l'étudiant
- `total_amount` : Montant total
- `installments` : Nombre d'échéances
- `start_date` : Date de début

## 7. Scholarship Controller (`/api/scholarship/*`)

### Endpoints disponibles
- `POST /api/scholarship` - Liste des bourses
- `POST /api/scholarship/get` - Détail d'une bourse
- `POST /api/scholarship/create` - Créer une bourse
- `POST /api/scholarship/update` - Mettre à jour une bourse
- `POST /api/scholarship/delete` - Supprimer une bourse
- `POST /api/scholarship/approve` - Approuver une bourse
- `POST /api/scholarship/reject` - Rejeter une bourse
- `POST /api/scholarship/stats` - Statistiques

### Paramètres principaux
- `scholarship_id` : ID de la bourse
- `student_id` : ID de l'étudiant
- `amount` : Montant de la bourse
- `type` : Type de bourse
- `criteria` : Critères d'attribution

## 8. Discount Controller (`/api/discount/*`)

### Endpoints disponibles
- `POST /api/discount` - Liste des remises
- `POST /api/discount/get` - Détail d'une remise
- `POST /api/discount/create` - Créer une remise
- `POST /api/discount/update` - Mettre à jour une remise
- `POST /api/discount/delete` - Supprimer une remise
- `POST /api/discount/apply` - Appliquer remise
- `POST /api/discount/calculate` - Calculer montant remise
- `POST /api/discount/stats` - Statistiques

### Paramètres principaux
- `discount_id` : ID de la remise
- `name` : Nom de la remise
- `discount_type` : Type (percentage/amount)
- `value` : Valeur de la remise
- `conditions` : Conditions d'application

## 9. Payment Method Controller (`/api/payment-method/*`)

### Endpoints disponibles
- `POST /api/payment-method` - Liste des méthodes
- `POST /api/payment-method/get` - Détail d'une méthode
- `POST /api/payment-method/create` - Créer une méthode
- `POST /api/payment-method/update` - Mettre à jour une méthode
- `POST /api/payment-method/set-default` - Définir par défaut
- `POST /api/payment-method/calculate-fees` - Calculer frais
- `POST /api/payment-method/stats` - Statistiques

### Paramètres principaux
- `method_id` : ID de la méthode
- `name` : Nom de la méthode
- `method_type` : Type (cash, card, bank_transfer, etc.)
- `fee_percentage` : Pourcentage de frais
- `fixed_fee` : Frais fixes

## 10. Accounting Config Controller (`/api/accounting-config/*`)

### Endpoints disponibles
- `POST /api/accounting-config` - Liste des configurations
- `POST /api/accounting-config/get` - Détail d'une configuration
- `POST /api/accounting-config/create` - Créer une configuration
- `POST /api/accounting-config/update` - Mettre à jour une configuration
- `POST /api/accounting-config/set-default` - Définir par défaut
- `POST /api/accounting-config/validate` - Valider configuration
- `POST /api/accounting-config/duplicate` - Dupliquer
- `POST /api/accounting-config/types` - Types disponibles
- `POST /api/accounting-config/stats` - Statistiques

### Paramètres principaux
- `config_id` : ID de la configuration
- `name` : Nom de la configuration
- `company_id` : Société
- `currency_id` : Devise
- `default_account_ids` : Comptes par défaut

## 11. Financial Aid Controller (`/api/financial-aid/*`)

### Endpoints disponibles
- `POST /api/financial-aid` - Liste des aides
- `POST /api/financial-aid/get` - Détail d'une aide
- `POST /api/financial-aid/create` - Créer une aide
- `POST /api/financial-aid/update` - Mettre à jour une aide
- `POST /api/financial-aid/approve` - Approuver une aide
- `POST /api/financial-aid/reject` - Rejeter une aide
- `POST /api/financial-aid/disburse` - Décaisser une aide
- `POST /api/financial-aid/stats` - Statistiques

### Paramètres principaux
- `aid_id` : ID de l'aide
- `student_id` : ID de l'étudiant
- `amount` : Montant de l'aide
- `percentage` : Pourcentage (mutuellement exclusif avec amount)
- `start_date` : Date de début
- `end_date` : Date de fin

## 12. Accounting Dashboard Controller (`/api/dashboard/*`)

### Endpoints disponibles
- `POST /api/dashboard/overview` - Vue d'ensemble
- `POST /api/dashboard/revenue-trends` - Tendances revenus
- `POST /api/dashboard/payment-analysis` - Analyse des paiements
- `POST /api/dashboard/overdue-analysis` - Analyse retards
- `POST /api/dashboard/student-ranking` - Classement étudiants
- `POST /api/dashboard/kpis` - Indicateurs clés

### Paramètres principaux
- `date_from` : Date de début
- `date_to` : Date de fin
- `academic_year_id` : Année académique
- `course_id` : Cours

## 13. Reports Controller (`/api/reports/*`)

### Endpoints disponibles
- `POST /api/reports/financial-summary` - Synthèse financière
- `POST /api/reports/student-account-statement` - Relevé étudiant
- `POST /api/reports/fee-collection-report` - Rapport collecte
- `POST /api/reports/payment-analysis` - Analyse paiements
- `POST /api/reports/overdue-students` - Étudiants en retard
- `POST /api/reports/export` - Export de rapport

### Paramètres principaux
- `report_type` : Type de rapport
- `format` : Format d'export (json, csv, xlsx)
- `student_id` : ID étudiant (pour relevé)
- `days_overdue` : Jours de retard (pour retards)

## 14. Utils Controller (`/api/utils/*`)

### Endpoints disponibles
- `POST /api/utils/academic-years` - Années académiques
- `POST /api/utils/courses` - Liste des cours
- `POST /api/utils/students` - Liste des étudiants
- `POST /api/utils/payment-methods` - Méthodes de paiement
- `POST /api/utils/calculate-total` - Calcul de montant
- `POST /api/utils/validate-payment` - Validation paiement
- `POST /api/utils/system-info` - Informations système
- `POST /api/utils/health-check` - Vérification santé

### Paramètres principaux
- `active_only` : Seulement les actifs (true/false)
- `search_term` : Terme de recherche
- `limit` : Limite de résultats
- `offset` : Décalage pour pagination

## Paramètres de pagination communs

```json
{
  "limit": 20,        // Nombre d'éléments par page (défaut: 20)
  "offset": 0,        // Décalage (défaut: 0)
  "order": "name asc" // Ordre de tri (optionnel)
}
```

## Filtres de date communs

```json
{
  "date_from": "2024-01-01",
  "date_to": "2024-12-31",
  "academic_year_id": 1,
  "course_id": 1
}
```

## Gestion des erreurs

Toutes les erreurs retournent un format standard :

```json
{
  "success": false,
  "error": "Message d'erreur descriptif"
}
```

Les erreurs sont également loggées côté serveur pour le débogage.

## Authentification

Toutes les APIs requièrent une authentification utilisateur Odoo valide. L'utilisateur doit avoir les permissions appropriées pour accéder aux modèles concernés.

## Exemples d'utilisation

### Créer une facture étudiant
```javascript
fetch('/api/student-invoice/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    student_id: 123,
    amount_total: 1000.00,
    due_date: '2024-12-31',
    description: 'Frais de scolarité'
  })
})
```

### Récupérer les statistiques de paiement
```javascript
fetch('/api/student-payment/stats', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    date_from: '2024-01-01',
    date_to: '2024-12-31'
  })
})
```

Cette documentation couvre l'ensemble des APIs REST disponibles dans le module edu_accounting_pro. Toutes les APIs suivent les mêmes conventions et formats de réponse pour assurer une intégration cohérente.
