#!/usr/bin/env python
"""
This script adds ML capabilities to your app.py
Run it to automatically update your app.py
"""

import os
import re

# Read current app.py
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if ML is already integrated
if 'ml_integration' in content:
    print("✅ ML already integrated in app.py")
    exit(0)

# Add ML import at the top (after other imports)
ml_import = '''
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
'''

# Find where to insert (after other imports)
if 'from ml_integration' not in content:
    # Insert after the last import
    lines = content.split('\n')
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            insert_pos = i + 1
        elif line.startswith('app = FastAPI'):
            break
    
    lines.insert(insert_pos, ml_import)
    content = '\n'.join(lines)

# Update the diagnose function
old_diagnose_pattern = r'(@app\.post\("/api/diagnose"\)\s+async def diagnose\([^)]+\):\s+.*?)(?=@app\.|$)'
new_diagnose = '''
@app.post("/api/diagnose")
async def diagnose(request: SymptomRequest):
    # Try ML prediction first if available
    ml_result = None
    if ML_AVAILABLE:
        ml_result = ml_model.predict_with_details(request.symptoms)
    
    # Use ML result if confidence is high (>70%)
    if ml_result and ml_result['confidence'] > 70:
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
        "ml_used": ML_AVAILABLE and ml_result and ml_result['confidence'] > 70,
        "ml_confidence": ml_result['confidence'] if (ML_AVAILABLE and ml_result) else 0
    }
    consultations_db.append(consultation)
    
    return {
        "primary_diagnosis": diagnosis[0],
        "alternative_diagnoses": alternatives,
        "consultation_id": len(consultations_db),
        "ml_enabled": ML_AVAILABLE,
        "ml_used": ML_AVAILABLE and ml_result and ml_result['confidence'] > 70
    }
'''

# Replace the diagnose function using regex (simplified approach)
import re
pattern = r'(@app\.post\("/api/diagnose"\)\s+async def diagnose\([^)]+\):.*?)(?=@app\.(?:get|post|put|delete)|\Z)'
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, new_diagnose, content, flags=re.DOTALL)
else:
    print("⚠️ Could not find diagnose function to replace")

# Save updated app.py
with open('app_ml.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Updated app.py created as app_ml.py")
print("To use ML version: python app_ml.py")
