// Medical AI Assistant - Complete Application

const MedicalApp = {
    selectedSymptoms: new Set(),
    selectedMedications: [],
    
    // Initialize app
    init() {
        console.log('Medical App Initializing...');
        this.loadSymptoms();
        this.loadStats();
        this.loadMedicalFact();
        this.loadDiseases();
        this.loadAppointments();
        this.loadConsultationHistory();
        this.setupEventListeners();
    },
    
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('[data-tab]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = link.getAttribute('data-tab');
                this.switchTab(tabName);
            });
        });
        
        // Disease search
        const searchInput = document.getElementById('disease-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.loadDiseases(e.target.value);
            });
        }
        
        // Image preview
        const imageInput = document.getElementById('image-input');
        if (imageInput) {
            imageInput.addEventListener('change', (e) => {
                this.previewImage(e.target.files[0]);
            });
        }
    },
    
    switchTab(tabName) {
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.style.display = 'none';
        });
        
        const selectedTab = document.getElementById(`${tabName}-tab`);
        if (selectedTab) {
            selectedTab.style.display = 'block';
        }
        
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        const activeLink = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
        
        if (tabName === 'appointments') this.loadAppointments();
        if (tabName === 'history') this.loadConsultationHistory();
        if (tabName === 'diseases') this.loadDiseases();
    },
    
    showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.style.display = 'flex';
    },
    
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.style.display = 'none';
    },
    
    previewImage(file) {
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const preview = document.getElementById('image-preview');
                if (preview) {
                    preview.innerHTML = `<img src="${e.target.result}" style="max-width:100%; margin-top:10px; border-radius:8px;">`;
                }
            };
            reader.readAsDataURL(file);
        }
    },
    
    async loadSymptoms() {
        try {
            const response = await fetch('/api/symptoms');
            const data = await response.json();
            const container = document.getElementById('symptoms-container');
            if (container) {
                container.innerHTML = data.symptoms.map(s => 
                    `<span class="symptom-badge" onclick="window.medicalApp.toggleSymptom('${s}')">${s}</span>`
                ).join('');
            }
        } catch (error) {
            console.error('Error loading symptoms:', error);
        }
    },
    
    toggleSymptom(symptom) {
        const badges = document.querySelectorAll('.symptom-badge');
        for (let badge of badges) {
            if (badge.textContent === symptom) {
                if (this.selectedSymptoms.has(symptom)) {
                    this.selectedSymptoms.delete(symptom);
                    badge.classList.remove('selected');
                } else {
                    this.selectedSymptoms.add(symptom);
                    badge.classList.add('selected');
                }
                break;
            }
        }
    },
    
    async performDiagnosis() {
        if (this.selectedSymptoms.size === 0) {
            alert('Please select at least one symptom');
            return;
        }
        
        this.showLoading();
        
        const requestData = {
            symptoms: Array.from(this.selectedSymptoms),
            age_group: document.getElementById('age-group').value,
            duration: document.getElementById('duration').value,
            severity: document.getElementById('severity').value
        };
        
        try {
            const response = await fetch('/api/diagnose', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            this.displayDiagnosis(result);
            await this.loadStats();
            await this.loadConsultationHistory();
        } catch (error) {
            console.error('Error:', error);
            alert('Error performing diagnosis');
        } finally {
            this.hideLoading();
        }
    },
    
    displayDiagnosis(result) {
        const primary = result.primary_diagnosis;
        const html = `
            <div class="diagnosis-card">
                <h3>🎯 Primary Diagnosis: ${primary.disease}</h3>
                <p><strong>Match Confidence:</strong> ${primary.match_percentage}%</p>
                <p><strong>Matched Symptoms:</strong> ${primary.matched_symptoms.join(', ')}</p>
                <p><strong>Severity:</strong> ${primary.severity}</p>
                <p><strong>Expected Duration:</strong> ${primary.duration}</p>
                <p><strong>Recommendation:</strong> ${primary.recommendation}</p>
                <p><strong>⚠️ When to see doctor:</strong> ${primary.when_to_see_doctor}</p>
                <p><strong>🛡️ Prevention:</strong> ${primary.prevention}</p>
            </div>
        `;
        
        const container = document.getElementById('diagnosis-result');
        if (container) {
            container.innerHTML = html;
            container.style.display = 'block';
            container.scrollIntoView({ behavior: 'smooth' });
        }
    },
    
    async analyzeImage() {
        const fileInput = document.getElementById('image-input');
        const file = fileInput?.files[0];
        
        if (!file) {
            alert('Please select an image first');
            return;
        }
        
        this.showLoading();
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/analyze-image', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            let html = `
                <div class="alert alert-info">
                    <h5>Analysis Results</h5>
                    <p><strong>Quality:</strong> ${result.quality}</p>
                    <p><strong>Brightness:</strong> ${result.brightness}</p>
                    <p><strong>Contrast:</strong> ${result.contrast}</p>
                    <p><strong>Redness:</strong> ${result.redness}%</p>
                    <p><strong>Detail Level:</strong> ${result.edge_density}%</p>
            `;
            if (result.recommendations && result.recommendations.length > 0) {
                html += '<p><strong>Recommendations:</strong></p><ul>';
                result.recommendations.forEach(r => {
                    html += `<li>${r}</li>`;
                });
                html += '</ul>';
            }
            html += `</div>`;
            
            document.getElementById('analysis-result').innerHTML = html;
        } catch (error) {
            console.error('Error:', error);
            alert('Error analyzing image');
        } finally {
            this.hideLoading();
        }
    },
    
    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            const html = `
                <div class="stats-grid">
                    <div class="metric-card"><div class="metric-value">${stats.total_diseases}</div><div class="metric-label">Diseases</div></div>
                    <div class="metric-card"><div class="metric-value">${stats.total_symptoms}</div><div class="metric-label">Symptoms</div></div>
                    <div class="metric-card"><div class="metric-value">${stats.consultations || 0}</div><div class="metric-label">Consultations</div></div>
                </div>
            `;
            const container = document.getElementById('stats-container');
            if (container) container.innerHTML = html;
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    },
    
    async loadMedicalFact() {
        try {
            const response = await fetch('/api/medical-fact');
            const data = await response.json();
            const container = document.getElementById('fact-container');
            if (container) {
                container.innerHTML = `<div class="fact-card"><i class="fas fa-lightbulb"></i> ${data.fact}</div>`;
            }
        } catch (error) {
            console.error('Error loading fact:', error);
        }
    },
    
    async loadDiseases(searchTerm = '') {
        try {
            const response = await fetch('/api/diseases');
            const data = await response.json();
            
            let diseases = data.diseases || [];
            if (searchTerm) {
                diseases = diseases.filter(d => d.toLowerCase().includes(searchTerm.toLowerCase()));
            }
            
            const container = document.getElementById('diseases-list');
            if (!container) return;
            
            if (diseases.length === 0) {
                container.innerHTML = '<p class="text-muted">No diseases found</p>';
                return;
            }
            
            container.innerHTML = diseases.map(disease => {
                const d = data.details[disease];
                return `
                    <div class="card mb-2">
                        <div class="card-body">
                            <h5>${disease}</h5>
                            <p><strong>Severity:</strong> ${d.severity}</p>
                            <p><strong>Symptoms:</strong> ${d.symptoms.slice(0, 5).join(', ')}</p>
                            <button class="btn btn-sm btn-primary" onclick="window.medicalApp.showDiseaseDetails('${disease}')">View Details</button>
                        </div>
                    </div>
                `;
            }).join('');
        } catch (error) {
            console.error('Error loading diseases:', error);
        }
    },
    
    async showDiseaseDetails(diseaseName) {
        try {
            const response = await fetch(`/api/disease/${diseaseName}`);
            const data = await response.json();
            const d = data.details;
            alert(`
${diseaseName}

Severity: ${d.severity}
Duration: ${d.duration}

Symptoms:
${d.symptoms.join(', ')}

Recommendation:
${d.recommendation}

When to see doctor:
${d.when_to_see_doctor}

Prevention:
${d.prevention}
            `);
        } catch (error) {
            alert('Error loading disease details');
        }
    },
    
    async loadConsultationHistory() {
        try {
            const response = await fetch('/api/consultations');
            const data = await response.json();
            const consultations = data.consultations || [];
            
            const container = document.getElementById('history-list');
            if (!container) return;
            
            if (consultations.length === 0) {
                container.innerHTML = '<p class="text-muted">No consultations yet</p>';
                return;
            }
            
            container.innerHTML = consultations.map(c => `
                <div class="history-item">
                    <strong>${c.diagnosis}</strong>
                    <small class="text-muted float-end">${c.timestamp}</small>
                    <p class="mt-2"><strong>Symptoms:</strong> ${c.symptoms.join(', ')}</p>
                    <span class="badge bg-info">${c.severity}</span>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading history:', error);
        }
    },
    
    // Medication Functions
    addMedication() {
        const input = document.getElementById('medication-input');
        const medication = input?.value.trim();
        
        if (medication && !this.selectedMedications.includes(medication)) {
            this.selectedMedications.push(medication);
            this.updateMedicationsDisplay();
            input.value = '';
        }
    },
    
    removeMedication(medication) {
        this.selectedMedications = this.selectedMedications.filter(m => m !== medication);
        this.updateMedicationsDisplay();
    },
    
    updateMedicationsDisplay() {
        const container = document.getElementById('selected-medications');
        if (container) {
            container.innerHTML = this.selectedMedications.map(med => `
                <span class="badge bg-primary p-2">
                    ${med}
                    <i class="fas fa-times-circle ms-2" style="cursor:pointer;" onclick="window.medicalApp.removeMedication('${med}')"></i>
                </span>
            `).join('');
        }
    },
    
    async checkMedicationInteractions() {
        if (this.selectedMedications.length < 2) {
            alert('Please add at least 2 medications to check interactions');
            return;
        }
        
        this.showLoading();
        
        try {
            const medicationsParam = this.selectedMedications.join(',');
            const response = await fetch(`/api/check-interactions?medications=${encodeURIComponent(medicationsParam)}`);
            
            if (!response.ok) throw new Error('Failed to check interactions');
            
            const result = await response.json();
            this.displayInteractions(result.interactions);
        } catch (error) {
            console.error('Error:', error);
            alert('Error checking interactions');
        } finally {
            this.hideLoading();
        }
    },
    
    displayInteractions(interactions) {
        const container = document.getElementById('interaction-results');
        if (!container) return;
        
        if (interactions.length === 0) {
            container.innerHTML = '<div class="alert alert-success mt-3">✅ No interactions found between your medications.</div>';
        } else {
            container.innerHTML = `
                <div class="alert alert-warning mt-3">
                    <h6>⚠️ Interactions Found:</h6>
                    ${interactions.map(i => `
                        <div class="mt-2 p-2 bg-light rounded">
                            <strong>${i.medications.join(' + ')}</strong>
                            <p class="text-danger mb-0 small">${i.warning}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    },
    
    // Appointment Functions
    async scheduleAppointment() {
        const doctor_name = document.getElementById('doctor-name')?.value;
        const specialty = document.getElementById('specialty')?.value;
        const appointment_date = document.getElementById('appointment-date')?.value;
        const notes = document.getElementById('appointment-notes')?.value;
        
        if (!doctor_name || !specialty || !appointment_date) {
            alert('Please fill all required fields');
            return;
        }
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/appointments', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ doctor_name, specialty, appointment_date, notes })
            });
            
            if (response.ok) {
                alert('✅ Appointment scheduled successfully!');
                document.getElementById('doctor-name').value = '';
                document.getElementById('appointment-date').value = '';
                document.getElementById('appointment-notes').value = '';
                await this.loadAppointments();
            } else {
                alert('Failed to schedule appointment');
            }
        } catch (error) {
            alert('Error scheduling appointment');
        } finally {
            this.hideLoading();
        }
    },
    
    async loadAppointments() {
        try {
            const response = await fetch('/api/appointments');
            const data = await response.json();
            const appointments = data.appointments || [];
            
            const container = document.getElementById('appointments-list');
            if (!container) return;
            
            if (appointments.length === 0) {
                container.innerHTML = '<p class="text-muted">No appointments scheduled</p>';
                return;
            }
            
            container.innerHTML = appointments.map(a => `
                <div class="history-item">
                    <strong>Dr. ${a.doctor_name}</strong> - ${a.specialty}
                    <br>
                    <small>📅 ${new Date(a.appointment_date).toLocaleString()}</small>
                    ${a.notes ? `<p class="mt-2 small">📝 ${a.notes}</p>` : ''}
                    <span class="badge bg-success float-end">${a.status}</span>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading appointments:', error);
        }
    },
    
    cancelAppointment(appointmentId) {
        if (confirm('Are you sure you want to cancel this appointment?')) {
            alert('Cancellation feature coming soon');
        }
    }
};

// Initialize
window.medicalApp = MedicalApp;

// Auto-initialize when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    MedicalApp.init();
});

// Global functions for inline onclick handlers
window.toggleSymptom = (s) => MedicalApp.toggleSymptom(s);
window.performDiagnosis = () => MedicalApp.performDiagnosis();
window.analyzeImage = () => MedicalApp.analyzeImage();
window.addMedication = () => MedicalApp.addMedication();
window.removeMedication = (m) => MedicalApp.removeMedication(m);
window.checkMedicationInteractions = () => MedicalApp.checkMedicationInteractions();
window.scheduleAppointment = () => MedicalApp.scheduleAppointment();
window.loadAppointments = () => MedicalApp.loadAppointments();
window.showDiseaseDetails = (d) => MedicalApp.showDiseaseDetails(d);
window.cancelAppointment = (id) => MedicalApp.cancelAppointment(id);
