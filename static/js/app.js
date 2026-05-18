
const MedicalApp = {
    selectedSymptoms: new Set(),
    selectedMedications: [],
    
    init() {
        console.log('Medical App Starting...');
        this.loadSymptoms();
        this.loadStats();
        this.loadMedicalFact();
        this.loadDiseases();
        this.loadAppointments();
        this.loadConsultationHistory();
        this.setupEventListeners();
    },
    
    setupEventListeners() {
        document.querySelectorAll('[data-tab]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(link.getAttribute('data-tab'));
            });
        });
        
        const searchInput = document.getElementById('disease-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.loadDiseases(e.target.value);
            });
        }
        
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
        const selectedTab = document.getElementById(tabName + '-tab');
        if (selectedTab) selectedTab.style.display = 'block';
        
        if (tabName === 'appointments') this.loadAppointments();
        if (tabName === 'history') this.loadConsultationHistory();
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
                    preview.innerHTML = '<img src="' + e.target.result + '" style="max-width:100%; margin-top:10px;">';
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
                let html = '';
                for (let s of data.symptoms) {
                    html += '<span class="symptom-badge" onclick="medicalApp.toggleSymptom(\'' + s + '\')">' + s + '</span>';
                }
                container.innerHTML = html;
            }
        } catch(e) { console.error(e); }
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
        
        const data = {
            symptoms: Array.from(this.selectedSymptoms),
            age_group: document.getElementById('age-group').value,
            duration: document.getElementById('duration').value,
            severity: document.getElementById('severity').value
        };
        
        try {
            const response = await fetch('/api/diagnose', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            this.displayDiagnosis(result);
            this.loadStats();
            this.loadConsultationHistory();
        } catch(e) { alert('Error'); }
        finally { this.hideLoading(); }
    },
    
    displayDiagnosis(result) {
        const p = result.primary_diagnosis;
        const html = '<div style="background:#e0f2fe; padding:20px; border-radius:10px; margin-top:20px;">' +
            '<h3>Primary Diagnosis: ' + p.disease + '</h3>' +
            '<p><strong>Match:</strong> ' + p.match_percentage + '%</p>' +
            '<p><strong>Severity:</strong> ' + p.severity + '</p>' +
            '<p><strong>Duration:</strong> ' + p.duration + '</p>' +
            '<p><strong>Recommendation:</strong> ' + p.recommendation + '</p>' +
            '<p><strong>When to see doctor:</strong> ' + p.when_to_see_doctor + '</p>' +
            '<p><strong>Prevention:</strong> ' + p.prevention + '</p>' +
            '</div>';
        
        const container = document.getElementById('diagnosis-result');
        if (container) {
            container.innerHTML = html;
            container.style.display = 'block';
        }
    },
    
    async analyzeImage() {
        const file = document.getElementById('image-input').files[0];
        if (!file) { alert('Please select an image'); return; }
        
        this.showLoading();
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/analyze-image', { method: 'POST', body: formData });
            const result = await response.json();
            let html = '<div class="alert alert-info"><h5>Analysis Results</h5>' +
                '<p>Quality: ' + result.quality + '</p>' +
                '<p>Brightness: ' + result.brightness + '</p>' +
                '<p>Contrast: ' + result.contrast + '</p>' +
                '<p>Redness: ' + result.redness + '%</p>';
            if (result.recommendations) {
                for (let r of result.recommendations) {
                    html += '<p>⚠️ ' + r + '</p>';
                }
            }
            html += '</div>';
            document.getElementById('analysis-result').innerHTML = html;
        } catch(e) { alert('Error'); }
        finally { this.hideLoading(); }
    },
    
    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            const html = '<div style="text-align:center">' +
                '<h3>' + stats.total_diseases + '</h3><p>Diseases</p>' +
                '<h3>' + stats.total_symptoms + '</h3><p>Symptoms</p>' +
                '<h3>' + (stats.consultations || 0) + '</h3><p>Consultations</p>' +
                '</div>';
            const container = document.getElementById('stats-container');
            if (container) container.innerHTML = html;
        } catch(e) { console.error(e); }
    },
    
    async loadMedicalFact() {
        try {
            const response = await fetch('/api/medical-fact');
            const data = await response.json();
            const container = document.getElementById('fact-container');
            if (container) {
                container.innerHTML = '<div class="alert alert-info">💡 ' + data.fact + '</div>';
            }
        } catch(e) { console.error(e); }
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
                container.innerHTML = '<p>No diseases found</p>';
                return;
            }
            let html = '';
            for (let disease of diseases) {
                const d = data.details[disease];
                html += '<div class="card mb-2"><div class="card-body">' +
                    '<h5>' + disease + '</h5>' +
                    '<p><strong>Severity:</strong> ' + d.severity + '</p>' +
                    '<p><strong>Symptoms:</strong> ' + d.symptoms.slice(0, 5).join(', ') + '</p>' +
                    '<button class="btn btn-sm btn-primary" onclick="medicalApp.showDiseaseDetails(\'' + disease + '\')">View Details</button>' +
                    '</div></div>';
            }
            container.innerHTML = html;
        } catch(e) { console.error(e); }
    },
    
    async showDiseaseDetails(diseaseName) {
        try {
            const response = await fetch('/api/disease/' + diseaseName);
            const data = await response.json();
            const d = data.details;
            alert(diseaseName + '\n\nSeverity: ' + d.severity + '\nDuration: ' + d.duration +
                '\n\nSymptoms:\n' + d.symptoms.join(', ') +
                '\n\nRecommendation:\n' + d.recommendation +
                '\n\nWhen to see doctor:\n' + d.when_to_see_doctor);
        } catch(e) { alert('Error loading details'); }
    },
    
    async loadConsultationHistory() {
        try {
            const response = await fetch('/api/consultations');
            const data = await response.json();
            const consultations = data.consultations || [];
            const container = document.getElementById('history-list');
            if (!container) return;
            if (consultations.length === 0) {
                container.innerHTML = '<p>No consultations yet</p>';
                return;
            }
            let html = '';
            for (let c of consultations) {
                html += '<div class="card mb-2"><div class="card-body">' +
                    '<h6>' + c.diagnosis + '</h6>' +
                    '<p>' + c.timestamp + '</p>' +
                    '<p>Symptoms: ' + c.symptoms.join(', ') + '</p>' +
                    '<span class="badge bg-info">' + c.severity + '</span>' +
                    '</div></div>';
            }
            container.innerHTML = html;
        } catch(e) { console.error(e); }
    },
    
    async scheduleAppointment() {
        const doctor_name = document.getElementById('doctor-name')?.value;
        const specialty = document.getElementById('specialty')?.value;
        const appointment_date = document.getElementById('appointment-date')?.value;
        const notes = document.getElementById('appointment-notes')?.value;
        
        if (!doctor_name || !specialty || !appointment_date) {
            alert('Please fill all fields');
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
                alert('Appointment scheduled successfully!');
                document.getElementById('doctor-name').value = '';
                document.getElementById('appointment-date').value = '';
                document.getElementById('appointment-notes').value = '';
                this.loadAppointments();
            } else {
                alert('Failed to schedule appointment');
            }
        } catch(e) { alert('Error'); }
        finally { this.hideLoading(); }
    },
    
    async loadAppointments() {
        try {
            const response = await fetch('/api/appointments');
            const data = await response.json();
            const appointments = data.appointments || [];
            const container = document.getElementById('appointments-list');
            if (!container) return;
            if (appointments.length === 0) {
                container.innerHTML = '<p>No appointments scheduled</p>';
                return;
            }
            let html = '';
            for (let a of appointments) {
                html += '<div class="card mb-2"><div class="card-body">' +
                    '<h6>Dr. ' + a.doctor_name + ' - ' + a.specialty + '</h6>' +
                    '<p>📅 ' + new Date(a.appointment_date).toLocaleString() + '</p>' +
                    (a.notes ? '<p>📝 ' + a.notes + '</p>' : '') +
                    '<span class="badge bg-success">' + a.status + '</span>' +
                    '</div></div>';
            }
            container.innerHTML = html;
        } catch(e) { console.error(e); }
    }
};

// Initialize
window.medicalApp = MedicalApp;
MedicalApp.init();

// Global functions
window.toggleSymptom = (s) => MedicalApp.toggleSymptom(s);
window.performDiagnosis = () => MedicalApp.performDiagnosis();
window.analyzeImage = () => MedicalApp.analyzeImage();
window.scheduleAppointment = () => MedicalApp.scheduleAppointment();
window.loadAppointments = () => MedicalApp.loadAppointments();
window.showDiseaseDetails = (d) => MedicalApp.showDiseaseDetails(d);