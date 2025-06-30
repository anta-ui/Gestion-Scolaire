/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class QRScanner extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            isScanning: false,
            lastResult: null,
            error: null
        });

        this.video = null;
        this.canvas = null;
        this.context = null;
        this.scanInterval = null;

        onMounted(() => {
            this.initializeScanner();
        });

        onWillUnmount(() => {
            this.stopScanner();
        });
    }

    async initializeScanner() {
        try {
            this.video = document.getElementById('qr-video');
            this.canvas = document.getElementById('qr-canvas');
            
            if (this.canvas) {
                this.context = this.canvas.getContext('2d');
            }
        } catch (error) {
            console.error("Erreur d'initialisation du scanner:", error);
            this.state.error = "Impossible d'initialiser le scanner";
        }
    }

    async toggleScanner() {
        if (this.state.isScanning) {
            this.stopScanner();
        } else {
            await this.startScanner();
        }
    }

    async startScanner() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "environment" }
            });
            
            if (this.video) {
                this.video.srcObject = stream;
                this.state.isScanning = true;
                this.state.error = null;
                
                // Démarrer la détection QR
                this.scanInterval = setInterval(() => {
                    this.scanForQR();
                }, 500);
            }
        } catch (error) {
            console.error("Erreur d'accès à la caméra:", error);
            this.state.error = "Impossible d'accéder à la caméra";
            this.notification.add("Erreur d'accès à la caméra", {
                type: "danger"
            });
        }
    }

    stopScanner() {
        if (this.video && this.video.srcObject) {
            const tracks = this.video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            this.video.srcObject = null;
        }
        
        if (this.scanInterval) {
            clearInterval(this.scanInterval);
            this.scanInterval = null;
        }
        
        this.state.isScanning = false;
    }

    scanForQR() {
        if (!this.video || !this.canvas || !this.context) return;
        
        try {
            // Copier la vidéo sur le canvas
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            this.context.drawImage(this.video, 0, 0);
            
            // Obtenir les données d'image
            const imageData = this.context.getImageData(0, 0, this.canvas.width, this.canvas.height);
            
            // Ici, vous devriez utiliser une bibliothèque de détection QR
            // comme jsQR ou qr-scanner
            // Pour l'instant, simulation d'une détection
            this.simulateQRDetection();
            
        } catch (error) {
            console.error("Erreur lors du scan QR:", error);
        }
    }

    simulateQRDetection() {
        // Simulation pour les tests - à remplacer par une vraie détection QR
        const testQR = Math.random() > 0.95; // 5% de chance de "détecter" un QR
        
        if (testQR) {
            const qrData = "QR_TEST_" + Date.now();
            this.onQRDetected(qrData);
        }
    }

    async onQRDetected(qrData) {
        this.state.lastResult = qrData;
        
        try {
            // Traiter le QR code détecté
            const result = await this.orm.call(
                "edu.qr.code",
                "process_qr_scan",
                [qrData]
            );
            
            if (result.success) {
                this.notification.add(result.message || "QR code traité avec succès", {
                    type: "success"
                });
            } else {
                this.notification.add(result.message || "Erreur lors du traitement du QR code", {
                    type: "warning"
                });
            }
        } catch (error) {
            console.error("Erreur lors du traitement du QR:", error);
            this.notification.add("Erreur lors du traitement du QR code", {
                type: "danger"
            });
        }
    }
}

QRScanner.template = "edu_attendance_smart.QRScanner";

registry.category("actions").add("edu_attendance_smart.qr_scanner", QRScanner);
