/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class BiometricScanner extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            isScanning: false,
            scanProgress: 0,
            lastResult: null,
            error: null,
            deviceConnected: false
        });
    }

    async checkDeviceConnection() {
        try {
            // Simuler la vérification de connexion d'un appareil biométrique
            // Dans un vrai scénario, ceci communiquerait avec un SDK biométrique
            this.state.deviceConnected = Math.random() > 0.3; // 70% de chance d'être connecté
            
            if (!this.state.deviceConnected) {
                this.notification.add("Aucun appareil biométrique détecté", {
                    type: "warning"
                });
            }
        } catch (error) {
            console.error("Erreur lors de la vérification de l'appareil:", error);
            this.state.error = "Erreur de connexion à l'appareil biométrique";
        }
    }

    async startBiometricScan() {
        if (!this.state.deviceConnected) {
            await this.checkDeviceConnection();
            if (!this.state.deviceConnected) return;
        }

        this.state.isScanning = true;
        this.state.scanProgress = 0;
        this.state.error = null;

        try {
            // Simuler le processus de scan biométrique
            await this.simulateBiometricScan();
        } catch (error) {
            console.error("Erreur lors du scan biométrique:", error);
            this.state.error = "Erreur lors du scan biométrique";
            this.notification.add("Erreur lors du scan biométrique", {
                type: "danger"
            });
        } finally {
            this.state.isScanning = false;
            this.state.scanProgress = 0;
        }
    }

    async simulateBiometricScan() {
        return new Promise((resolve, reject) => {
            const scanInterval = setInterval(() => {
                this.state.scanProgress += 10;
                
                if (this.state.scanProgress >= 100) {
                    clearInterval(scanInterval);
                    
                    // Simuler le résultat du scan
                    const scanSuccess = Math.random() > 0.2; // 80% de succès
                    
                    if (scanSuccess) {
                        this.onBiometricDetected("BIOMETRIC_" + Date.now());
                        resolve();
                    } else {
                        this.state.error = "Empreinte non reconnue";
                        reject(new Error("Scan failed"));
                    }
                }
            }, 200);
        });
    }

    async onBiometricDetected(biometricData) {
        this.state.lastResult = biometricData;
        
        try {
            // Traiter les données biométriques
            const result = await this.orm.call(
                "edu.biometric.data",
                "process_biometric_scan",
                [biometricData]
            );
            
            if (result.success) {
                this.notification.add(
                    result.message || "Scan biométrique réussi", 
                    { type: "success" }
                );
                
                // Si un utilisateur est identifié, traiter la présence
                if (result.user_id) {
                    await this.processAttendance(result.user_id);
                }
            } else {
                this.notification.add(
                    result.message || "Empreinte non reconnue", 
                    { type: "warning" }
                );
            }
        } catch (error) {
            console.error("Erreur lors du traitement biométrique:", error);
            this.notification.add("Erreur lors du traitement des données biométriques", {
                type: "danger"
            });
        }
    }

    async processAttendance(userId) {
        try {
            const result = await this.orm.call(
                "edu.attendance.record",
                "create_from_biometric",
                [userId]
            );
            
            if (result.success) {
                this.notification.add("Présence enregistrée avec succès", {
                    type: "success"
                });
            }
        } catch (error) {
            console.error("Erreur lors de l'enregistrement de présence:", error);
        }
    }

    async enrollBiometric() {
        // Fonction pour enregistrer de nouvelles données biométriques
        this.notification.add("Fonctionnalité d'inscription biométrique à implémenter", {
            type: "info"
        });
    }
}

BiometricScanner.template = "edu_attendance_smart.BiometricScanner";

registry.category("actions").add("edu_attendance_smart.biometric_scanner", BiometricScanner);
