#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exemple d'utilisation rapide des tests API
Ce script montre comment tester un endpoint spécifique rapidement
"""

import json
import requests
from datetime import datetime


def test_fee_structure_endpoint():
    """Exemple rapide de test d'endpoint Fee Structure"""
    
    # Configuration
    BASE_URL = "http://172.16.209.129:8069"
    DATABASE = "school_management_new"
    USERNAME = "admin"
    PASSWORD = "admin"
    
    print("🚀 Test rapide de l'endpoint Fee Structure")
    print("=" * 50)
    
    # 1. Créer une session
    session = requests.Session()
    
    # 2. Authentification
    print("🔐 Authentification...")
    auth_url = f"{BASE_URL}/web/session/authenticate"
    auth_data = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "db": DATABASE,
            "login": USERNAME,
            "password": PASSWORD
        },
        "id": 1
    }
    
    try:
        response = session.post(auth_url, json=auth_data)
        result = response.json()
        
        if result.get("result") and result["result"].get("session_id"):
            print("✅ Authentification réussie!")
            session_id = result["result"]["session_id"]
        else:
            print("❌ Échec de l'authentification")
            return
    except Exception as e:
        print(f"❌ Erreur d'authentification: {e}")
        return
    
    # 3. Test de l'endpoint Fee Structure
    print("\n🔍 Test de l'endpoint /api/fee-structures...")
    
    endpoint_url = f"{BASE_URL}/api/fee-structures"
    request_data = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "limit": 5,
            "active": True
        },
        "id": 1
    }
    
    try:
        response = session.post(endpoint_url, json=request_data)
        result = response.json()
        
        if response.status_code == 200:
            api_result = result.get("result", {})
            
            if api_result.get("success"):
                print("✅ Succès!")
                data = api_result.get("data", [])
                print(f"📊 {len(data)} structure(s) trouvée(s)")
                
                # Afficher les détails
                for i, structure in enumerate(data[:3], 1):  # Limiter à 3 pour l'exemple
                    print(f"\n📋 Structure {i}:")
                    print(f"   ID: {structure.get('id')}")
                    print(f"   Nom: {structure.get('name')}")
                    print(f"   Code: {structure.get('code')}")
                    print(f"   Montant total: {structure.get('total_amount', 0)} {structure.get('currency_symbol', '')}")
                    
            else:
                print("❌ Échec de la requête API")
                print(f"Erreur: {api_result.get('error', 'Erreur inconnue')}")
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la requête: {e}")
    
    print("\n✅ Test terminé!")


def test_custom_endpoint(endpoint, data=None):
    """Test d'un endpoint personnalisé"""
    
    # Configuration
    BASE_URL = "http://localhost:8069"
    DATABASE = "school_management_new"
    USERNAME = "admin"
    PASSWORD = "admin"
    
    print(f"🚀 Test de l'endpoint: {endpoint}")
    print("=" * 50)
    
    # Session et authentification
    session = requests.Session()
    auth_url = f"{BASE_URL}/web/session/authenticate"
    auth_data = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "db": DATABASE,
            "login": USERNAME,
            "password": PASSWORD
        },
        "id": 1
    }
    
    try:
        response = session.post(auth_url, json=auth_data)
        result = response.json()
        
        if not (result.get("result") and result["result"].get("session_id")):
            print("❌ Échec de l'authentification")
            return
            
        print("✅ Authentification réussie!")
        
    except Exception as e:
        print(f"❌ Erreur d'authentification: {e}")
        return
    
    # Test de l'endpoint
    print(f"\n🔍 Test de l'endpoint {endpoint}...")
    
    endpoint_url = f"{BASE_URL}{endpoint}"
    request_data = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": data or {},
        "id": 1
    }
    
    try:
        response = session.post(endpoint_url, json=request_data)
        result = response.json()
        
        print(f"📨 Réponse (Status: {response.status_code}):")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Erreur lors de la requête: {e}")
    
    print("\n✅ Test terminé!")


if __name__ == "__main__":
    import sys
    
    print("🎯 Exemples de tests API rapides")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Test d'un endpoint spécifique
        endpoint = sys.argv[1]
        
        # Données optionnelles
        data = {}
        if len(sys.argv) > 2:
            try:
                data = json.loads(sys.argv[2])
            except json.JSONDecodeError:
                print("❌ Données JSON invalides")
                sys.exit(1)
        
        test_custom_endpoint(endpoint, data)
    else:
        # Test par défaut
        test_fee_structure_endpoint()
        
        print("\n💡 Conseils d'utilisation:")
        print("─" * 30)
        print("1. Test par défaut (Fee Structure):")
        print("   python3 quick_test_example.py")
        print()
        print("2. Test d'un endpoint spécifique:")
        print("   python3 quick_test_example.py '/api/fee-types'")
        print()
        print("3. Test avec données:")
        print("   python3 quick_test_example.py '/api/fee-structures' '{\"limit\": 10}'")
        print()
        print("4. Autres endpoints à tester:")
        print("   - /api/fee-types")
        print("   - /api/student-invoices")
        print("   - /api/student-payments")
        print("   - /api/accounting-dashboard/stats") 