# Tests API pour edu_accounting_pro

Ce module contient des scripts de test pour valider les APIs REST du module `edu_accounting_pro`.

## 📋 Prérequis

- Python 3.6 ou plus récent
- Module `requests` Python: `pip install requests`
- Instance Odoo 17 en cours d'exécution
- Module `edu_accounting_pro` installé dans Odoo

## 🚀 Scripts de test disponibles

### 1. Script de test automatisé complet
**Fichier**: `tests/test_api_endpoints.py`

Ce script exécute tous les tests de manière automatisée et génère un rapport complet.

```bash
cd addons/custom/edu_accounting_pro
python3 tests/test_api_endpoints.py
```

### 2. Script de test interactif
**Fichier**: `interactive_api_test.py`

Interface interactive pour tester les endpoints individuellement.

```bash
cd addons/custom/edu_accounting_pro
python3 interactive_api_test.py
```

### 3. Script bash automatisé
**Fichier**: `run_api_tests.sh`

Script bash qui configure et lance les tests automatiquement.

```bash
cd addons/custom/edu_accounting_pro
chmod +x run_api_tests.sh
./run_api_tests.sh
```

## ⚙️ Configuration

### Fichier de configuration
**Fichier**: `test_config.py`

Modifiez ce fichier pour adapter les paramètres de test à votre environnement:

```python
# Configuration de connexion Odoo
ODOO_CONFIG = {
    'BASE_URL': 'http://localhost:8069',  # URL de votre instance Odoo
    'DATABASE': 'test_db',                # Nom de votre base de données
    'USERNAME': 'admin',                  # Nom d'utilisateur
    'PASSWORD': 'admin'                   # Mot de passe
}

# Configuration des tests
TEST_CONFIG = {
    'ACADEMIC_YEAR_ID': 1,    # ID d'une année académique existante
    'COURSE_ID': 1,           # ID d'un cours existant
    'STUDENT_ID': 1,          # ID d'un étudiant existant
    'FEE_TYPE_ID': 1,         # ID d'un type de frais existant
    'PAYMENT_METHOD_ID': 1,   # ID d'une méthode de paiement existante
    # ...
}
```

## 🔍 Endpoints testés

### 1. Fee Structure (Structure de frais)
- `GET /api/fee-structures` - Liste des structures
- `POST /api/fee-structures/create` - Création d'une structure
- `POST /api/fee-structures/get` - Récupération d'une structure
- `POST /api/fee-structures/update` - Mise à jour d'une structure
- `POST /api/fee-structures/delete` - Suppression d'une structure
- `POST /api/fee-structures/generate-invoices` - Génération de factures

### 2. Fee Type (Type de frais)
- `GET /api/fee-types` - Liste des types
- `POST /api/fee-types/create` - Création d'un type
- `POST /api/fee-types/get` - Récupération d'un type
- `POST /api/fee-types/update` - Mise à jour d'un type
- `POST /api/fee-types/delete` - Suppression d'un type

### 3. Student Invoice (Facture étudiant)
- `GET /api/student-invoices` - Liste des factures
- `POST /api/student-invoices/create` - Création d'une facture
- `POST /api/student-invoices/get` - Récupération d'une facture
- `POST /api/student-invoices/confirm` - Confirmation d'une facture
- `POST /api/student-invoices/cancel` - Annulation d'une facture

### 4. Student Payment (Paiement étudiant)
- `GET /api/student-payments` - Liste des paiements
- `POST /api/student-payments/create` - Création d'un paiement
- `POST /api/student-payments/get` - Récupération d'un paiement
- `POST /api/student-payments/validate` - Validation d'un paiement
- `POST /api/student-payments/cancel` - Annulation d'un paiement

### 5. Dashboard (Tableau de bord)
- `GET /api/accounting-dashboard/stats` - Statistiques
- `GET /api/accounting-dashboard/charts` - Données graphiques

### 6. Configuration
- `GET /api/accounting-config` - Configuration du module

## 🎯 Utilisation du script interactif

1. **Lancer le script**:
   ```bash
   python3 interactive_api_test.py
   ```

2. **Menu principal**:
   ```
   📋 MENU PRINCIPAL
   ────────────────────────────────────────
   1. Tester tous les endpoints
   2. Tester un endpoint spécifique
   3. Tester les endpoints Fee Structure
   4. Tester les endpoints Fee Type
   5. Tester les endpoints Student Invoice
   6. Tester les endpoints Student Payment
   7. Tester les endpoints Dashboard
   8. Tester un endpoint personnalisé
   9. Afficher la configuration actuelle
   0. Quitter
   ```

3. **Tester un endpoint personnalisé**:
   - Choisir l'option 8
   - Entrer l'endpoint (ex: `/api/fee-structures`)
   - Entrer les données JSON (optionnel)
   - Voir la réponse complète

## 📊 Rapports de test

Les tests génèrent des rapports détaillés:

- **Format JSON**: `test_report_YYYYMMDD_HHMMSS.json`
- **Contenu**: Résultats détaillés de chaque test
- **Informations**: Succès/échec, messages d'erreur, timestamps

### Exemple de rapport:
```json
{
  "test_name": "Fee Structure - Liste",
  "success": true,
  "message": "Récupération de 5 structures",
  "timestamp": "2024-01-15T10:30:00",
  "data": {...}
}
```

## 🛠️ Débogage

### Erreurs communes

1. **Erreur d'authentification**:
   - Vérifier les identifiants dans `test_config.py`
   - S'assurer que l'utilisateur a les droits nécessaires

2. **Endpoint non trouvé**:
   - Vérifier que le module est installé
   - Redémarrer Odoo après installation

3. **Données invalides**:
   - Vérifier que les IDs de test existent dans la base
   - Adapter les données de test à votre environnement

4. **Timeout**:
   - Augmenter la valeur `TIMEOUT` dans `test_config.py`
   - Vérifier la performance d'Odoo

### Logs détaillés

Pour activer les logs détaillés:
```python
TEST_CONFIG['VERBOSE'] = True
```

## 📝 Personnalisation

### Ajouter un nouvel endpoint

1. **Modifier `test_config.py`**:
   ```python
   ENDPOINTS_TO_TEST.append({
       'name': 'Mon Endpoint',
       'endpoint': '/api/mon-endpoint',
       'method': 'POST',
       'data': {'param': 'value'}
   })
   ```

2. **Ajouter des tests spécifiques** dans `test_api_endpoints.py`

### Modifier les données de test

Adapter les valeurs dans `TEST_CONFIG` selon votre base de données:
```python
TEST_CONFIG = {
    'ACADEMIC_YEAR_ID': 42,  # ID réel de votre base
    'COURSE_ID': 15,         # ID réel de votre base
    # ...
}
```

## 🔐 Sécurité

- Ne jamais committer les mots de passe réels
- Utiliser des variables d'environnement pour les informations sensibles
- Tester uniquement sur des environnements de développement/test

## 📞 Support

Pour toute question ou problème:
1. Vérifier les logs Odoo
2. Activer le mode verbose
3. Consulter la documentation API complète
4. Tester les endpoints individuellement

---

**Note**: Ces scripts sont conçus pour tester les APIs dans un environnement de développement. Adaptez la configuration selon votre environnement spécifique. 