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
BLUE='\033[0;34m'
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

# Fonction pour vérifier les prérequis
check_prerequisites() {
    echo -e "${BLUE}🔍 Vérification des prérequis...${NC}"
    
    # Vérifier que le dossier source existe
    if [ ! -d "$SOURCE_DIR" ]; then
        echo -e "  ❌ ${RED}Erreur: Dossier source $SOURCE_DIR n'existe pas${NC}"
        exit 1
    else
        echo -e "  ✅ Dossier source: ${GREEN}$SOURCE_DIR${NC}"
    fi
    
    # Vérifier que le dossier destination existe
    if [ ! -d "$DEST_DIR" ]; then
        echo -e "  ⚠️  ${YELLOW}Dossier destination n'existe pas, création...${NC}"
        mkdir -p "$DEST_DIR"
        if [ $? -eq 0 ]; then
            echo -e "  ✅ ${GREEN}Dossier destination créé: $DEST_DIR${NC}"
        else
            echo -e "  ❌ ${RED}Erreur lors de la création du dossier destination${NC}"
            exit 1
        fi
    else
        echo -e "  ✅ Dossier destination: ${GREEN}$DEST_DIR${NC}"
    fi
    
    # Vérifier les permissions
    if [ ! -w "$DEST_DIR" ]; then
        echo -e "  ❌ ${RED}Erreur: Pas de permissions d'écriture sur $DEST_DIR${NC}"
        exit 1
    else
        echo -e "  ✅ ${GREEN}Permissions d'écriture OK${NC}"
    fi
    
    echo ""
}

# Fonction pour lister les modules disponibles
list_available_modules() {
    echo -e "${BLUE}📦 Modules disponibles dans $SOURCE_DIR:${NC}"
    
    for module in "${MODULES[@]}"; do
        if [ -d "$SOURCE_DIR/$module" ]; then
            echo -e "  ✅ ${GREEN}$module${NC}"
        else
            echo -e "  ❌ ${RED}$module (manquant)${NC}"
        fi
    done
    echo ""
}

# Fonction pour corriger les modules mal placés
fix_misplaced_modules() {
    echo -e "${YELLOW}🔧 Vérification des modules mal placés...${NC}"
    
    for module in "${MODULES[@]}"; do
        # Vérifier si le module est dans /addons/ au lieu de /addons/custom/
        if [ -d "/opt/odoo17/addons/$module" ] && [ ! -d "$SOURCE_DIR/$module" ]; then
            echo -e "  📦 Déplacement de $module vers custom/"
            mv "/opt/odoo17/addons/$module" "$SOURCE_DIR/"
            if [ $? -eq 0 ]; then
                echo -e "  ✅ ${GREEN}$module déplacé${NC}"
            else
                echo -e "  ❌ ${RED}Erreur lors du déplacement de $module${NC}"
            fi
        fi
    done
    echo ""
}

# Fonction pour vérifier les liens symboliques
check_symlinks() {
    echo -e "${YELLOW}📋 Vérification des liens symboliques...${NC}"
    
    for module in "${MODULES[@]}"; do
        if [ -L "$DEST_DIR/$module" ]; then
            target=$(readlink "$DEST_DIR/$module")
            if [ "$target" = "../../addons/custom/$module" ]; then
                echo -e "  ✅ $module -> ${GREEN}LIEN OK${NC} ($target)"
            else
                echo -e "  ⚠️  $module -> ${YELLOW}LIEN INCORRECT${NC} ($target)"
            fi
        elif [ -d "$DEST_DIR/$module" ]; then
            echo -e "  📁 $module -> ${YELLOW}DOSSIER (pas un lien)${NC}"
        else
            echo -e "  ❌ $module -> ${RED}PAS DE LIEN${NC}"
        fi
    done
    echo ""
}

# Fonction pour recréer les liens symboliques
recreate_symlinks() {
    echo -e "${YELLOW}🔧 Recréation des liens symboliques...${NC}"
    
    # S'assurer qu'on est dans le bon dossier
    if ! cd "$DEST_DIR"; then
        echo -e "  ❌ ${RED}Erreur: Impossible d'accéder à $DEST_DIR${NC}"
        exit 1
    fi
    
    echo -e "  📍 ${BLUE}Répertoire de travail: $(pwd)${NC}"
    
    for module in "${MODULES[@]}"; do
        echo -e "  🔄 Traitement de $module..."
        
        # Supprimer l'ancien lien/dossier s'il existe
        if [ -e "$module" ]; then
            echo -e "    🗑️  Suppression de l'ancien $module"
            rm -rf "$module"
            if [ $? -ne 0 ]; then
                echo -e "    ❌ ${RED}Erreur lors de la suppression${NC}"
                continue
            fi
        fi
        
        # Vérifier que le module source existe
        if [ ! -d "$SOURCE_DIR/$module" ]; then
            echo -e "    ❌ ${RED}$module non trouvé dans $SOURCE_DIR${NC}"
            continue
        fi
        
        # Créer le nouveau lien symbolique
        echo -e "    🔗 Création du lien symbolique..."
        ln -s "../../addons/custom/$module" "$module"
        
        if [ $? -eq 0 ]; then
            # Vérifier que le lien fonctionne
            if [ -d "$module" ]; then
                echo -e "    ✅ ${GREEN}$module synchronisé et fonctionnel${NC}"
            else
                echo -e "    ⚠️  ${YELLOW}$module lien créé mais non fonctionnel${NC}"
            fi
        else
            echo -e "    ❌ ${RED}Erreur lors de la création du lien pour $module${NC}"
        fi
    done
    echo ""
}

# ... existing code ...

# Menu principal
case "${1:-menu}" in
    "check")
        check_prerequisites
        list_available_modules
        check_symlinks
        ;;
    "sync")
        check_prerequisites
        list_available_modules
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
        check_prerequisites
        list_available_modules
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
