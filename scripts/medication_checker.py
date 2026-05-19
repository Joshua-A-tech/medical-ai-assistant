#!/usr/bin/env python
"""
Medication Interaction Checker using CSV database
"""

import json
from pathlib import Path

class MedicationChecker:
    def __init__(self):
        self.load_interactions()
    
    def load_interactions(self):
        json_path = Path('data/medications/interactions_lookup.json')
        if json_path.exists():
            with open(json_path, 'r') as f:
                self.interactions = json.load(f)
            print(f"✅ Loaded {len(self.interactions)} medication interactions")
            return True
        else:
            print("❌ Interactions database not found")
            self.interactions = {}
            return False
    
    def check_pair(self, drug1, drug2):
        """Check interaction between two drugs"""
        key = f"{min(drug1, drug2)},{max(drug1, drug2)}"
        if key in self.interactions:
            return self.interactions[key]
        return None
    
    def check_multiple(self, drugs):
        """Check interactions for multiple drugs"""
        results = []
        for i in range(len(drugs)):
            for j in range(i+1, len(drugs)):
                interaction = self.check_pair(drugs[i], drugs[j])
                if interaction:
                    results.append({
                        'drugs': [drugs[i], drugs[j]],
                        'severity': interaction['severity'],
                        'effect': interaction['clinical_effect'],
                        'management': interaction['management'],
                        'confidence': interaction['confidence']
                    })
        return results
    
    def get_statistics(self):
        """Get interaction statistics"""
        severity_counts = {'critical': 0, 'moderate': 0, 'low': 0}
        for _, data in self.interactions.items():
            severity_counts[data['severity']] = severity_counts.get(data['severity'], 0) + 1
        
        return {
            'total_interactions': len(self.interactions),
            'severity_breakdown': severity_counts
        }

# Create global instance
checker = MedicationChecker()

if __name__ == "__main__":
    print("="*60)
    print("💊 Medication Interaction Checker")
    print("="*60)
    
    print(f"\n📊 Statistics: {checker.get_statistics()}")
    
    print("\n🧪 Test Examples:")
    test_cases = [
        ['Warfarin', 'Aspirin'],
        ['Metformin', 'Insulin', 'Warfarin'],
        ['Simvastatin', 'Grapefruit'],
        ['Lisinopril', 'Potassium']
    ]
    
    for drugs in test_cases:
        print(f"\n  Drugs: {', '.join(drugs)}")
        interactions = checker.check_multiple(drugs)
        if interactions:
            for inter in interactions:
                print(f"    ⚠️ {inter['drugs'][0]} + {inter['drugs'][1]}")
                print(f"       Severity: {inter['severity'].upper()}")
                print(f"       Effect: {inter['effect']}")
                print(f"       Management: {inter['management']}")
        else:
            print("    ✅ No interactions found")
    
    print("\n" + "="*60)
