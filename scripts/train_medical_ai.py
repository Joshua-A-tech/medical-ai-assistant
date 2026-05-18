#!/usr/bin/env python
"""
Medical AI Training Script - Works with Python 3.14
No TensorFlow required - uses scikit-learn only
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib
import json
import os
from datetime import datetime

print("="*60)
print("🏥 Medical AI Training System")
print("="*60)

# Create directories
os.makedirs("ml_models", exist_ok=True)

# Real medical symptom-disease mapping
print("\n📊 Creating medical knowledge base...")

symptom_database = {
    'Common Cold': {
        'symptoms': ['runny nose', 'sneezing', 'cough', 'sore throat', 'mild fever', 'congestion'],
        'severity': 'Mild',
        'duration': '7-10 days'
    },
    'Influenza': {
        'symptoms': ['high fever', 'body aches', 'fatigue', 'dry cough', 'headache', 'chills', 'sore throat'],
        'severity': 'Moderate to Severe',
        'duration': '1-2 weeks'
    },
    'COVID-19': {
        'symptoms': ['fever', 'dry cough', 'loss of taste', 'loss of smell', 'fatigue', 'shortness of breath'],
        'severity': 'Variable',
        'duration': '5-14 days'
    },
    'Migraine': {
        'symptoms': ['severe headache', 'light sensitivity', 'nausea', 'aura', 'vomiting', 'sound sensitivity'],
        'severity': 'Moderate to Severe',
        'duration': '4-72 hours'
    },
    'Bronchitis': {
        'symptoms': ['persistent cough', 'mucus production', 'fatigue', 'chest discomfort', 'shortness of breath'],
        'severity': 'Moderate',
        'duration': '10-14 days'
    },
    'Pneumonia': {
        'symptoms': ['persistent cough', 'high fever', 'difficulty breathing', 'chest pain', 'fatigue', 'sweating'],
        'severity': 'Severe',
        'duration': '2-4 weeks'
    },
    'Allergic Rhinitis': {
        'symptoms': ['sneezing', 'runny nose', 'itchy eyes', 'nasal congestion', 'watery eyes'],
        'severity': 'Mild to Moderate',
        'duration': 'Variable'
    },
    'Strep Throat': {
        'symptoms': ['severe sore throat', 'difficulty swallowing', 'swollen lymph nodes', 'fever', 'white patches'],
        'severity': 'Moderate',
        'duration': '3-7 days'
    },
    'Sinusitis': {
        'symptoms': ['facial pain', 'nasal congestion', 'headache', 'post nasal drip', 'reduced smell'],
        'severity': 'Mild to Moderate',
        'duration': '7-14 days'
    },
    'Gastroenteritis': {
        'symptoms': ['diarrhea', 'vomiting', 'nausea', 'stomach cramps', 'low grade fever'],
        'severity': 'Mild to Moderate',
        'duration': '2-5 days'
    }
}

print(f"✅ Loaded {len(symptom_database)} diseases")

# Generate training data
print("\n🔧 Generating training data from real patterns...")

# Collect all unique symptoms
all_symptoms = []
for disease_info in symptom_database.values():
    all_symptoms.extend(disease_info['symptoms'])
unique_symptoms = sorted(list(set(all_symptoms)))
print(f"📋 Total unique symptoms: {len(unique_symptoms)}")

# Create training samples
training_data = []
target_labels = []

for disease, info in symptom_database.items():
    # Generate multiple samples for each disease
    num_samples = 200  # Samples per disease
    
    for _ in range(num_samples):
        symptoms_vector = []
        for symptom in unique_symptoms:
            if symptom in info['symptoms']:
                # Symptom typical for this disease - high probability (70-95%)
                prob = np.random.uniform(0.7, 0.95)
                symptoms_vector.append(1 if np.random.random() < prob else 0)
            else:
                # Not typical - low probability (0-15%)
                prob = np.random.uniform(0, 0.15)
                symptoms_vector.append(1 if np.random.random() < prob else 0)
        
        training_data.append(symptoms_vector)
        target_labels.append(disease)

# Convert to DataFrame
X = np.array(training_data)
y = np.array(target_labels)

print(f"✅ Generated {len(X)} training samples")
print(f"📊 Features: {X.shape[1]} symptoms")
print(f"📊 Classes: {len(np.unique(y))} diseases")

# Encode labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)
print(f"🎯 Diseases: {list(le.classes_)}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"\n📊 Training set: {len(X_train)} samples")
print(f"📊 Testing set: {len(X_test)} samples")

# Train models
print("\n🤖 Training Machine Learning Models...")

models = {
    'Random Forest': RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    ),
    'Gradient Boosting': GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )
}

best_model = None
best_score = 0
best_name = ""

for name, model in models.items():
    print(f"\n  Training {name}...")
    model.fit(X_train, y_train)
    
    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5)
    print(f"    CV Score: {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")
    
    # Test score
    test_score = model.score(X_test, y_test)
    print(f"    Test Score: {test_score*100:.2f}%")
    
    if test_score > best_score:
        best_score = test_score
        best_model = model
        best_name = name

print(f"\n✅ Best Model: {best_name} with {best_score*100:.2f}% accuracy")

# Feature importance analysis
if hasattr(best_model, 'feature_importances_'):
    feature_importance = pd.DataFrame({
        'symptom': unique_symptoms,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🎯 Top 10 Most Important Symptoms:")
    for i, row in feature_importance.head(10).iterrows():
        print(f"    {row['symptom']}: {row['importance']*100:.2f}%")

# Save model and artifacts
print("\n💾 Saving model and artifacts...")
joblib.dump(best_model, 'ml_models/medical_diagnosis_model.joblib')
joblib.dump(le, 'ml_models/label_encoder.joblib')
joblib.dump(unique_symptoms, 'ml_models/symptom_features.joblib')
joblib.dump(symptom_database, 'ml_models/disease_database.joblib')

# Save training report
report = {
    'timestamp': datetime.now().isoformat(),
    'model_type': best_name,
    'accuracy': float(best_score),
    'features_count': len(unique_symptoms),
    'diseases_count': len(le.classes_),
    'diseases': list(le.classes_),
    'cv_mean': float(cv_scores.mean()),
    'cv_std': float(cv_scores.std())
}

with open('ml_models/training_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print("✅ Model and artifacts saved to ml_models/")
print(f"📁 Model: ml_models/medical_diagnosis_model.joblib")
print(f"📁 Encoder: ml_models/label_encoder.joblib")
print(f"📁 Features: ml_models/symptom_features.joblib")
print(f"📁 Report: ml_models/training_report.json")

print("\n" + "="*60)
print("✅ Training Complete!")
print("="*60)

# Test prediction
print("\n🧪 Testing prediction with sample...")
sample_symptoms = ['fever', 'cough', 'fatigue']
print(f"Sample symptoms: {sample_symptoms}")

# Create feature vector
feature_vector = np.zeros(len(unique_symptoms))
for i, symptom in enumerate(unique_symptoms):
    if symptom in sample_symptoms:
        feature_vector[i] = 1

prediction = best_model.predict([feature_vector])[0]
probabilities = best_model.predict_proba([feature_vector])[0]
predicted_disease = le.inverse_transform([prediction])[0]
confidence = probabilities[prediction] * 100

print(f"Predicted disease: {predicted_disease}")
print(f"Confidence: {confidence:.1f}%")

# Show top 3 predictions
top_3_idx = np.argsort(probabilities)[-3:][::-1]
print("\nTop 3 predictions:")
for idx in top_3_idx:
    disease = le.inverse_transform([idx])[0]
    prob = probabilities[idx] * 100
    print(f"  - {disease}: {prob:.1f}%")
