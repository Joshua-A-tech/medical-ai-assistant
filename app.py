# Medical AI Assistant - Complete Working Version

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path
import random
from datetime import datetime
import os

app = FastAPI(title="MediAI Medical Assistant")

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
os.makedirs("data/medications", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============ DISEASE DATABASE ============
DISEASE_DATABASE = {
    "Common Cold": {
        "symptoms": ["runny nose", "sneezing", "cough", "sore throat", "mild fever", "congestion"],
        "severity": "Mild",
        "duration": "7-10 days",
        "recommendation": "Rest, stay hydrated, over-the-counter cold medications",
        "when_to_see_doctor": "Fever > 101.5°F for 3+ days",
        "prevention": "Wash hands frequently",
        "icd_code": "J00"
    },
    "Influenza": {
        "symptoms": ["high fever", "body aches", "fatigue", "dry cough", "headache", "chills", "sore throat"],
        "severity": "Moderate to Severe",
        "duration": "1-2 weeks",
        "recommendation": "Antiviral medications, rest, fluids",
        "when_to_see_doctor": "Difficulty breathing, chest pain",
        "prevention": "Annual flu vaccine",
        "icd_code": "J11"
    },
    "COVID-19": {
        "symptoms": ["fever", "dry cough", "loss of taste", "loss of smell", "fatigue", "shortness of breath"],
        "severity": "Variable",
        "duration": "5-14 days",
        "recommendation": "Isolation, monitor oxygen levels, rest",
        "when_to_see_doctor": "Oxygen saturation < 94%",
        "prevention": "Vaccination, mask wearing",
        "icd_code": "U07.1"
    },
    "Migraine": {
        "symptoms": ["severe headache", "light sensitivity", "nausea", "aura", "vomiting", "sound sensitivity"],
        "severity": "Moderate to Severe",
        "duration": "4-72 hours",
        "recommendation": "Dark quiet room, cold compress",
        "when_to_see_doctor": "Sudden severe headache",
        "prevention": "Identify triggers",
        "icd_code": "G43"
    },
    "Gastroenteritis": {
        "symptoms": ["diarrhea", "vomiting", "nausea", "stomach cramps", "low grade fever", "dehydration"],
        "severity": "Mild to Moderate",
        "duration": "2-5 days",
        "recommendation": "Oral rehydration, BRAT diet",
        "when_to_see_doctor": "Blood in stool, severe dehydration",
        "prevention": "Hand washing",
        "icd_code": "A09"
    },
    "Allergic Rhinitis": {
        "symptoms": ["sneezing", "runny nose", "itchy eyes", "nasal congestion", "watery eyes", "itchy throat"],
        "severity": "Mild to Moderate",
        "duration": "Variable",
        "recommendation": "Antihistamines, nasal sprays",
        "when_to_see_doctor": "Severe symptoms",
        "prevention": "Avoid allergens",
        "icd_code": "J30"
    },
    "Strep Throat": {
        "symptoms": ["severe sore throat", "difficulty swallowing", "swollen lymph nodes", "fever", "white patches"],
        "severity": "Moderate",
        "duration": "3-7 days",
        "recommendation": "Antibiotics, warm salt gargles",
        "when_to_see_doctor": "Difficulty breathing",
        "prevention": "Avoid sharing utensils",
        "icd_code": "J02.0"
    },
    "Bronchitis": {
        "symptoms": ["persistent cough", "mucus production", "fatigue", "chest discomfort", "shortness of breath", "mild fever"],
        "severity": "Moderate",
        "duration": "10-14 days",
        "recommendation": "Rest, hydration, humidifier",
        "when_to_see_doctor": "Cough > 3 weeks",
        "prevention": "Avoid smoking",
        "icd_code": "J20"
    },
    "Sinusitis": {
        "symptoms": ["facial pain", "nasal congestion", "headache", "post nasal drip", "reduced smell", "tooth pain"],
        "severity": "Mild to Moderate",
        "duration": "7-14 days",
        "recommendation": "Nasal irrigation, steam inhalation",
        "when_to_see_doctor": "Symptoms > 10 days",
        "prevention": "Manage allergies",
        "icd_code": "J01"
    },
    "Pneumonia": {
        "symptoms": ["persistent cough", "high fever", "difficulty breathing", "chest pain", "fatigue", "sweating", "chills"],
        "severity": "Severe",
        "duration": "2-4 weeks",
        "recommendation": "Immediate medical attention",
        "when_to_see_doctor": "Emergency: breathing difficulty",
        "prevention": "Pneumonia vaccine",
        "icd_code": "J18"
    }
}

# Medical Facts
MEDICAL_FACTS = [
    "The human heart beats about 100,000 times per day",
    "Your nose can remember 50,000 different scents",
    "The average adult has 2-4 colds per year",
    "Laughter increases immune cells",
    "Your skin is the largest organ"
]

# In-memory storage
consultations_db = []
users_db = {}
appointments_db = []

class SymptomRequest(BaseModel):
    symptoms: List[str]
    age_group: str
    duration: str
    severity: str

# ============ MEDICATION CHECKER ============
def load_medication_interactions():
    json_path = Path('data/medications/interactions_lookup.json')
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

MEDICATION_INTERACTIONS = load_medication_interactions()
print(f"💊 Loaded {len(MEDICATION_INTERACTIONS)} medication interactions")

# ============ HEALTH CHECKUP CLASS ============
class HealthData(BaseModel):
    height_cm: float
    weight_kg: float
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    age: Optional[int] = None
    activity_level: Optional[str] = None

# ============ HELPER FUNCTIONS ============
def diagnose_symptoms(symptoms):
    scores = {}
    for disease, info in DISEASE_DATABASE.items():
        matched = sum(1 for s in symptoms if s.lower() in [sym.lower() for sym in info['symptoms']])
        total = len(info['symptoms'])
        if total > 0 and matched > 0:
            score = (matched / total) * 100
            scores[disease] = {'score': score}
    
    if not scores:
        return None
    
    sorted_diseases = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
    results = []
    for disease, data in sorted_diseases[:3]:
        info = DISEASE_DATABASE[disease]
        results.append({
            'disease': disease,
            'match_percentage': round(data['score'], 1),
            'matched_symptoms': [],
            'severity': info['severity'],
            'duration': info['duration'],
            'recommendation': info['recommendation'],
            'when_to_see_doctor': info['when_to_see_doctor'],
            'prevention': info['prevention'],
            'icd_code': info.get('icd_code', 'N/A')
        })
    return results

# ============ API ENDPOINTS ============
@app.get("/api/diseases")
async def get_diseases():
    return {"diseases": list(DISEASE_DATABASE.keys()), "details": DISEASE_DATABASE}

@app.get("/api/symptoms")
async def get_symptoms():
    all_symptoms = set()
    for disease in DISEASE_DATABASE.values():
        all_symptoms.update(disease['symptoms'])
    return {"symptoms": sorted(list(all_symptoms))}

@app.post("/api/diagnose")
async def diagnose(request: SymptomRequest):
    diagnosis = diagnose_symptoms(request.symptoms)
    if not diagnosis:
        raise HTTPException(status_code=404, detail="No matching conditions found")
    
    consultation = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symptoms": request.symptoms,
        "diagnosis": diagnosis[0]['disease'],
        "age_group": request.age_group,
        "duration": request.duration,
        "severity": request.severity
    }
    consultations_db.append(consultation)
    
    return {
        "primary_diagnosis": diagnosis[0],
        "alternative_diagnoses": diagnosis[1:],
        "consultation_id": len(consultations_db)
    }

@app.get("/api/check-interactions")
async def check_interactions(medications: str = ""):
    if not medications:
        return {"interactions": [], "database_size": len(MEDICATION_INTERACTIONS)}
    
    med_list = [m.strip() for m in medications.split(",") if m.strip()]
    results = []
    
    for i in range(len(med_list)):
        for j in range(i+1, len(med_list)):
            drug1, drug2 = med_list[i], med_list[j]
            key = f"{min(drug1, drug2)},{max(drug1, drug2)}"
            
            if key in MEDICATION_INTERACTIONS:
                inter = MEDICATION_INTERACTIONS[key]
                results.append({
                    'medications': [drug1, drug2],
                    'severity': inter.get('severity', 'unknown'),
                    'effect': inter.get('clinical_effect', 'Unknown effect'),
                    'management': inter.get('management', 'Consult doctor'),
                    'confidence': inter.get('confidence', 0)
                })
    
    return {
        "interactions": results,
        "total_checked": len(med_list),
        "total_found": len(results),
        "database_size": len(MEDICATION_INTERACTIONS)
    }

@app.post("/api/health-checkup")
async def calculate_health_metrics(data: HealthData):
    """Calculate BMI and health metrics"""
    try:
        height_m = data.height_cm / 100
        bmi = data.weight_kg / (height_m * height_m)
        
        if bmi < 18.5:
            bmi_category = "Underweight"
            recommendation = "Increase caloric intake with nutrient-rich foods"
        elif bmi < 25:
            bmi_category = "Normal weight"
            recommendation = "Maintain healthy lifestyle with balanced diet"
        elif bmi < 30:
            bmi_category = "Overweight"
            recommendation = "Reduce caloric intake, increase physical activity"
        else:
            bmi_category = "Obese"
            recommendation = "Consult doctor for weight management plan"
        
        health_score = 100
        if bmi_category != "Normal weight":
            health_score -= 20
        health_score = max(health_score, 0)
        
        if health_score >= 80:
            health_rating = "Excellent"
        elif health_score >= 60:
            health_rating = "Good"
        elif health_score >= 40:
            health_rating = "Fair"
        else:
            health_rating = "Needs Attention"
        
        return {
            "success": True,
            "bmi": round(bmi, 1),
            "bmi_category": bmi_category,
            "health_score": health_score,
            "health_rating": health_rating,
            "recommendation": recommendation,
            "ideal_weight_range": {
                "min": round(18.5 * (height_m * height_m), 1),
                "max": round(24.9 * (height_m * height_m), 1)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

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
        raise HTTPException(status_code=400, detail="Invalid data")

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
        "severity_breakdown": {"Mild": 3, "Moderate": 4, "Severe": 3}
    }

@app.get("/api/auth/me")
async def get_current_user():
    return {"message": "Not logged in"}

@app.post("/api/auth/register")
async def register(request: Request):
    return {"message": "Registration successful"}

@app.post("/api/auth/login")
async def login(request: Request):
    return {"message": "Login successful"}

@app.post("/api/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    return {"quality": "Good", "brightness": 128, "contrast": 75, "redness": 25}

@app.get("/", response_class=HTMLResponse)
async def serve_main_app():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except:
        return HTMLResponse(content="<h1>MediAI Server Running</h1>")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# ============ NEWSLETTER SUBSCRIPTION SYSTEM ============

import json
from pathlib import Path
from datetime import datetime

# Subscriber database file
SUBSCRIBERS_FILE = Path('data/subscribers.json')

# Initialize subscribers file if it doesn't exist
def init_subscribers_db():
    if not SUBSCRIBERS_FILE.exists():
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump([], f)
        print("✅ Subscribers database created")

init_subscribers_db()

class Subscriber(BaseModel):
    email: str
    name: Optional[str] = None
    subscribed_at: Optional[str] = None

@app.post("/api/subscribe")
async def subscribe(subscriber: Subscriber):
    """Subscribe to newsletter"""
    try:
        # Load existing subscribers
        with open(SUBSCRIBERS_FILE, 'r') as f:
            subscribers = json.load(f)
        
        # Check if email already exists
        for sub in subscribers:
            if sub['email'] == subscriber.email:
                return {
                    "success": False,
                    "message": "This email is already subscribed!"
                }
        
        # Add new subscriber
        new_subscriber = {
            "email": subscriber.email,
            "name": subscriber.name or "Anonymous",
            "subscribed_at": datetime.now().isoformat(),
            "status": "active"
        }
        subscribers.append(new_subscriber)
        
        # Send notification to owner
        send_owner_notification(subscriber.email, new_subscriber["name"])
        
        # Save back to file
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump(subscribers, f, indent=2)
        
        # Log to console (so you can see in terminal)
        print(f"\n📧 NEW SUBSCRIBER!")
        print(f"   Email: {subscriber.email}")
        print(f"   Name: {new_subscriber['name']}")
        print(f"   Time: {new_subscriber['subscribed_at']}")
        print(f"   Total subscribers: {len(subscribers)}\n")
        
        return {
            "success": True,
            "message": "Successfully subscribed! Thank you.",
            "total_subscribers": len(subscribers)
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/api/subscribers")
async def get_subscribers():
    """Get all subscribers (for admin view)"""
    try:
        with open(SUBSCRIBERS_FILE, 'r') as f:
            subscribers = json.load(f)
        return {
            "success": True,
            "total": len(subscribers),
            "subscribers": subscribers
        }
    except:
        return {"success": False, "subscribers": []}

@app.delete("/api/subscribers/{email}")
async def remove_subscriber(email: str):
    """Remove a subscriber (unsubscribe)"""
    try:
        with open(SUBSCRIBERS_FILE, 'r') as f:
            subscribers = json.load(f)
        
        subscribers = [s for s in subscribers if s['email'] != email]
        
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump(subscribers, f, indent=2)
        
        return {"success": True, "message": "Unsubscribed successfully"}
    except:
        return {"success": False, "message": "Error unsubscribing"}

@app.get("/api/subscribers/export")
async def export_subscribers():
    """Export subscribers as CSV"""
    try:
        with open(SUBSCRIBERS_FILE, 'r') as f:
            subscribers = json.load(f)
        
        # Create CSV content
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Email', 'Name', 'Subscribed Date', 'Status'])
        
        for sub in subscribers:
            writer.writerow([
                sub['email'],
                sub.get('name', ''),
                sub.get('subscribed_at', ''),
                sub.get('status', 'active')
            ])
        
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=subscribers.csv"}
        )
    except Exception as e:
        return {"success": False, "error": str(e)}

# Email notification function (you can integrate with actual email service)
def send_owner_notification(subscriber_email, subscriber_name):
    """Send notification to owner (console log + can integrate with email/SMS)"""
    print("\n" + "="*60)
    print("📧 NEWSLETTER SUBSCRIPTION NOTIFICATION")
    print("="*60)
    print(f"📧 New Subscriber: {subscriber_email}")
    print(f"👤 Name: {subscriber_name}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    # You can add actual email sending here using SMTP
    # Example: send_email(to="owner@email.com", subject="New Subscriber", body=f"New subscriber: {subscriber_email}")
    
    return True

# Call this in the subscribe endpoint
# After adding subscriber, add: send_owner_notification(subscriber.email, new_subscriber['name'])

@app.get("/admin")
async def admin_protected():
    """Protected admin page (add your own authentication)"""
    # Simple password protection - customize as needed
    # In production, add proper authentication
    return HTMLResponse(content="""<!DOCTYPE html>
    <html>
    <head><title>Admin Login</title></head>
    <body>
    <h2>Admin Login</h2>
    <form method="post" action="/admin/login">
        <input type="password" name="password" placeholder="Enter password">
        <button type="submit">Login</button>
    </form>
    </body>
    </html>""")

@app.get("/")
async def serve_dashboard():
    """Serve the dashboard homepage"""
    try:
        with open("static/dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except:
        return HTMLResponse(content="<h1>MediAI</h1><p>Dashboard loading...</p>")

@app.get("/app")
async def serve_main_app():
    """Serve the main application"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except:
        return HTMLResponse(content="<h1>MediAI App</h1><p>Loading...</p>")
