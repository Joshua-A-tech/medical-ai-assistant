"""
ML Integration for Medical AI App
This module loads the trained model and provides prediction functions
"""

import joblib
import numpy as np
import os
import json
from typing import List, Dict

class MedicalMLModel:
    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.symptom_features = None
        self.disease_database = None
        self.is_loaded = False
        self.accuracy = 0
        self.load_model()
    
    def load_model(self):
        """Load trained ML model and artifacts"""
        try:
            # Check if model files exist
            model_path = 'ml_models/medical_diagnosis_model.joblib'
            encoder_path = 'ml_models/label_encoder.joblib'
            features_path = 'ml_models/symptom_features.joblib'
            database_path = 'ml_models/disease_database.joblib'
            
            if all(os.path.exists(p) for p in [model_path, encoder_path, features_path]):
                self.model = joblib.load(model_path)
                self.label_encoder = joblib.load(encoder_path)
                self.symptom_features = joblib.load(features_path)
                self.disease_database = joblib.load(database_path) if os.path.exists(database_path) else {}
                self.is_loaded = True
                
                # Load accuracy from training report
                try:
                    with open('ml_models/training_report.json', 'r') as f:
                        report = json.load(f)
                        self.accuracy = report.get('accuracy', 0) * 100
                except:
                    self.accuracy = 0
                
                print(f"✅ ML Model Loaded Successfully!")
                print(f"   - Accuracy: {self.accuracy:.1f}%")
                print(f"   - Diseases: {len(self.label_encoder.classes_)}")
                print(f"   - Symptoms: {len(self.symptom_features)}")
                return True
            else:
                print("⚠️ ML model files not found")
                return False
        except Exception as e:
            print(f"⚠️ Could not load ML model: {e}")
            return False
    
    def predict(self, symptoms: List[str]) -> Dict:
        """Predict disease from symptoms using trained ML model"""
        if not self.is_loaded:
            return None
        
        # Convert symptoms to lowercase for matching
        symptoms_lower = [s.lower() for s in symptoms]
        feature_symptoms_lower = [s.lower() for s in self.symptom_features]
        
        # Create feature vector
        feature_vector = np.zeros(len(self.symptom_features))
        for i, symptom in enumerate(feature_symptoms_lower):
            if symptom in symptoms_lower:
                feature_vector[i] = 1
        
        # Get prediction
        prediction = self.model.predict([feature_vector])[0]
        probabilities = self.model.predict_proba([feature_vector])[0]
        
        # Get top 3 predictions
        top_3_idx = np.argsort(probabilities)[-3:][::-1]
        
        # Get disease info from database if available
        predicted_disease = self.label_encoder.inverse_transform([prediction])[0]
        disease_info = self.disease_database.get(predicted_disease, {})
        
        return {
            'disease': predicted_disease,
            'confidence': float(probabilities[prediction] * 100),
            'severity': disease_info.get('severity', 'Unknown'),
            'duration': disease_info.get('duration', 'See doctor for accurate duration'),
            'recommendation': disease_info.get('recommendation', 'Consult healthcare provider'),
            'when_to_see_doctor': disease_info.get('when_to_see_doctor', 'If symptoms persist or worsen'),
            'prevention': disease_info.get('prevention', 'Follow healthy lifestyle'),
            'top_3': [
                {
                    'disease': self.label_encoder.inverse_transform([idx])[0],
                    'confidence': float(probabilities[idx] * 100)
                }
                for idx in top_3_idx
            ],
            'all_probabilities': {
                self.label_encoder.inverse_transform([i])[0]: float(prob * 100)
                for i, prob in enumerate(probabilities)
                if prob > 0.05  # Only show probabilities > 5%
            }
        }
    
    def predict_with_details(self, symptoms: List[str]) -> Dict:
        """Get detailed prediction with matched symptoms"""
        result = self.predict(symptoms)
        if not result:
            return None
        
        # Find matched symptoms
        matched_symptoms = []
        for symptom in symptoms:
            for fs in self.symptom_features:
                if symptom.lower() in fs.lower() or fs.lower() in symptom.lower():
                    matched_symptoms.append(symptom)
                    break
        
        result['matched_symptoms'] = list(set(matched_symptoms))
        return result
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            'loaded': self.is_loaded,
            'accuracy': self.accuracy,
            'diseases': list(self.label_encoder.classes_) if self.label_encoder else [],
            'symptoms_count': len(self.symptom_features) if self.symptom_features else 0
        }

# Create global instance
ml_model = MedicalMLModel()
