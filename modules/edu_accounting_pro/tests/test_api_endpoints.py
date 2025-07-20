# -*- coding: utf-8 -*-

import json
import requests
import logging
from datetime import datetime, timedelta
from unittest import TestCase

_logger = logging.getLogger(__name__)


class TestEduAccountingProAPI:
    """Classe de test pour les APIs du module edu_accounting_pro"""
    
    def __init__(self, base_url="http://localhost:8069", database="test_db", username="admin", password="admin"):
        """
        Initialise la classe de test
        
        Args:
            base_url (str): URL de base d'Odoo
            database (str): Nom de la base de données
            username (str): Nom d'utilisateur
            password (str): Mot de passe
        """
        self.base_url = base_url
        self.database = database
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session_id = None
        self.test_results = []
        
    def authenticate(self):
        """Authentifie l'utilisateur et obtient la session"""
        try:
            # Connexion à Odoo
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
            
            response = self.session.post(auth_url, json=auth_data)
            result = response.json()
            
            if result.get("result") and result["result"].get("session_id"):
                self.session_id = result["result"]["session_id"]
                print(f"✅ Authentification réussie. Session ID: {self.session_id}")
                return True
            else:
                print("❌ Échec de l'authentification")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de l'authentification: {str(e)}")
            return False
    
    def make_api_request(self, endpoint, data=None):
        """
        Effectue une requête API
        
        Args:
            endpoint (str): Endpoint API (ex: '/api/fee-structures')
            data (dict): Données à envoyer
            
        Returns:
            dict: Réponse de l'API
        """
        try:
            url = f"{self.base_url}{endpoint}"
            
            if data is None:
                data = {}
            
            # Préparer les données pour la requête JSON-RPC
            request_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": data,
                "id": 1
            }
            
            response = self.session.post(url, json=request_data)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {})
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def log_test_result(self, test_name, success, message="", data=None):
        """Enregistre le résultat d'un test"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
    
    def test_fee_structure_endpoints(self):
        """Test des endpoints de structure de frais"""
        print("\n🔍 Test des endpoints Fee Structure...")
        
        # Test 1: Récupérer la liste des structures
        response = self.make_api_request("/api/fee-structures")
        success = response.get("success", False)
        self.log_test_result(
            "Fee Structure - Liste", 
            success, 
            f"Récupération de {len(response.get('data', []))} structures" if success else response.get('error', 'Erreur inconnue')
        )
        
        # Test 2: Créer une nouvelle structure
        test_structure_data = {
            "name": "Structure Test API",
            "code": "ST_API_001",
            "academic_year_id": 1,  # Assurez-vous que cet ID existe
            "course_id": 1,  # Assurez-vous que cet ID existe
            "billing_type": "annual",
            "active": True,
            "fee_lines": [
                {
                    "fee_type_id": 1,
                    "amount": 1000.0,
                    "is_mandatory": True,
                    "sequence": 10
                }
            ]
        }
        
        response = self.make_api_request("/api/fee-structures/create", test_structure_data)
        success = response.get("success", False)
        created_structure_id = response.get("data", {}).get("id") if success else None
        
        self.log_test_result(
            "Fee Structure - Création", 
            success, 
            f"Structure créée avec ID: {created_structure_id}" if success else response.get('error', 'Erreur inconnue')
        )
        
        # Test 3: Récupérer une structure spécifique
        if created_structure_id:
            response = self.make_api_request("/api/fee-structures/get", {"structure_id": created_structure_id})
            success = response.get("success", False)
            self.log_test_result(
                "Fee Structure - Récupération spécifique", 
                success, 
                f"Structure récupérée: {response.get('data', {}).get('name', '')}" if success else response.get('error', 'Erreur inconnue')
            )
        
        # Test 4: Mettre à jour la structure
        if created_structure_id:
            update_data = {
                "structure_id": created_structure_id,
                "name": "Structure Test API - Modifiée",
                "description": "Description mise à jour via API"
            }
            response = self.make_api_request("/api/fee-structures/update", update_data)
            success = response.get("success", False)
            self.log_test_result(
                "Fee Structure - Mise à jour", 
                success, 
                "Structure mise à jour avec succès" if success else response.get('error', 'Erreur inconnue')
            )
        
        # Test 5: Supprimer la structure (à faire en dernier)
        if created_structure_id:
            response = self.make_api_request("/api/fee-structures/delete", {"structure_id": created_structure_id})
            success = response.get("success", False)
            self.log_test_result(
                "Fee Structure - Suppression", 
                success, 
                "Structure supprimée avec succès" if success else response.get('error', 'Erreur inconnue')
            )
    
    def test_fee_type_endpoints(self):
        """Test des endpoints de type de frais"""
        print("\n🔍 Test des endpoints Fee Type...")
        
        # Test 1: Récupérer la liste des types
        response = self.make_api_request("/api/fee-types")
        success = response.get("success", False)
        self.log_test_result(
            "Fee Type - Liste", 
            success, 
            f"Récupération de {len(response.get('data', []))} types" if success else response.get('error', 'Erreur inconnue')
        )
        
        # Test 2: Créer un nouveau type
        test_type_data = {
            "name": "Type Test API",
            "code": "TT_API_001",
            "default_amount": 500.0,
            "is_mandatory": True,
            "active": True
        }
        
        response = self.make_api_request("/api/fee-types/create", test_type_data)
        success = response.get("success", False)
        created_type_id = response.get("data", {}).get("id") if success else None
        
        self.log_test_result(
            "Fee Type - Création", 
            success, 
            f"Type créé avec ID: {created_type_id}" if success else response.get('error', 'Erreur inconnue')
        )
        
        # Test 3: Récupérer un type spécifique
        if created_type_id:
            response = self.make_api_request("/api/fee-types/get", {"fee_type_id": created_type_id})
            success = response.get("success", False)
            self.log_test_result(
                "Fee Type - Récupération spécifique", 
                success, 
                f"Type récupéré: {response.get('data', {}).get('name', '')}" if success else response.get('error', 'Erreur inconnue')
            )
        
        # Test 4: Supprimer le type
        if created_type_id:
            response = self.make_api_request("/api/fee-types/delete", {"fee_type_id": created_type_id})
            success = response.get("success", False)
            self.log_test_result(
                "Fee Type - Suppression", 
                success, 
                "Type supprimé avec succès" if success else response.get('error', 'Erreur inconnue')
            )
    
    def test_student_invoice_endpoints(self):
        """Test des endpoints de facture étudiant"""
        print("\n🔍 Test des endpoints Student Invoice...")
        
        # Test 1: Récupérer la liste des factures
        response = self.make_api_request("/api/student-invoices")
        success = response.get("success", False)
        self.log_test_result(
            "Student Invoice - Liste", 
            success, 
            f"Récupération de {len(response.get('data', []))} factures" if success else response.get('error', 'Erreur inconnue')
        )
        
        # Test 2: Créer une facture
        test_invoice_data = {
            "student_id": 1,  # Assurez-vous que cet ID existe
            "fee_structure_id": 1,  # Assurez-vous que cet ID existe
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "description": "Facture test API"
        }
        
        response = self.make_api_request("/api/student-invoices/create", test_invoice_data)
        success = response.get("success", False)
        created_invoice_id = response.get("data", {}).get("id") if success else None
        
        self.log_test_result(
            "Student Invoice - Création", 
            success, 
            f"Facture créée avec ID: {created_invoice_id}" if success else response.get('error', 'Erreur inconnue')
        )
        
        # Test 3: Récupérer une facture spécifique
        if created_invoice_id:
            response = self.make_api_request("/api/student-invoices/get", {"invoice_id": created_invoice_id})
            success = response.get("success", False)
            self.log_test_result(
                "Student Invoice - Récupération spécifique", 
                success, 
                f"Facture récupérée: {response.get('data', {}).get('name', '')}" if success else response.get('error', 'Erreur inconnue')
            )
    
    def test_payment_endpoints(self):
        """Test des endpoints de paiement"""
        print("\n🔍 Test des endpoints Student Payment...")
        
        # Test 1: Récupérer la liste des paiements
        response = self.make_api_request("/api/student-payments")
        success = response.get("success", False)
        self.log_test_result(
            "Student Payment - Liste", 
            success, 
            f"Récupération de {len(response.get('data', []))} paiements" if success else response.get('error', 'Erreur inconnue')
        )
        
        # Test 2: Créer un paiement
        test_payment_data = {
            "student_id": 1,  # Assurez-vous que cet ID existe
            "amount": 1000.0,
            "payment_method_id": 1,  # Assurez-vous que cet ID existe
            "reference": "PAY_API_001",
            "payment_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "Paiement test API"
        }
        
        response = self.make_api_request("/api/student-payments/create", test_payment_data)
        success = response.get("success", False)
        created_payment_id = response.get("data", {}).get("id") if success else None
        
        self.log_test_result(
            "Student Payment - Création", 
            success, 
            f"Paiement créé avec ID: {created_payment_id}" if success else response.get('error', 'Erreur inconnue')
        )
    
    def test_dashboard_endpoints(self):
        """Test des endpoints de tableau de bord"""
        print("\n🔍 Test des endpoints Dashboard...")
        
        # Test 1: Statistiques globales
        response = self.make_api_request("/api/accounting-dashboard/stats")
        success = response.get("success", False)
        self.log_test_result(
            "Dashboard - Statistiques", 
            success, 
            "Statistiques récupérées" if success else response.get('error', 'Erreur inconnue')
        )
        
        # Test 2: Graphiques
        response = self.make_api_request("/api/accounting-dashboard/charts")
        success = response.get("success", False)
        self.log_test_result(
            "Dashboard - Graphiques", 
            success, 
            "Données graphiques récupérées" if success else response.get('error', 'Erreur inconnue')
        )
    
    def test_configuration_endpoints(self):
        """Test des endpoints de configuration"""
        print("\n🔍 Test des endpoints Configuration...")
        
        # Test 1: Récupérer la configuration
        response = self.make_api_request("/api/accounting-config")
        success = response.get("success", False)
        self.log_test_result(
            "Configuration - Liste", 
            success, 
            "Configuration récupérée" if success else response.get('error', 'Erreur inconnue')
        )
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🚀 Début des tests API pour edu_accounting_pro")
        print("=" * 50)
        
        # Authentification
        if not self.authenticate():
            print("❌ Impossible de continuer sans authentification")
            return
        
        # Exécution des tests
        self.test_fee_structure_endpoints()
        self.test_fee_type_endpoints()
        self.test_student_invoice_endpoints()
        self.test_payment_endpoints()
        self.test_dashboard_endpoints()
        self.test_configuration_endpoints()
        
        # Rapport final
        self.generate_report()
    
    def generate_report(self):
        """Génère un rapport final des tests"""
        print("\n" + "=" * 50)
        print("📊 RAPPORT FINAL DES TESTS")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"Tests réussis: {passed_tests}")
        print(f"Tests échoués: {failed_tests}")
        print(f"Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Tests échoués:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        # Sauvegarde du rapport
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Rapport détaillé sauvegardé dans: {report_file}")


# Script principal
if __name__ == "__main__":
    # Configuration du test
    # Modifiez ces valeurs selon votre environnement
    BASE_URL = "http://localhost:8069"
    DATABASE = "test_db"
    USERNAME = "admin"
    PASSWORD = "admin"
    
    # Création et exécution des tests
    tester = TestEduAccountingProAPI(BASE_URL, DATABASE, USERNAME, PASSWORD)
    tester.run_all_tests() 