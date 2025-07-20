// JavaScript pour l'interface mobile du scanner de présences

class MobileAttendanceScanner {
    constructor() {
        this.isScanning = false;
        this.video = null;
        this.canvas = null;
        this.context = null;
        this.scanInterval = null;
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupEventListeners();
            this.initializeElements();
        });
    }

    setupEventListeners() {
        // Bouton de démarrage du scan
        const startBtn = document.getElementById('start-scan');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startScanning());
        }

        // Bouton d'arrêt du scan
        const stopBtn = document.getElementById('stop-scan');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopScanning());
        }

        // Formulaire de pointage rapide
        const quickForm = document.getElementById('quick-checkin-form');
        if (quickForm) {
            quickForm.addEventListener('submit', (e) => this.handleQuickCheckin(e));
        }

        // Bouton de rafraîchissement de la liste
        const refreshBtn = document.querySelector('[onclick="refreshAttendanceList()"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshAttendanceList());
        }
    }

    initializeElements() {
        this.video = document.getElementById('qr-video');
        
        // Créer le canvas s'il n'existe pas
        if (!document.getElementById('qr-canvas')) {
            this.canvas = document.createElement('canvas');
            this.canvas.id = 'qr-canvas';
            this.canvas.style.display = 'none';
            document.body.appendChild(this.canvas);
        } else {
            this.canvas = document.getElementById('qr-canvas');
        }

        if (this.canvas) {
            this.context = this.canvas.getContext('2d');
        }
    }

    async startScanning() {
        if (this.isScanning) return;

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    facingMode: "environment",
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });

            if (this.video) {
                this.video.srcObject = stream;
                this.isScanning = true;
                this.updateScanButtons();
                
                // Commencer la détection QR
                this.scanInterval = setInterval(() => {
                    this.scanForQR();
                }, 500);
            }
        } catch (error) {
            console.error('Erreur d\'accès à la caméra:', error);
            this.showNotification('Impossible d\'accéder à la caméra', 'error');
        }
    }

    stopScanning() {
        if (!this.isScanning) return;

        if (this.video && this.video.srcObject) {
            const tracks = this.video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            this.video.srcObject = null;
        }

        if (this.scanInterval) {
            clearInterval(this.scanInterval);
            this.scanInterval = null;
        }

        this.isScanning = false;
        this.updateScanButtons();
    }

    updateScanButtons() {
        const startBtn = document.getElementById('start-scan');
        const stopBtn = document.getElementById('stop-scan');

        if (startBtn && stopBtn) {
            if (this.isScanning) {
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
            } else {
                startBtn.style.display = 'inline-block';
                stopBtn.style.display = 'none';
            }
        }
    }

    scanForQR() {
        if (!this.video || !this.canvas || !this.context) return;
        if (this.video.readyState !== this.video.HAVE_ENOUGH_DATA) return;

        try {
            // Copier la vidéo sur le canvas
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            this.context.drawImage(this.video, 0, 0);

            // Simulation de détection QR (à remplacer par une vraie bibliothèque)
            this.simulateQRDetection();
        } catch (error) {
            console.error('Erreur lors du scan QR:', error);
        }
    }

    simulateQRDetection() {
        // Simulation pour les tests
        const testQR = Math.random() > 0.98; // 2% de chance de "détecter" un QR
        
        if (testQR) {
            const qrData = "STUDENT_" + Math.floor(Math.random() * 1000);
            this.onQRDetected(qrData);
        }
    }

    onQRDetected(qrData) {
        const resultDiv = document.getElementById('scan-result');
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <strong>QR Code détecté :</strong> ${qrData}
                    <br><small>Traitement en cours...</small>
                </div>
            `;
        }

        // Traiter le QR code
        this.processQRCode(qrData);
    }

    async processQRCode(qrData) {
        try {
            // Simulation d'un appel API
            const response = await fetch('/edu_attendance/process_qr', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ qr_data: qrData })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification(result.message || 'Présence enregistrée', 'success');
                this.refreshAttendanceList();
            } else {
                this.showNotification(result.message || 'Erreur lors du traitement', 'error');
            }
        } catch (error) {
            console.error('Erreur lors du traitement du QR:', error);
            this.showNotification('Erreur de connexion', 'error');
        }
    }

    async handleQuickCheckin(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const data = {
            student_id: formData.get('student_id'),
            session_id: formData.get('session_id'),
            action: formData.get('action')
        };

        try {
            const response = await fetch('/edu_attendance/quick_checkin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Présence enregistrée avec succès', 'success');
                event.target.reset();
                this.refreshAttendanceList();
            } else {
                this.showNotification(result.message || 'Erreur lors de l\'enregistrement', 'error');
            }
        } catch (error) {
            console.error('Erreur lors du pointage rapide:', error);
            this.showNotification('Erreur de connexion', 'error');
        }
    }

    async refreshAttendanceList() {
        const listContainer = document.getElementById('attendance-list');
        if (!listContainer) return;

        // Afficher un indicateur de chargement
        listContainer.innerHTML = '<div class="text-center"><div class="loading-spinner"></div> Chargement...</div>';

        try {
            const response = await fetch('/edu_attendance/get_today_attendance');
            const data = await response.json();
            
            if (data.success) {
                this.renderAttendanceList(data.records);
            } else {
                listContainer.innerHTML = '<div class="alert alert-warning">Aucune donnée disponible</div>';
            }
        } catch (error) {
            console.error('Erreur lors du chargement de la liste:', error);
            listContainer.innerHTML = '<div class="alert alert-danger">Erreur de chargement</div>';
        }
    }

    renderAttendanceList(records) {
        const listContainer = document.getElementById('attendance-list');
        if (!listContainer) return;

        if (records.length === 0) {
            listContainer.innerHTML = '<div class="alert alert-info">Aucune présence enregistrée aujourd\'hui</div>';
            return;
        }

        const html = records.map(record => `
            <div class="attendance-list-item ${record.status}">
                <div class="student-info">
                    <div class="student-name">${record.student_name}</div>
                    <div class="session-info">${record.session_name}</div>
                </div>
                <div class="status-info">
                    <div class="status-badge ${record.status}">${record.status_display}</div>
                    <div class="time-info">${record.time}</div>
                </div>
            </div>
        `).join('');

        listContainer.innerHTML = html;
    }

    showNotification(message, type = 'info') {
        // Créer une notification toast
        const toast = document.createElement('div');
        toast.className = `toast-mobile alert alert-${type === 'error' ? 'danger' : type}`;
        toast.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span>${message}</span>
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

        document.body.appendChild(toast);

        // Supprimer automatiquement après 5 secondes
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
}

// Initialiser le scanner mobile
const mobileScanner = new MobileAttendanceScanner();

// Fonction globale pour le rafraîchissement (pour compatibilité)
function refreshAttendanceList() {
    mobileScanner.refreshAttendanceList();
}
