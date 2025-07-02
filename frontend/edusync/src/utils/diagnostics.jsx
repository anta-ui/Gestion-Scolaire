// diagnostics.js - Utilitaire de diagnostic pour les problèmes réseau

export const diagnostics = {
    // Tester la connectivité de base vers l'API
    async testApiConnectivity() {
      const results = {
        timestamp: new Date().toISOString(),
        tests: {}
      };
  
      const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8069';
      
      try {
        // Test 1: Ping basique
        console.log('🔍 Test 1: Ping basique vers', apiUrl);
        const pingStart = performance.now();
        const pingResponse = await fetch(`${apiUrl}/api/test`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        });
        const pingTime = performance.now() - pingStart;
        
        results.tests.ping = {
          success: pingResponse.ok,
          status: pingResponse.status,
          responseTime: Math.round(pingTime),
          url: `${apiUrl}/api/test`
        };
        
        if (pingResponse.ok) {
          const pingData = await pingResponse.json();
          results.tests.ping.data = pingData;
          console.log('✅ Ping réussi:', pingData);
        } else {
          console.log('❌ Échec du ping:', pingResponse.status, pingResponse.statusText);
        }
      } catch (error) {
        console.log('❌ Erreur ping:', error.message);
        results.tests.ping = {
          success: false,
          error: error.message,
          url: `${apiUrl}/api/test`
        };
      }
  
      try {
        // Test 2: Test des étudiants sans authentification
        console.log('🔍 Test 2: Test endpoint étudiants');
        const studentsStart = performance.now();
        const studentsResponse = await fetch(`${apiUrl}/api/dashboard/students`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        });
        const studentsTime = performance.now() - studentsStart;
        
        results.tests.students = {
          success: studentsResponse.ok || studentsResponse.status === 401, // 401 est normal sans auth
          status: studentsResponse.status,
          responseTime: Math.round(studentsTime),
          url: `${apiUrl}/api/dashboard/students`
        };
        
        if (studentsResponse.ok) {
          const studentsData = await studentsResponse.json();
          results.tests.students.data = studentsData;
          console.log('✅ Endpoint étudiants accessible:', studentsData);
        } else if (studentsResponse.status === 401) {
          console.log('⚠️ Endpoint étudiants protégé (normal):', studentsResponse.status);
        } else {
          console.log('❌ Erreur endpoint étudiants:', studentsResponse.status, studentsResponse.statusText);
        }
      } catch (error) {
        console.log('❌ Erreur endpoint étudiants:', error.message);
        results.tests.students = {
          success: false,
          error: error.message,
          url: `${apiUrl}/api/dashboard/students`
        };
      }
  
      try {
        // Test 3: Vérification CORS
        console.log('🔍 Test 3: Vérification CORS');
        const corsResponse = await fetch(`${apiUrl}/api/test`, {
          method: 'OPTIONS',
          headers: {
            'Origin': window.location.origin,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type',
          }
        });
        
        results.tests.cors = {
          success: corsResponse.ok,
          status: corsResponse.status,
          headers: {
            'access-control-allow-origin': corsResponse.headers.get('access-control-allow-origin'),
            'access-control-allow-methods': corsResponse.headers.get('access-control-allow-methods'),
            'access-control-allow-headers': corsResponse.headers.get('access-control-allow-headers'),
          }
        };
        
        console.log('CORS Headers:', results.tests.cors.headers);
      } catch (error) {
        console.log('❌ Erreur CORS:', error.message);
        results.tests.cors = {
          success: false,
          error: error.message
        };
      }
  
      // Test 4: Informations réseau
      results.tests.network = {
        origin: window.location.origin,
        userAgent: navigator.userAgent,
        onLine: navigator.onLine,
        connection: navigator.connection ? {
          effectiveType: navigator.connection.effectiveType,
          downlink: navigator.connection.downlink,
          rtt: navigator.connection.rtt
        } : 'Non disponible'
      };
  
      console.log('📊 Résultats complets du diagnostic:', results);
      return results;
    },
  
    // Affichage formaté des résultats
    formatResults(results) {
      let output = `🔍 Diagnostic API - ${results.timestamp}\n\n`;
      
      // Résumé
      const totalTests = Object.keys(results.tests).length - 1; // -1 pour exclure 'network'
      const successfulTests = Object.values(results.tests).filter(test => test.success && test.success !== undefined).length;
      output += `📈 Résumé: ${successfulTests}/${totalTests} tests réussis\n\n`;
      
      // Détails des tests
      for (const [testName, testResult] of Object.entries(results.tests)) {
        if (testName === 'network') continue;
        
        const icon = testResult.success ? '✅' : '❌';
        output += `${icon} ${testName.toUpperCase()}\n`;
        output += `   Status: ${testResult.status || 'N/A'}\n`;
        output += `   URL: ${testResult.url || 'N/A'}\n`;
        
        if (testResult.responseTime) {
          output += `   Temps: ${testResult.responseTime}ms\n`;
        }
        
        if (testResult.error) {
          output += `   Erreur: ${testResult.error}\n`;
        }
        
        output += '\n';
      }
      
      // Informations réseau
      output += `🌐 RÉSEAU\n`;
      output += `   Origin: ${results.tests.network.origin}\n`;
      output += `   En ligne: ${results.tests.network.onLine}\n`;
      output += `   Connexion: ${results.tests.network.connection?.effectiveType || 'N/A'}\n\n`;
      
      return output;
    },
  
    // Exécuter le diagnostic complet avec affichage
    async runDiagnostic() {
      console.log('🚀 Démarrage du diagnostic réseau...');
      
      try {
        const results = await this.testApiConnectivity();
        const formattedResults = this.formatResults(results);
        
        console.log(formattedResults);
        
        // Retourner les résultats pour utilisation
        return {
          success: results.tests.ping?.success || false,
          results: results,
          formatted: formattedResults
        };
      } catch (error) {
        console.error('💥 Erreur durant le diagnostic:', error);
        return {
          success: false,
          error: error.message
        };
      }
    }
  };
  
  export default diagnostics; 