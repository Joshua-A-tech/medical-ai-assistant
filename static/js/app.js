// Medical AI Assistant - Complete Frontend

const MedicalApp = {
    selectedSymptoms: new Set(),
    selectedMedications: [],
    
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
                    `<span class="symptom-badge" onclick="medicalApp.toggleSymptom('${s}')">${s}</span>`
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
            <div class="diagnosis-card" style="background:#e0f2fe; padding:20px; border-radius:10px; margin-top:20px;">
                <h3>🎯 Primary Diagnosis: ${primary.disease}</h3>
                <p><strong>Match Confidence:</strong> ${primary.match_percentage}%</p>
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
                </div>
            `;
            document.getElementById('analysis-result').innerHTML = html;
        } catch (error) {
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
                    <div class="metric-card"><div class="metric-value">${stats.total_diseases}</div><div>Diseases</div></div>
                    <div class="metric-card"><div class="metric-value">${stats.total_symptoms}</div><div>Symptoms</div></div>
                    <div class="metric-card"><div class="metric-value">${stats.consultations || 0}</div><div>Consultations</div></div>
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
                            <button class="btn btn-sm btn-primary" onclick="medicalApp.showDiseaseDetails('${disease}')">View Details</button>
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
                    <i class="fas fa-times-circle ms-2" style="cursor:pointer;" onclick="medicalApp.removeMedication('${med}')"></i>
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
            alert('Error checking interactions: ' + error.message);
        } finally {
            this.hideLoading();
        }
    },
    
    displayInteractions(interactions) {
        const container = document.getElementById('interaction-results');
        if (!container) return;
        
        if (!interactions || interactions.length === 0) {
            container.innerHTML = '<div class="alert alert-success mt-3">✅ No interactions found between your medications.</div>';
            return;
        }
        
        let html = '<div class="mt-3">';
        
        for (let inter of interactions) {
            const severityClass = inter.severity === 'critical' ? 'danger' : 'warning';
            const drug1 = inter.medications[0];
            const drug2 = inter.medications[1];
            
            html += `
                <div class="alert alert-${severityClass} mt-2">
                    <div class="d-flex align-items-start">
                        <i class="fas ${severityClass === 'danger' ? 'fa-skull-crossbones' : 'fa-exclamation-triangle'} fa-2x me-3 mt-1"></i>
                        <div>
                            <strong>⚠️ ${drug1} + ${drug2}</strong>
                            <p class="mb-1 mt-2"><strong>Severity:</strong> <span class="badge ${severityClass === 'danger' ? 'bg-danger' : 'bg-warning'}">${inter.severity.toUpperCase()}</span></p>
                            <p class="mb-1"><strong>Clinical Effect:</strong> ${inter.effect || 'Unknown effect'}</p>
                            <p class="mb-0"><strong>Management:</strong> ${inter.management || 'Consult healthcare provider'}</p>
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += '<div class="alert alert-info mt-3"><i class="fas fa-info-circle"></i> <strong>Important:</strong> Always consult your healthcare provider before combining medications.</div>';
        container.innerHTML = html;
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
    }
};

// Initialize
const medicalApp = MedicalApp;
medicalApp.init();

// Global functions
window.medicalApp = medicalApp;
window.addMedication = () => medicalApp.addMedication();
window.removeMedication = (m) => medicalApp.removeMedication(m);
window.checkMedicationInteractions = () => medicalApp.checkMedicationInteractions();
window.scheduleAppointment = () => medicalApp.scheduleAppointment();
window.loadAppointments = () => medicalApp.loadAppointments();
window.toggleSymptom = (s) => medicalApp.toggleSymptom(s);
window.performDiagnosis = () => medicalApp.performDiagnosis();
window.analyzeImage = () => medicalApp.analyzeImage();
window.showDiseaseDetails = (d) => medicalApp.showDiseaseDetails(d);

// ============ HEALTH CHECKUP FUNCTIONS ============

async function calculateHealthCheckup() {
    const height = parseFloat(document.getElementById('height')?.value);
    const weight = parseFloat(document.getElementById('weight')?.value);
    const age = parseInt(document.getElementById('age')?.value);
    const activity = document.getElementById('activity')?.value;
    const systolic = parseInt(document.getElementById('systolic')?.value);
    const diastolic = parseInt(document.getElementById('diastolic')?.value);
    
    if (!height || !weight) {
        alert('Please enter height and weight');
        return;
    }
    
    showLoading();
    
    const requestData = {
        height_cm: height,
        weight_kg: weight,
        systolic_bp: systolic || null,
        diastolic_bp: diastolic || null,
        age: age || null,
        activity_level: activity || 'sedentary'
    };
    
    try {
        const response = await fetch('/api/health-checkup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        displayHealthResults(result);
    } catch (error) {
        console.error('Error:', error);
        alert('Error calculating health metrics');
    } finally {
        hideLoading();
    }
}

function displayHealthResults(result) {
    const container = document.getElementById('health-results');
    if (!container) return;
    
    const metrics = result.metrics;
    const bp = result.blood_pressure;
    const healthScore = result.health_score;
    const healthRating = result.health_rating;
    
    // Determine score color
    let scoreColor = 'success';
    if (healthScore < 40) scoreColor = 'danger';
    else if (healthScore < 60) scoreColor = 'warning';
    else if (healthScore < 80) scoreColor = 'info';
    
    let html = `
        <div class="text-center mb-4">
            <div class="display-4 fw-bold text-${scoreColor}">${healthScore}</div>
            <div class="badge bg-${scoreColor} fs-6">${healthRating} Health Rating</div>
        </div>
        
        <div class="alert alert-info">
            <i class="fas fa-chart-simple"></i> <strong>BMI: ${metrics.bmi}</strong> (${metrics.bmi_category})
            <div class="progress mt-2">
                <div class="progress-bar bg-${metrics.bmi === 'Normal weight' ? 'success' : 'warning'}" 
                     style="width: ${Math.min(metrics.bmi / 40 * 100, 100)}%"></div>
            </div>
            <small class="text-muted">${metrics.bmi_recommendation}</small>
        </div>
        
        ${bp ? `
        <div class="alert ${bp.status.includes('Normal') ? 'alert-success' : bp.status.includes('Elevated') ? 'alert-warning' : 'alert-danger'}">
            <i class="fas fa-heartbeat"></i> <strong>Blood Pressure: ${bp.systolic}/${bp.diastolic}</strong>
            <div>${bp.status}</div>
            <small class="text-muted">${bp.recommendation}</small>
        </div>
        ` : ''}
        
        <div class="row mt-3">
            <div class="col-6">
                <div class="metric-card">
                    <div class="metric-value">${metrics.bmr_calories}</div>
                    <div class="metric-label">BMR (calories/day)</div>
                </div>
            </div>
            <div class="col-6">
                <div class="metric-card">
                    <div class="metric-value">${metrics.tdee_calories}</div>
                    <div class="metric-label">TDEE (calories/day)</div>
                </div>
            </div>
        </div>
        
        <div class="alert alert-success mt-3">
            <strong><i class="fas fa-bullseye"></i> Ideal Weight Range:</strong><br>
            ${metrics.ideal_weight_range.min} - ${metrics.ideal_weight_range.max} kg
        </div>
        
        <div class="alert alert-warning">
            <strong><i class="fas fa-list"></i> Health Recommendations:</strong>
            <ul class="mt-2 mb-0">
                ${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        </div>
    `;
    
    container.innerHTML = html;
}

// Add to window for global access
window.calculateHealthCheckup = calculateHealthCheckup;

// ============ HEALTH CHECKUP FUNCTIONS ============

async function calculateHealthCheckup() {
    console.log("Calculating health checkup...");
    
    // Get form values
    const height = parseFloat(document.getElementById('height')?.value);
    const weight = parseFloat(document.getElementById('weight')?.value);
    const age = parseInt(document.getElementById('age')?.value);
    const activity = document.getElementById('activity')?.value;
    const systolic = parseInt(document.getElementById('systolic')?.value);
    const diastolic = parseInt(document.getElementById('diastolic')?.value);
    
    // Validate
    if (!height || !weight) {
        alert('Please enter height and weight');
        return;
    }
    
    // Show loading
    if (window.medicalApp) {
        window.medicalApp.showLoading();
    }
    
    const requestData = {
        height_cm: height,
        weight_kg: weight,
        systolic_bp: systolic || null,
        diastolic_bp: diastolic || null,
        age: age || null,
        activity_level: activity || 'sedentary'
    };
    
    try {
        const response = await fetch('/api/health-checkup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            displayHealthResults(result);
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error calculating health metrics. Please try again.');
    } finally {
        if (window.medicalApp) {
            window.medicalApp.hideLoading();
        }
    }
}

function displayHealthResults(result) {
    const container = document.getElementById('health-results');
    if (!container) return;
    
    const metrics = result.metrics;
    const bp = result.blood_pressure;
    const healthScore = result.health_score;
    
    // Score color
    let scoreColor = 'success';
    if (healthScore < 40) scoreColor = 'danger';
    else if (healthScore < 60) scoreColor = 'warning';
    else if (healthScore < 80) scoreColor = 'info';
    
    let html = `
        <div class="text-center mb-4">
            <div class="display-4 fw-bold text-${scoreColor}">${healthScore}</div>
            <span class="badge bg-${scoreColor} fs-6">${result.health_rating}</span>
            <div class="small text-muted">Health Score</div>
        </div>
        
        <div class="alert alert-info">
            <strong>📊 BMI: ${metrics.bmi}</strong> (${metrics.bmi_category})
            <div class="progress mt-2">
                <div class="progress-bar ${metrics.bmi_category === 'Normal weight' ? 'bg-success' : 'bg-warning'}" 
                     style="width: ${Math.min(metrics.bmi / 40 * 100, 100)}%"></div>
            </div>
            <small class="d-block mt-2">${metrics.bmi_recommendation}</small>
        </div>`;
    
    if (bp && bp.status) {
        let bpColor = 'success';
        if (bp.status.includes('Elevated')) bpColor = 'warning';
        else if (bp.status.includes('Stage')) bpColor = 'danger';
        else if (bp.status.includes('Crisis')) bpColor = 'danger';
        
        html += `
        <div class="alert alert-${bpColor}">
            <strong>❤️ Blood Pressure: ${bp.systolic}/${bp.diastolic}</strong>
            <div>${bp.status}</div>
            <small>${bp.recommendation || 'Monitor regularly'}</small>
        </div>`;
    }
    
    html += `
        <div class="row mt-3">
            <div class="col-6">
                <div class="metric-card">
                    <div class="metric-value">${metrics.bmr_calories}</div>
                    <div class="metric-label">BMR (calories/day)</div>
                </div>
            </div>
            <div class="col-6">
                <div class="metric-card">
                    <div class="metric-value">${metrics.tdee_calories}</div>
                    <div class="metric-label">Daily Calories</div>
                </div>
            </div>
        </div>
        
        <div class="alert alert-success mt-3">
            <strong>🎯 Healthy Weight Range:</strong><br>
            ${metrics.ideal_weight_range.min} - ${metrics.ideal_weight_range.max} kg
        </div>
        
        <div class="alert alert-warning">
            <strong>📋 Health Recommendations:</strong>
            <ul class="mt-2 mb-0">
                ${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        </div>
    `;
    
    container.innerHTML = html;
}

// Make global
window.calculateHealthCheckup = calculateHealthCheckup;

// ============ HEALTH CHECKUP FUNCTION ============

async function calculateHealthCheckup() {
    console.log("Calculating health checkup...");
    
    // Get values from form
    const height = parseFloat(document.getElementById('height')?.value);
    const weight = parseFloat(document.getElementById('weight')?.value);
    const age = parseInt(document.getElementById('age')?.value);
    const activity = document.getElementById('activity')?.value;
    const systolic = parseInt(document.getElementById('systolic')?.value);
    const diastolic = parseInt(document.getElementById('diastolic')?.value);
    
    // Validate
    if (!height || !weight) {
        alert('Please enter height and weight');
        return;
    }
    
    // Show loading
    if (window.medicalApp && window.medicalApp.showLoading) {
        window.medicalApp.showLoading();
    }
    
    const requestData = {
        height_cm: height,
        weight_kg: weight,
        systolic_bp: systolic || null,
        diastolic_bp: diastolic || null,
        age: age || null,
        activity_level: activity || 'sedentary'
    };
    
    try {
        const response = await fetch('/api/health-checkup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        console.log("Health result:", result);
        
        if (result.success) {
            displayHealthResults(result);
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error calculating health metrics: ' + error.message);
    } finally {
        if (window.medicalApp && window.medicalApp.hideLoading) {
            window.medicalApp.hideLoading();
        }
    }
}

function displayHealthResults(result) {
    const container = document.getElementById('health-results');
    if (!container) {
        console.error("Health results container not found");
        return;
    }
    
    const bmi = result.bmi;
    const bmiCategory = result.bmi_category;
    const healthScore = result.health_score;
    const healthRating = result.health_rating;
    const recommendation = result.recommendation;
    const idealMin = result.ideal_weight_range.min;
    const idealMax = result.ideal_weight_range.max;
    
    // Determine color based on BMI category
    let bmiColor = 'info';
    if (bmiCategory === 'Normal weight') bmiColor = 'success';
    else if (bmiCategory === 'Overweight') bmiColor = 'warning';
    else if (bmiCategory === 'Obese') bmiColor = 'danger';
    else if (bmiCategory === 'Underweight') bmiColor = 'warning';
    
    // Score color
    let scoreColor = 'success';
    if (healthScore < 40) scoreColor = 'danger';
    else if (healthScore < 60) scoreColor = 'warning';
    else if (healthScore < 80) scoreColor = 'info';
    
    const html = `
        <div class="text-center mb-4">
            <div class="display-4 fw-bold text-${scoreColor}">${healthScore}</div>
            <span class="badge bg-${scoreColor} fs-6">${healthRating}</span>
            <div class="small text-muted">Health Score</div>
        </div>
        
        <div class="alert alert-${bmiColor}">
            <strong>📊 BMI: ${bmi}</strong> (${bmiCategory})
            <div class="progress mt-2">
                <div class="progress-bar bg-${bmiColor}" 
                     style="width: ${Math.min(bmi / 40 * 100, 100)}%"></div>
            </div>
            <small class="d-block mt-2">${recommendation}</small>
        </div>
        
        <div class="alert alert-success mt-3">
            <strong>🎯 Healthy Weight Range:</strong><br>
            ${idealMin} - ${idealMax} kg
        </div>
        
        <div class="alert alert-info mt-3">
            <strong>💡 Health Tips:</strong>
            <ul class="mt-2 mb-0">
                <li>Get 7-8 hours of sleep daily</li>
                <li>Drink 8+ glasses of water daily</li>
                <li>Exercise 30 minutes, 5 days a week</li>
                <li>Eat a balanced diet with fruits and vegetables</li>
            </ul>
        </div>
    `;
    
    container.innerHTML = html;
}

// Make function global
window.calculateHealthCheckup = calculateHealthCheckup;

// Ensure the footer links work with the app
if (window.medicalApp) {
    const originalSwitchTab = window.medicalApp.switchTab;
    window.medicalApp.switchTab = function(tabName) {
        if (originalSwitchTab) originalSwitchTab.call(this, tabName);
        // Close mobile menu if open
        const navbarCollapse = document.querySelector('.navbar-collapse');
        if (navbarCollapse && navbarCollapse.classList.contains('show')) {
            navbarCollapse.classList.remove('show');
        }
    };
}

// ============ MOBILE RESPONSIVENESS ============

// Close mobile menu when clicking a link
document.querySelectorAll('.nav-link, .navbar-nav a').forEach(link => {
    link.addEventListener('click', () => {
        const navbarCollapse = document.querySelector('.navbar-collapse');
        if (navbarCollapse && navbarCollapse.classList.contains('show')) {
            navbarCollapse.classList.remove('show');
        }
    });
});

// Handle touch events for symptom badges
function initTouchEvents() {
    const isTouch = 'ontouchstart' in window;
    if (isTouch) {
        document.querySelectorAll('.symptom-badge').forEach(badge => {
            badge.addEventListener('touchstart', function(e) {
                e.preventDefault();
                this.click();
            });
        });
    }
}

// Call on load
document.addEventListener('DOMContentLoaded', () => {
    initTouchEvents();
});

// Adjust layout on orientation change
window.addEventListener('orientationchange', function() {
    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
    }, 100);
});

// Fix for 100vh on mobile browsers
function setVh() {
    let vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
}

window.addEventListener('resize', setVh);
setVh();
