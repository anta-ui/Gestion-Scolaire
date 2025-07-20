#!/bin/bash

# Script pour tester les APIs du module edu_accounting_pro

echo "🚀 Lancement des tests API pour edu_accounting_pro"
echo "=============================================="

# Configuration par défaut
DEFAULT_URL="http://172.16.209.129:8069"
DEFAULT_DB="school_management_new"
DEFAULT_EMAIL="odoo"
DEFAULT_PASSWORD="odoo"

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Vérifier si le module requests est installé
if ! python3 -c "import requests" &> /dev/null; then
    echo "📦 Installation du module requests..."
    pip3 install requests
fi

# Demander les paramètres de connexion
echo "📝 Configuration de la connexion:"
read -p "URL d'Odoo (défaut: $DEFAULT_URL): " ODOO_URL
read -p "Base de données (défaut: $DEFAULT_DB): " DATABASE
read -p "Nom d'utilisateur (défaut: $DEFAULT_USER): " USERNAME
read -s -p "Mot de passe (défaut: $DEFAULT_PASS): " PASSWORD
echo

# Utiliser les valeurs par défaut si aucune entrée
ODOO_URL=${ODOO_URL:-$DEFAULT_URL}
DATABASE=${DATABASE:-$DEFAULT_DB}
USERNAME=${USERNAME:-$DEFAULT_USER}
PASSWORD=${PASSWORD:-$DEFAULT_PASS}

# Créer le fichier de configuration temporaire
CONFIG_FILE="/tmp/api_test_config.py"
cat > "$CONFIG_FILE" << EOF
# Configuration pour les tests API
BASE_URL = "$ODOO_URL"
DATABASE = "$DATABASE"
USERNAME = "$USERNAME"
PASSWORD = "$PASSWORD"
EOF

# Exécuter les tests
echo "🔍 Exécution des tests..."
cd "$(dirname "$0")" || exit 1

# Modifier le script de test pour utiliser la configuration
python3 -c "
import sys
sys.path.insert(0, '/tmp')
from api_test_config import BASE_URL, DATABASE, USERNAME, PASSWORD
exec(open('tests/test_api_endpoints.py').read())
tester = TestEduAccountingProAPI(BASE_URL, DATABASE, USERNAME, PASSWORD)
tester.run_all_tests()
"

# Nettoyer le fichier de configuration
rm -f "$CONFIG_FILE"

echo
echo "✅ Tests terminés!"
echo "📄 Consultez le rapport généré pour les détails" 