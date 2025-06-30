#!/bin/bash

# Script de synchronisation automatique des modules EDU
# Auteur: Assistant IA
# Date: $(date +%Y-%m-%d)

echo "🔄 Synchronisation des modules EDU..."
echo "======================================"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Dossiers source et destination
SOURCE_DIR="/opt/odoo17/addons/custom"
DEST_DIR="/opt/odoo17/gestion_scolaire_personnalise/modules"

# Liste des modules EDU
MODULES=(
    "edu_accounting_pro"
    "edu_attendance_smart"
    "edu_communication_hub"
    "edu_evaluation_genius"
    "edu_health_center"
    "edu_library_plus"
    "edu_parent_portal"
    "edu_student_enhanced"
    "edu_timetable_ai"
    "edu_transport_manager"
)

# Fonction pour corriger les modules mal placés
fix_misplaced_modules() {
    echo -e "${YELLOW}🔧 Vérification des modules mal placés...${NC}"
    
    for module in "${MODULES[@]}"; do
        # Vérifier si le module est dans /addons/ au lieu de /addons/custom/
        if [ -d "/opt/odoo17/addons/$module" ] && [ ! -d "$SOURCE_DIR/$module" ]; then
            echo -e "  📦 Déplacement de $module vers custom/"
            mv "/opt/odoo17/addons/$module" "$SOURCE_DIR/"
            echo -e "  ✅ ${GREEN}$module déplacé${NC}"
        fi
    done
}

# Fonction pour vérifier les liens symboliques
check_symlinks() {
    echo -e "${YELLOW}📋 Vérification des liens symboliques...${NC}"
    
    for module in "${MODULES[@]}"; do
        if [ -L "$DEST_DIR/$module" ]; then
            target=$(readlink "$DEST_DIR/$module")
            if [ "$target" = "../../addons/custom/$module" ]; then
                echo -e "  ✅ $module -> ${GREEN}LIEN OK${NC}"
            else
                echo -e "  ⚠️  $module -> ${YELLOW}LIEN INCORRECT${NC}"
            fi
        else
            echo -e "  ❌ $module -> ${RED}PAS DE LIEN${NC}"
        fi
    done
}

# Fonction pour recréer les liens symboliques
recreate_symlinks() {
    echo -e "${YELLOW}🔧 Recréation des liens symboliques...${NC}"
    
    cd "$DEST_DIR" || exit 1
    
    for module in "${MODULES[@]}"; do
        # Supprimer l'ancien lien/dossier s'il existe
        if [ -e "$module" ]; then
            rm -rf "$module"
        fi
        
        # Créer le nouveau lien symbolique
        if [ -d "$SOURCE_DIR/$module" ]; then
            ln -s "../../addons/custom/$module" "$module"
            echo -e "  ✅ ${GREEN}$module synchronisé${NC}"
        else
            echo -e "  ❌ ${RED}$module non trouvé dans $SOURCE_DIR${NC}"
        fi
    done
}

# Fonction pour redémarrer Odoo
restart_odoo() {
    echo -e "${YELLOW}🔄 Redémarrage d'Odoo...${NC}"
    
    # Arrêter Odoo
    pkill -f odoo
    sleep 2
    
    # Redémarrer Odoo
    cd /opt/odoo17
    python3 odoo-bin -c /etc/odoo/odoo.conf &
    
    echo -e "${GREEN}✅ Odoo redémarré${NC}"
}

# Fonction pour mettre à jour les modules en base
update_modules() {
    echo -e "${YELLOW}📊 Mise à jour des modules en base...${NC}"
    
    # Arrêter Odoo
    pkill -f odoo
    sleep 2
    
    # Mettre à jour tous les modules EDU
    cd /opt/odoo17
    module_list=$(IFS=,; echo "${MODULES[*]}")
    python3 odoo-bin -c /etc/odoo/odoo.conf -d school_management -u "$module_list" --stop-after-init
    
    echo -e "${GREEN}✅ Modules mis à jour${NC}"
}

# Menu principal
case "${1:-menu}" in
    "check")
        check_symlinks
        ;;
    "sync")
        fix_misplaced_modules
        recreate_symlinks
        ;;
    "restart")
        restart_odoo
        ;;
    "update")
        update_modules
        ;;
    "full")
        fix_misplaced_modules
        echo ""
        check_symlinks
        echo ""
        recreate_symlinks
        echo ""
        update_modules
        echo ""
        restart_odoo
        ;;
    "menu"|*)
        echo "🎯 Script de synchronisation des modules EDU"
        echo ""
        echo "Usage: $0 [commande]"
        echo ""
        echo "Commandes disponibles:"
        echo "  check    - Vérifier les liens symboliques"
        echo "  sync     - Synchroniser les modules (déplacer + recréer les liens)"
        echo "  restart  - Redémarrer Odoo"
        echo "  update   - Mettre à jour les modules en base"
        echo "  full     - Tout faire (sync + update + restart)"
        echo ""
        echo "Exemple: $0 full"
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Terminé !${NC}" 