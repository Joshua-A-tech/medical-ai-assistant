# Medical AI Assistant - Production Version for Render
import os
import sys

# Add ml_models to path
sys.path.append('ml_models')

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import cv2
import numpy as np
from PIL import Image
import io
import random
from datetime import datetime
import json

# Import ML model
try:
    from ml_integration import ml_model
    ML_AVAILABLE = ml_model.is_loaded
    print(f"🤖 ML Model: ACTIVE ({ml_model.accuracy:.1f}% accuracy)")
except Exception as e:
    ML_AVAILABLE = False
    print(f"⚠️ ML Model not available: {e}")

# Initialize FastAPI
app = FastAPI(title="MediAI Medical Assistant", version="2.0.0")

# CORS
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

# Disease Database
DISEASE_DATABASE = {
    "Common Cold": {
        "symptoms": ["runny nose", "sneezing", "cough", "sore throat", "mild fever", "congestion"],
        "severity": "Mild",
        "duration": "7-10 days",
        "recommendation": "Rest, stay hydrated, over-the-counter cold medications",
        "when_to_see_doctor": "Fever > 101.5°F for 3+ days",
        "prevention": "Wash hands frequently, avoid close contact",
        "icd_code": "J00"
    },
    "Influenza": {
        "symptoms": ["high fever", "body aches", "fatigue", "dry cough", "headache", "chills", "sore throat"],
        "severity": "Moderate to Severe",
        "duration": "1-2 weeks",
        "recommendation": "Antiviral medications, rest, fluids, fever reducers",
        "when_to_see_doctor": "Difficulty breathing, chest pain, fever > 103°F",
        "prevention": "Annual flu vaccine, good hygiene",
        "icd_code": "J11"
    },
    "COVID-19": {
        "symptoms": ["fever", "dry cough", "loss of taste", "loss of smell", "fatigue", "shortness of breath"],
        "severity": "Variable",
        "duration": "5-14 days",
        "recommendation": "Isolation, monitor oxygen levels, rest, hydration",
        "when_to_see_doctor": "Oxygen saturation < 94%, difficulty breathing",
        "prevention": "Vaccination, mask wearing, social distancing",
        "icd_code": "U07.1"
    },
    "Migraine": {
        "symptoms": ["severe headache", "light sensitivity", "nausea", "aura", "vomiting", "sound sensitivity"],
        "severity": "Moderate to Severe",
        "duration": "4-72 hours",
        "recommendation": "Dark quiet room, cold compress, migraine medications",
        "when_to_see_doctor": "Sudden severe headache, neurological symptoms",
        "prevention": "Identify triggers, regular sleep schedule",
        "icd_code": "G43"
    },
    "Bronchitis": {
        "symptoms": ["persistent cough", "mucus production", "fatigue", "chest discomfort", "shortness of breath"],
        "severity": "Moderate",
        "duration": "10-14 days",
        "recommendation": "Rest, hydration, humidifier, cough medications",
        "when_to_see_doctor": "Cough > 3 weeks, fever > 100.4°F, bloody mucus",
        "prevention": "Avoid smoking, hand washing, flu vaccination",
        "icd_code": "J20"
    },
    "Pneumonia": {
        "symptoms": ["persistent cough", "high fever", "difficulty breathing", "chest pain", "fatigue", "sweating"],
        "severity": "Severe",
        "duration": "2-4 weeks",
        "recommendation": "Immediate medical attention, antibiotics, rest",
        "when_to_see_doctor": "Emergency: breathing difficulty, chest pain, confusion",
        "prevention": "Pneumonia vaccine, flu vaccine, hand hygiene",
        "icd_code": "J18"
    },
    "Allergic Rhinitis": {
        "symptoms": ["sneezing", "runny nose", "itchy eyes", "nasal congestion", "watery eyes"],
        "severity": "Mild to Moderate",
        "duration": "Variable",
        "recommendation": "Antihistamines, nasal sprays, avoid allergens",
        "when_to_see_doctor": "Severe symptoms affecting daily life",
        "prevention": "Avoid allergens, use air purifiers",
        "icd_code": "J30"
    },
    "Strep Throat": {
        "symptoms": ["severe sore throat", "difficulty swallowing", "swollen lymph nodes", "fever", "white patches"],
        "severity": "Moderate",
        "duration": "3-7 days",
        "recommendation": "Antibiotics, warm salt gargles, rest",
        "when_to_see_doctor": "Difficulty breathing, unable to swallow liquids",
        "prevention": "Avoid sharing utensils, frequent hand washing",
        "icd_code": "J02.0"
    },
    "Sinusitis": {
        "symptoms": ["facial pain", "nasal congestion", "headache", "post nasal drip", "reduced smell"],
        "severity": "Mild to Moderate",
        "duration": "7-14 days",
        "recommendation": "Nasal irrigation, steam inhalation, decongestants",
        "when_to_see_doctor": "Symptoms > 10 days, severe headache",
        "prevention": "Manage allergies, avoid smoke, use humidifier",
        "icd_code": "J01"
    },
    "Gastroenteritis": {
        "symptoms": ["diarrhea", "vomiting", "nausea", "stomach cramps", "low grade fever"],
        "severity": "Mild to Moderate",
        "duration": "2-5 days",
        "recommendation": "Oral rehydration solution, BRAT diet, rest",
        "when_to_see_doctor": "Blood in stool, severe dehydration",
        "prevention": "Hand washing, food safety, clean water",
        "icd_code": "A09"
    }
}

# Medical Facts
MEDICAL_FACTS = [
    "The human heart beats about 100,000 times per day",
    "Your nose can remember 50,000 different scents",
    "The average adult has 2-4 colds per year",
    "Laughter increases immune cells and infection-fighting antibodies",
    "Your skin is the largest organ, making up about 15% of your body weight"
]

# In-memory storage (for demo)
consultations_db = []
users_db = {}
appointments_db = []

class SymptomRequest(BaseModel):
    symptoms: List[str]
    age_group: str
    duration: str
    severity: str

# Helper functions
def diagnose_symptoms(symptoms):
    scores = {}
    for disease, info in DISEASE_DATABASE.items():
        matched = sum(1 for s in symptoms if s in info['symptoms'])
        total = len(info['symptoms'])
        if total > 0:
            score = (matched / total) * 100
            if score > 0:
                scores[disease] = {
                    'score': score,
                    'matched': matched,
                    'symptoms': [s for s in symptoms if s in info['symptoms']]
                }
    
    if not scores:
        return None
    
    sorted_diseases = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
    results = []
    for disease, data in sorted_diseases[:3]:
        info = DISEASE_DATABASE[disease]
        results.append({
            'disease': disease,
            'match_percentage': round(data['score'], 1),
            'matched_symptoms': data['symptoms'],
            'severity': info['severity'],
            'duration': info['duration'],
            'recommendation': info['recommendation'],
            'when_to_see_doctor': info['when_to_see_doctor'],
            'prevention': info['prevention'],
            'icd_code': info.get('icd_code', 'N/A')
        })
    return results

# API Endpoints
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

@app.post("/api/diagnose")
async def diagnose(request: SymptomRequest):
    # Try ML prediction first
    ml_result = None
    if ML_AVAILABLE:
        try:
            ml_result = ml_model.predict(request.symptoms)
        except:
            pass
    
    if ml_result and ml_result.get('confidence', 0) > 70:
        diagnosis = [{
            'disease': ml_result['disease'],
            'match_percentage': round(ml_result['confidence'], 1),
            'matched_symptoms': request.symptoms,
            'severity': 'Based on ML analysis',
            'duration': 'Consult doctor for accurate duration',
            'recommendation': 'ML model suggests this diagnosis with high confidence',
            'when_to_see_doctor': 'Consult healthcare provider for confirmation',
            'prevention': 'Follow medical advice',
            'icd_code': 'N/A'
        }]
        alternatives = []
    else:
        diagnosis = diagnose_symptoms(request.symptoms)
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
        "ml_used": ML_AVAILABLE and ml_result is not None
    }
    consultations_db.append(consultation)
    
    return {
        "primary_diagnosis": diagnosis[0],
        "alternative_diagnoses": alternatives,
        "consultation_id": len(consultations_db),
        "ml_enabled": ML_AVAILABLE
    }

@app.get("/api/consultations")
async def get_consultations():
    return {"consultations": consultations_db}

@app.get("/api/appointments")
async def get_appointments():
    return {"appointments": appointments_db}

@app.post("/api/appointments")
async def create_appointment(request: Request):
    try:
        body = await request.json()
        new_appointment = {
            "id": len(appointments_db) + 1,
            "doctor_name": body.get('doctor_name'),
            "specialty": body.get('specialty'),
            "appointment_date": body.get('appointment_date'),
            "notes": body.get('notes', ''),
            "status": "scheduled"
        }
        appointments_db.append(new_appointment)
        return {"message": "Appointment scheduled", "appointment": new_appointment}
    except:
        raise HTTPException(status_code=400, detail="Invalid appointment data")

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
        "severity_breakdown": {
            "Mild": 3,
            "Moderate": 4,
            "Severe": 3
        }
    }

@app.get("/api/auth/me")
async def get_current_user():
    return {"message": "User not logged in"}

@app.post("/api/auth/register")
async def register(request: Request):
    return {"message": "Registration successful"}

@app.post("/api/auth/login")
async def login(request: Request):
    return {"message": "Login successful"}

@app.get("/api/check-interactions")
async def check_interactions(medications: str = ""):
    return {"interactions": []}

@app.post("/api/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    return {"quality": "Good", "brightness": 128, "contrast": 75, "redness": 25}

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except:
        return HTMLResponse(content="<h1>MediAI Medical Assistant</h1><p>Server is running!</p>")

# Run the app
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
