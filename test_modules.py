#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier que tous les modèles EDU sont bien chargés
"""

import sys
import os

# Ajouter le chemin d'Odoo
sys.path.insert(0, '/opt/odoo17')
sys.path.insert(0, '/opt/odoo17/addons')

try:
    import odoo
    from odoo import api, SUPERUSER_ID
    from odoo.tools import config
    
    # Configuration basique
    config.parse_config(['-c', '/etc/odoo/odoo.conf'])
    
    # Initialiser Odoo
    odoo.service.db.initialize()
    
    # Se connecter à la base
    with api.Environment.manage():
        env = api.Environment(odoo.registry('school_management'), SUPERUSER_ID, {})
        
        # Liste des modèles EDU à tester
        edu_models = [
            'edu.message',
            'edu.message.template',
            'edu.evaluation.type',
            'edu.grade.scale',
            'edu.library.book',
            'edu.health.record',
            'edu.parent.portal',
            'edu.transport.vehicle',
            'edu.accounting.fee',
            'edu.attendance.record',
            'edu.timetable.schedule'
        ]
        
        print("🧪 Test des modèles EDU")
        print("=" * 40)
        
        success_count = 0
        total_count = len(edu_models)
        
        for model_name in edu_models:
            try:
                # Tenter d'accéder au modèle
                model = env[model_name]
                # Tenter un search basique
                count = model.search_count([])
                print(f"✅ {model_name:<25} -> {count} enregistrements")
                success_count += 1
            except KeyError:
                print(f"❌ {model_name:<25} -> MODÈLE NON TROUVÉ")
            except Exception as e:
                print(f"⚠️  {model_name:<25} -> ERREUR: {str(e)[:50]}...")
        
        print("\n" + "=" * 40)
        print(f"📊 Résultat: {success_count}/{total_count} modèles fonctionnels")
        
        if success_count == total_count:
            print("🎉 Tous les modèles EDU sont opérationnels !")
            exit(0)
        else:
            print("⚠️  Certains modèles ont des problèmes")
            exit(1)
            
except Exception as e:
    print(f"❌ Erreur lors du test: {e}")
    import traceback
    traceback.print_exc()
    exit(1) 