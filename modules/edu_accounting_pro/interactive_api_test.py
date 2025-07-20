#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script interactif pour tester les APIs du module edu_accounting_pro
Usage: python3 interactive_api_test.py
"""

import json
import requests
import sys
from datetime import datetime
from test_config import ODOO_CONFIG, TEST_CONFIG, ENDPOINTS_TO_TEST, ERROR_MESSAGES


class InteractiveAPITester:
    """Testeur interactif pour les APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session_id = None
        self.base_url = ODOO_CONFIG['BASE_URL']
        self.database = ODOO_CONFIG['DATABASE']
        self.username = ODOO_CONFIG['USERNAME']
        self.password = ODOO_CONFIG['PASSWORD']
        
    def print_banner(self):
        """Affiche la bannière d'accueil"""
        print("=" * 60)
        print("🚀 TESTEUR INTERACTIF API - edu_accounting_pro")
        print("=" * 60)
        print(f"📍 URL: {self.base_url}")
        print(f"🗄️  Base de données: {self.database}")
        print(f"👤 Utilisateur: {self.username}")
        print("=" * 60)
        print()
    
    def authenticate(self):
        """Authentifie l'utilisateur"""
        print("🔐 Authentification en cours...")
        
        try:
            auth_url = f"{self.base_url}/web/session/authenticate"
            auth_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "db": self.database,
                    "login": self.username,
                    "password": self.password
                },
                "id": 1
            }
            
            response = self.session.post(auth_url, json=auth_data, timeout=TEST_CONFIG['TIMEOUT'])
            result = response.json()
            
            if result.get("result") and result["result"].get("session_id"):
                self.session_id = result["result"]["session_id"]
                print("✅ Authentification réussie!")
                return True
            else:
                print("❌ Échec de l'authentification")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de l'authentification: {str(e)}")
            return False
    
    def make_request(self, endpoint, data=None):
        """Effectue une requête API"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if data is None:
                data = {}
            
            request_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": data,
                "id": 1
            }
            
            response = self.session.post(url, json=request_data, timeout=TEST_CONFIG['TIMEOUT'])
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {})
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def display_menu(self):
        """Affiche le menu principal"""
        print("\n📋 MENU PRINCIPAL")
        print("-" * 40)
        print("1. Tester tous les endpoints")
        print("2. Tester un endpoint spécifique")
        print("3. Tester les endpoints Fee Structure")
        print("4. Tester les endpoints Fee Type")
        print("5. Tester les endpoints Student Invoice")
        print("6. Tester les endpoints Student Payment")
        print("7. Tester les endpoints Dashboard")
        print("8. Tester un endpoint personnalisé")
        print("9. Afficher la configuration actuelle")
        print("0. Quitter")
        print("-" * 40)
    
    def test_all_endpoints(self):
        """Teste tous les endpoints définis"""
        print("\n🔍 Test de tous les endpoints...")
        print("=" * 50)
        
        results = []
        
        for i, endpoint_config in enumerate(ENDPOINTS_TO_TEST, 1):
            print(f"\n[{i}/{len(ENDPOINTS_TO_TEST)}] {endpoint_config['name']}")
            print(f"🔗 {endpoint_config['endpoint']}")
            
            response = self.make_request(endpoint_config['endpoint'], endpoint_config['data'])
            
            if response.get('success', False):
                print("✅ Succès")
                if TEST_CONFIG['VERBOSE']:
                    if 'data' in response:
                        data_count = len(response['data']) if isinstance(response['data'], list) else 1
                        print(f"   📊 Données: {data_count} élément(s)")
                    print(f"   ⏱️  Réponse: {json.dumps(response, indent=2, ensure_ascii=False)[:200]}...")
            else:
                print("❌ Échec")
                print(f"   ❗ Erreur: {response.get('error', 'Erreur inconnue')}")
            
            results.append({
                'name': endpoint_config['name'],
                'endpoint': endpoint_config['endpoint'],
                'success': response.get('success', False),
                'error': response.get('error', ''),
                'timestamp': datetime.now().isoformat()
            })
        
        # Résumé
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 50)
        
        total = len(results)
        passed = sum(1 for r in results if r['success'])
        failed = total - passed
        
        print(f"Total: {total}")
        print(f"Réussis: {passed} ✅")
        print(f"Échoués: {failed} ❌")
        print(f"Taux de réussite: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ Endpoints échoués:")
            for result in results:
                if not result['success']:
                    print(f"   - {result['name']}: {result['error']}")
    
    def test_specific_endpoint(self):
        """Teste un endpoint spécifique"""
        print("\n🎯 Test d'un endpoint spécifique")
        print("-" * 40)
        
        # Afficher les endpoints disponibles
        for i, endpoint_config in enumerate(ENDPOINTS_TO_TEST, 1):
            print(f"{i}. {endpoint_config['name']} - {endpoint_config['endpoint']}")
        
        try:
            choice = int(input("\nChoisissez un endpoint (numéro): "))
            if 1 <= choice <= len(ENDPOINTS_TO_TEST):
                endpoint_config = ENDPOINTS_TO_TEST[choice - 1]
                
                print(f"\n🔍 Test de: {endpoint_config['name']}")
                print(f"🔗 Endpoint: {endpoint_config['endpoint']}")
                print(f"📝 Données: {json.dumps(endpoint_config['data'], indent=2, ensure_ascii=False)}")
                
                response = self.make_request(endpoint_config['endpoint'], endpoint_config['data'])
                
                print("\n📨 RÉPONSE:")
                print(json.dumps(response, indent=2, ensure_ascii=False))
                
            else:
                print("❌ Choix invalide")
                
        except ValueError:
            print("❌ Veuillez entrer un nombre valide")
    
    def test_custom_endpoint(self):
        """Teste un endpoint personnalisé"""
        print("\n🛠️  Test d'un endpoint personnalisé")
        print("-" * 40)
        
        endpoint = input("Entrez l'endpoint (ex: /api/fee-structures): ")
        
        print("Entrez les données JSON (ou laissez vide pour aucune donnée):")
        data_input = input("Données: ")
        
        data = {}
        if data_input.strip():
            try:
                data = json.loads(data_input)
            except json.JSONDecodeError:
                print("❌ Données JSON invalides")
                return
        
        print(f"\n🔍 Test de: {endpoint}")
        print(f"📝 Données: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        response = self.make_request(endpoint, data)
        
        print("\n📨 RÉPONSE:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    
    def display_config(self):
        """Affiche la configuration actuelle"""
        print("\n⚙️  CONFIGURATION ACTUELLE")
        print("=" * 40)
        print(f"URL Odoo: {ODOO_CONFIG['BASE_URL']}")
        print(f"Base de données: {ODOO_CONFIG['DATABASE']}")
        print(f"Utilisateur: {ODOO_CONFIG['USERNAME']}")
        print(f"Timeout: {TEST_CONFIG['TIMEOUT']}s")
        print(f"Mode verbose: {TEST_CONFIG['VERBOSE']}")
        print(f"Nombre d'endpoints: {len(ENDPOINTS_TO_TEST)}")
        print("=" * 40)
    
    def run(self):
        """Lance le testeur interactif"""
        self.print_banner()
        
        # Authentification
        if not self.authenticate():
            print("❌ Impossible de continuer sans authentification")
            return
        
        # Boucle principale
        while True:
            self.display_menu()
            
            try:
                choice = input("\n👉 Votre choix: ")
                
                if choice == '1':
                    self.test_all_endpoints()
                elif choice == '2':
                    self.test_specific_endpoint()
                elif choice == '3':
                    print("🏗️  Tests Fee Structure - À implémenter")
                elif choice == '4':
                    print("🏷️  Tests Fee Type - À implémenter")
                elif choice == '5':
                    print("🧾 Tests Student Invoice - À implémenter")
                elif choice == '6':
                    print("💳 Tests Student Payment - À implémenter")
                elif choice == '7':
                    print("📊 Tests Dashboard - À implémenter")
                elif choice == '8':
                    self.test_custom_endpoint()
                elif choice == '9':
                    self.display_config()
                elif choice == '0':
                    print("👋 Au revoir!")
                    break
                else:
                    print("❌ Choix invalide")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Au revoir!")
                break
            except Exception as e:
                print(f"❌ Erreur: {str(e)}")
        
        print("\n✅ Tests terminés!")


if __name__ == "__main__":
    # Vérifier les dépendances
    try:
        import requests
    except ImportError:
        print("❌ Le module 'requests' n'est pas installé")
        print("💡 Installez-le avec: pip install requests")
        sys.exit(1)
    
    # Lancer le testeur
    tester = InteractiveAPITester()
    tester.run() 