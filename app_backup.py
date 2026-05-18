# app.py - Complete Working Version

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import cv2
import numpy as np
from PIL import Image
import io
import random
from datetime import datetime
import os
import uvicorn
from pydantic import Field
import uuid
# ML Model Integration
import sys
sys.path.append('ml_models')
try:
    from ml_integration import ml_model
    ML_AVAILABLE = ml_model.is_loaded
    print(f"🤖 ML Model: {'ACTIVE' if ML_AVAILABLE else 'INACTIVE'}")
    if ML_AVAILABLE:
        model_info = ml_model.get_model_info()
        print(f"   - Accuracy: {model_info['accuracy']:.1f}%")
        print(f"   - Diseases: {len(model_info['diseases'])}")
except Exception as e:
    ML_AVAILABLE = False
    print(f"⚠️ ML Model not available: {e}")
# ============ CREATE FASTAPI APP FIRST ============
app = FastAPI(title="MediAI Medical Assistant", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============ MODELS ============
class UserRegister(BaseModel):
    full_name: str
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class SymptomRequest(BaseModel):
    symptoms: List[str]
    age_group: str
    duration: str
    severity: str

class AppointmentCreate(BaseModel):
    doctor_name: str
    specialty: str
    appointment_date: str
    notes: Optional[str] = ""

class AppointmentUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

# ============ DATABASES (In-memory storage) ============
users_db = {}
consultations_db = []
appointments_db = []

# ============ DISEASE DATABASE ============
DISEASE_DATABASE = {
    "Common Cold": {
        "symptoms": ["runny nose", "sneezing", "cough", "sore throat", "mild fever", "congestion"],
        "severity": "Mild",
        "duration": "7-10 days",
        "recommendation": "Rest, stay hydrated, over-the-counter cold medications, honey for cough",
        "when_to_see_doctor": "Fever > 101.5°F for 3+ days, severe sinus pain, difficulty breathing",
        "prevention": "Wash hands frequently, avoid close contact with sick individuals",
        "icd_code": "J00"
    },
    "Influenza (Flu)": {
        "symptoms": ["high fever", "body aches", "fatigue", "dry cough", "headache", "chills", "sore throat"],
        "severity": "Moderate to Severe",
        "duration": "1-2 weeks",
        "recommendation": "Antiviral medications (within 48 hours), rest, fluids, fever reducers",
        "when_to_see_doctor": "Difficulty breathing, chest pain, severe weakness, fever > 103°F",
        "prevention": "Annual flu vaccine, good hygiene, avoid crowded places during flu season",
        "icd_code": "J11"
    },
    "COVID-19": {
        "symptoms": ["fever", "dry cough", "loss of taste", "loss of smell", "fatigue", "shortness of breath", "body aches"],
        "severity": "Variable",
        "duration": "5-14 days",
        "recommendation": "Isolation, monitor oxygen levels, rest, hydration, seek immediate care for breathing difficulties",
        "when_to_see_doctor": "Oxygen saturation < 94%, difficulty breathing, confusion, chest pain",
        "prevention": "Vaccination, mask wearing, social distancing, hand hygiene",
        "icd_code": "U07.1"
    },
    "Migraine": {
        "symptoms": ["severe headache", "light sensitivity", "nausea", "aura", "vomiting", "sound sensitivity"],
        "severity": "Moderate to Severe",
        "duration": "4-72 hours",
        "recommendation": "Dark quiet room, cold compress, migraine medications, avoid triggers",
        "when_to_see_doctor": "Sudden severe headache, neurological symptoms, frequency increasing",
        "prevention": "Identify triggers, regular sleep schedule, stress management, hydration",
        "icd_code": "G43"
    },
    "Gastroenteritis": {
        "symptoms": ["diarrhea", "vomiting", "nausea", "stomach cramps", "low grade fever", "dehydration"],
        "severity": "Mild to Moderate",
        "duration": "2-5 days",
        "recommendation": "Oral rehydration solution, BRAT diet (bananas, rice, applesauce, toast), rest",
        "when_to_see_doctor": "Blood in stool, severe dehydration, vomiting > 48 hours, high fever",
        "prevention": "Hand washing, food safety, clean water consumption",
        "icd_code": "A09"
    },
    "Allergic Rhinitis": {
        "symptoms": ["sneezing", "runny nose", "itchy eyes", "nasal congestion", "watery eyes", "itchy throat"],
        "severity": "Mild to Moderate",
        "duration": "Variable (exposure dependent)",
        "recommendation": "Antihistamines, nasal sprays, avoid allergens, air purifiers",
        "when_to_see_doctor": "Severe symptoms affecting daily life, sinus infections, asthma symptoms",
        "prevention": "Avoid allergens, keep windows closed during high pollen counts, use HEPA filters",
        "icd_code": "J30"
    },
    "Strep Throat": {
        "symptoms": ["severe sore throat", "difficulty swallowing", "swollen lymph nodes", "fever", "white patches on tonsils"],
        "severity": "Moderate",
        "duration": "3-7 days with treatment",
        "recommendation": "Antibiotics (prescription required), warm salt gargles, rest, hydration",
        "when_to_see_doctor": "Difficulty breathing, unable to swallow liquids, severe pain",
        "prevention": "Avoid sharing utensils, frequent hand washing, replace toothbrush after treatment",
        "icd_code": "J02.0"
    },
    "Bronchitis": {
        "symptoms": ["persistent cough", "mucus production", "fatigue", "chest discomfort", "shortness of breath", "mild fever"],
        "severity": "Moderate",
        "duration": "10-14 days",
        "recommendation": "Rest, hydration, humidifier, cough medications, avoid irritants",
        "when_to_see_doctor": "Cough > 3 weeks, fever > 100.4°F, bloody mucus, breathing difficulty",
        "prevention": "Avoid smoking, hand washing, flu vaccination, mask in polluted areas",
        "icd_code": "J20"
    },
    "Sinusitis": {
        "symptoms": ["facial pain", "nasal congestion", "headache", "post nasal drip", "reduced smell", "tooth pain"],
        "severity": "Mild to Moderate",
        "duration": "7-14 days",
        "recommendation": "Nasal irrigation, steam inhalation, decongestants, warm compresses",
        "when_to_see_doctor": "Symptoms > 10 days, severe headache, vision changes, high fever",
        "prevention": "Manage allergies, avoid smoke, use humidifier, treat colds promptly",
        "icd_code": "J01"
    },
    "Pneumonia": {
        "symptoms": ["persistent cough", "high fever", "difficulty breathing", "chest pain", "fatigue", "sweating", "chills"],
        "severity": "Severe",
        "duration": "2-4 weeks",
        "recommendation": "Immediate medical attention, antibiotics if bacterial, rest, oxygen therapy if needed",
        "when_to_see_doctor": "Emergency: breathing difficulty, chest pain, confusion, blue lips",
        "prevention": "Pneumonia vaccine, flu vaccine, hand hygiene, no smoking",
        "icd_code": "J18"
    }
}

# Medical Facts
MEDICAL_FACTS = [
    "The human heart beats about 100,000 times per day, pumping 2,000 gallons of blood.",
    "Your nose can remember 50,000 different scents.",
    "The average adult has 2-4 colds per year, while children may have 6-8.",
    "Laughter increases immune cells and infection-fighting antibodies.",
    "The human body has 60,000 miles of blood vessels.",
    "Your stomach gets a new lining every 3-4 days.",
    "The brain generates about 20 watts of power - enough to power a lightbulb.",
    "Fever is actually your body's defense mechanism against infections.",
    "The liver is the only organ that can completely regenerate itself.",
    "Your skin is the largest organ, making up about 15% of your body weight."
]

# ============ MEDICAL ASSISTANT CLASS ============
class MedicalAIAssistant:
    def __init__(self):
        self.disease_db = DISEASE_DATABASE
        
    def diagnose_symptoms(self, symptoms: List[str]):
        if not symptoms:
            return None
        
        scores = {}
        for disease, info in self.disease_db.items():
            matched = sum(1 for s in symptoms if s.lower() in [sym.lower() for sym in info['symptoms']])
            total_symptoms = len(info['symptoms'])
            score = (matched / total_symptoms) * 100 if total_symptoms > 0 else 0
            if matched > 0:
                scores[disease] = {
                    'score': score,
                    'matched_list': [s for s in symptoms if s.lower() in [sym.lower() for sym in info['symptoms']]],
                    'details': info
                }
        
        sorted_diseases = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        top_diagnoses = []
        for disease, details in sorted_diseases[:3]:
            if details['score'] > 0:
                top_diagnoses.append({
                    'disease': disease,
                    'match_percentage': round(details['score'], 1),
                    'matched_symptoms': details['matched_list'],
                    'severity': details['details']['severity'],
                    'duration': details['details']['duration'],
                    'recommendation': details['details']['recommendation'],
                    'when_to_see_doctor': details['details']['when_to_see_doctor'],
                    'prevention': details['details']['prevention'],
                    'icd_code': details['details'].get('icd_code', 'N/A')
                })
        
        return top_diagnoses
    
    def analyze_image(self, image_bytes):
        try:
            image = Image.open(io.BytesIO(image_bytes))
            img = np.array(image)
            
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            
            brightness = np.mean(gray)
            contrast = np.std(gray)
            red_channel = img[:,:,0]
            redness_score = np.mean(red_channel) / 255
            
            if brightness < 50:
                quality = "Poor (Too Dark)"
            elif brightness > 200:
                quality = "Poor (Too Bright)"
            elif contrast < 30:
                quality = "Poor (Low Contrast)"
            elif 80 <= brightness <= 180 and contrast >= 50:
                quality = "Good"
            else:
                quality = "Fair"
            
            edge_density = np.sum(edges > 0) / edges.size
            
            analysis = {
                "quality": quality,
                "brightness": round(float(brightness), 1),
                "contrast": round(float(contrast), 1),
                "redness": round(float(redness_score * 100), 1),
                "edge_density": round(float(edge_density * 100), 1),
                "recommendations": []
            }
            
            if redness_score > 0.6:
                analysis["recommendations"].append("High redness detected - may indicate inflammation")
            if edge_density < 0.05:
                analysis["recommendations"].append("Image appears blurry - try to keep camera steady")
                
            return analysis
        except Exception as e:
            return {"error": f"Image analysis failed: {str(e)}"}

assistant = MedicalAIAssistant()

# ============ AUTHENTICATION ENDPOINTS ============
@app.post("/api/auth/register")
async def register(user: UserRegister):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    users_db[user.username] = {
        "full_name": user.full_name,
        "email": user.email,
        "password": user.password,
        "created_at": datetime.now().isoformat()
    }
    
    return {"message": "Registration successful", "username": user.username}

@app.post("/api/auth/login")
async def login(user: UserLogin):
    if user.username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if users_db[user.username]["password"] != user.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {"message": "Login successful", "username": user.username, "access_token": "demo-token"}

@app.get("/api/auth/me")
async def get_current_user():
    if users_db:
        first_user = list(users_db.keys())[0]
        user = users_db[first_user]
        return {"username": first_user, "full_name": user["full_name"], "email": user["email"]}
    return {"message": "No user logged in"}

# ============ DISEASE ENDPOINTS ============
@app.get("/api/diseases")
async def get_diseases():
    return {"diseases": list(DISEASE_DATABASE.keys()), "details": DISEASE_DATABASE}

@app.get("/api/symptoms")
async def get_symptoms():
    all_symptoms = set()
    for disease in DISEASE_DATABASE.values():
        all_symptoms.update(disease['symptoms'])
    return {"symptoms": sorted(list(all_symptoms))}

@app.get("/api/disease/{disease_name}")
async def get_disease_details(disease_name: str):
    if disease_name in DISEASE_DATABASE:
        return {"disease": disease_name, "details": DISEASE_DATABASE[disease_name]}
    raise HTTPException(status_code=404, detail="Disease not found")

# ============ DIAGNOSIS ENDPOINTS ============
@app.post("/api/diagnose")
async def diagnose(request: SymptomRequest):
    # Try ML prediction first if available
    ml_result = None
    if ML_AVAILABLE:
        try:
            ml_result = ml_model.predict_with_details(request.symptoms)
        except Exception as e:
            print(f"ML prediction error: {e}")
    
    # Use ML result if confidence is high (>70%)
    if ml_result and ml_result.get('confidence', 0) > 70:
        diagnosis = [{
            'disease': ml_result['disease'],
            'match_percentage': round(ml_result['confidence'], 1),
            'matched_symptoms': ml_result.get('matched_symptoms', request.symptoms),
            'severity': ml_result.get('severity', 'Unknown'),
            'duration': ml_result.get('duration', 'Consult doctor'),
            'recommendation': ml_result.get('recommendation', 'Consult healthcare provider'),
            'when_to_see_doctor': ml_result.get('when_to_see_doctor', 'If symptoms persist'),
            'prevention': ml_result.get('prevention', 'Follow healthy lifestyle'),
            'icd_code': 'N/A',
            'ml_confidence': round(ml_result['confidence'], 1)
        }]
        
        # Create alternatives from top_3
        alternatives = []
        if ml_result.get('top_3'):
            for alt in ml_result['top_3'][1:3]:
                alternatives.append({
                    'disease': alt['disease'],
                    'match_percentage': round(alt['confidence'], 1),
                    'matched_symptoms': request.symptoms
                })
    else:
        # Fall back to rule-based diagnosis
        diagnosis = assistant.diagnose_symptoms(request.symptoms)
        if not diagnosis:
            raise HTTPException(status_code=404, detail="No matching conditions found")
        alternatives = diagnosis[1:] if len(diagnosis) > 1 else []
    
    # Save consultation
    consultation = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symptoms": request.symptoms,
        "diagnosis": diagnosis[0]['disease'],
        "age_group": request.age_group,
        "duration": request.duration,
        "severity": request.severity,
        "ml_used": ML_AVAILABLE and ml_result and ml_result.get('confidence', 0) > 70
    }
    consultations_db.append(consultation)
    
    return {
        "primary_diagnosis": diagnosis[0],
        "alternative_diagnoses": alternatives,
        "consultation_id": len(consultations_db),
        "ml_enabled": ML_AVAILABLE,
        "ml_used": ML_AVAILABLE and ml_result and ml_result.get('confidence', 0) > 70
    }

# ============ IMAGE ANALYSIS ============
@app.post("/api/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        analysis = assistant.analyze_image(contents)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image processing failed: {str(e)}")

# ============ MEDICATION INTERACTIONS ============
@app.get("/api/check-interactions")
async def check_interactions_get(medications: str = ""):
    if not medications:
        return {"interactions": []}
    
    med_list = [m.strip() for m in medications.split(",") if m.strip()]
    
    interaction_pairs = {
        ("Warfarin", "Aspirin"): "⚠️ Increased bleeding risk. Monitor for signs of bleeding.",
        ("Warfarin", "Ibuprofen"): "⚠️ Increased bleeding risk. Avoid combination if possible.",
        ("Metformin", "Insulin"): "⚠️ Risk of hypoglycemia. Monitor blood sugar closely.",
    }
    
    interactions = []
    for i in range(len(med_list)):
        for j in range(i + 1, len(med_list)):
            pair = tuple(sorted([med_list[i], med_list[j]]))
            if pair in interaction_pairs:
                interactions.append({
                    "medications": [pair[0], pair[1]],
                    "warning": interaction_pairs[pair]
                })
    
    return {"interactions": interactions}

# ============ APPOINTMENT ENDPOINTS ============
@app.get("/api/appointments")
async def get_appointments():
    """Get all appointments"""
    return {"appointments": appointments_db}

@app.post("/api/appointments")
async def create_appointment(appointment: AppointmentCreate):
    """Create a new appointment"""
    try:
        new_appointment = {
            "id": len(appointments_db) + 1,
            "username": "current_user",
            "doctor_name": appointment.doctor_name,
            "specialty": appointment.specialty,
            "appointment_date": appointment.appointment_date,
            "notes": appointment.notes,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        appointments_db.append(new_appointment)
        
        return {
            "message": "Appointment scheduled successfully",
            "appointment": new_appointment
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create appointment: {str(e)}")

@app.delete("/api/appointments/{appointment_id}")
async def cancel_appointment(appointment_id: int):
    """Cancel/Delete appointment"""
    for i, appointment in enumerate(appointments_db):
        if appointment.get('id') == appointment_id:
            deleted = appointments_db.pop(i)
            return {"message": "Appointment cancelled", "appointment": deleted}
    
    raise HTTPException(status_code=404, detail="Appointment not found")

# ============ HISTORY & STATS ============
@app.get("/api/consultations")
async def get_consultations():
    return {"consultations": consultations_db}

@app.get("/api/consultation-history")
async def get_consultation_history():
    return {"history": consultations_db}

@app.get("/api/medical-fact")
async def get_medical_fact():
    return {"fact": random.choice(MEDICAL_FACTS)}

@app.get("/api/stats")
async def get_stats():
    total_symptoms = sum(len(info['symptoms']) for info in DISEASE_DATABASE.values())
    return {
        "total_diseases": len(DISEASE_DATABASE),
        "total_symptoms": total_symptoms,
        "consultations": len(consultations_db),
        "total_users": len(users_db),
        "severity_breakdown": {
            "Mild": sum(1 for d in DISEASE_DATABASE.values() if d['severity'] == "Mild"),
            "Moderate": sum(1 for d in DISEASE_DATABASE.values() if d['severity'] == "Moderate"),
            "Severe": sum(1 for d in DISEASE_DATABASE.values() if d['severity'] == "Severe")
        }
    }

# ============ FRONTEND ============
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>MediAI Server Running</h1><p>Please ensure static/index.html exists</p>")

if __name__ == "__main__":
    print("=" * 50)
    print("🏥 MediAI Medical Assistant")
    print("=" * 50)
    print(f"Diseases in DB: {len(DISEASE_DATABASE)}")
    print(f"Server starting at: http://localhost:8000")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)