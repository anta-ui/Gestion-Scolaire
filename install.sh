#!/bin/bash

# Script d'installation des modules de gestion scolaire personnalisés
# Auteur: Équipe de développement
# Date: $(date +"%Y-%m-%d")

echo "🚀 Installation des modules de gestion scolaire personnalisés"
echo "============================================================="

# Vérifier si Odoo est installé
if ! command -v odoo &> /dev/null; then
    echo "❌ Erreur: Odoo n'est pas installé ou pas dans le PATH"
    exit 1
fi

# Variables de configuration
ODOO_PATH=${1:-"/opt/odoo17"}
ADDONS_PATH="$ODOO_PATH/addons"

echo "📂 Chemin Odoo: $ODOO_PATH"
echo "📂 Chemin addons: $ADDONS_PATH"

# Vérifier si le dossier addons existe
if [ ! -d "$ADDONS_PATH" ]; then
    echo "❌ Erreur: Le dossier addons n'existe pas: $ADDONS_PATH"
    exit 1
fi

# Installer les dépendances Python
echo "📦 Installation des dépendances Python..."
pip install qrcode[pil] Pillow

# Copier les modules
echo "📋 Copie des modules personnalisés..."
for module in modules/edu_*; do
    if [ -d "$module" ]; then
        module_name=$(basename "$module")
        echo "  → Copie de $module_name"
        cp -r "$module" "$ADDONS_PATH/"
    fi
done

# Définir les permissions
echo "🔒 Configuration des permissions..."
chown -R odoo:odoo "$ADDONS_PATH"/edu_*
chmod -R 755 "$ADDONS_PATH"/edu_*

echo "✅ Installation terminée avec succès!"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Redémarrer le serveur Odoo"
echo "2. Activer le mode développeur"
echo "3. Aller dans Apps et mettre à jour la liste des modules"
echo "4. Installer les modules edu_* dans l'ordre des dépendances"
echo ""
echo "🎯 Modules installés:"
ls -1 "$ADDONS_PATH"/edu_* | sed 's/.*\///g' | sed 's/^/  - /' 