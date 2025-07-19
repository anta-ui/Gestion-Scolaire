# 🔄 Synchronisation Automatique des Modules EDU

## 📋 Vue d'ensemble

Vos 10 modules EDU sont maintenant **synchronisés automatiquement** entre :
- **Source** : `/opt/odoo17/addons/custom/` (modules actifs dans Odoo)
- **Personnalisation** : `/opt/odoo17/gestion_scolaire_personnalise/modules/` (votre dossier de travail)

## 🔗 Liens Symboliques

Tous les modules dans `gestion_scolaire_personnalise/modules/` sont des **liens symboliques** vers les modules actifs. Cela signifie :

✅ **Modifications en temps réel** : Toute modification dans un dossier se reflète instantanément dans l'autre  
✅ **Synchronisation automatique** : Plus besoin de copier/coller manuellement  
✅ **Source unique de vérité** : Les modules dans `/addons/custom/` restent la référence  

## 🛠️ Script de Synchronisation

Le script `sync_modules.sh` vous permet de gérer facilement la synchronisation :

### Commandes disponibles :

```bash
# Vérifier l'état des liens symboliques
./sync_modules.sh check

# Recréer tous les liens symboliques
./sync_modules.sh sync

# Redémarrer Odoo
./sync_modules.sh restart

# Tout faire d'un coup (recommandé)
./sync_modules.sh full
```

## 📦 Modules Synchronisés

1. **edu_accounting_pro** - Comptabilité Éducative
2. **edu_attendance_smart** - Présences Smart  
3. **edu_communication_hub** - Communication Hub
4. **edu_evaluation_genius** - Évaluation Genius
5. **edu_health_center** - Centre de Santé
6. **edu_library_plus** - Bibliothèque Plus
7. **edu_parent_portal** - Portail Parents
8. **edu_student_enhanced** - Students Enhanced
9. **edu_timetable_ai** - Emploi du Temps IA
10. **edu_transport_manager** - Transport Scolaire

## 🔧 Workflow de Développement

### Pour modifier un module :

1. **Modifiez directement** dans `gestion_scolaire_personnalise/modules/[nom_module]/`
2. **Les changements sont automatiquement appliqués** dans `/addons/custom/`
3. **Redémarrez Odoo** si nécessaire : `./sync_modules.sh restart`

### En cas de problème :

1. **Vérifiez les liens** : `./sync_modules.sh check`
2. **Resynchronisez** : `./sync_modules.sh sync`
3. **Redémarrez tout** : `./sync_modules.sh full`

## 📁 Sauvegarde

Vos anciens modules ont été sauvegardés dans :
```
/opt/odoo17/gestion_scolaire_personnalise/backup_modules_[DATE]/
```

## ⚠️ Important

- **NE SUPPRIMEZ PAS** les dossiers dans `/addons/custom/` - ce sont les modules actifs
- **Les liens symboliques** doivent pointer vers `../../addons/custom/[module]`
- **En cas de mise à jour Odoo**, relancez `./sync_modules.sh sync`

## 🎯 Avantages

✅ **Modifications en temps réel**  
✅ **Pas de duplication de fichiers**  
✅ **Gestion centralisée**  
✅ **Sauvegarde automatique**  
✅ **Script de maintenance fourni**  

---
*Synchronisation mise en place le $(date +%Y-%m-%d) par Assistant IA* 



python3 /opt/odoo17/odoo-bin -c /etc/odoo/odoo.conf -d school_management_new --http-port=8069 --log-level=info