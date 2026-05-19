#!/usr/bin/env python
"""
Load and query medication interactions from CSV
"""

import pandas as pd
import json
from pathlib import Path

# Load CSV
csv_path = Path('data/medications/drug_interactions.csv')
if csv_path.exists():
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} medication interactions")
    print(f"📊 Columns: {list(df.columns)}")
    print(f"\n📈 Severity breakdown:")
    print(df['severity'].value_counts())

    # Create a quick lookup dictionary with string keys
    interactions_lookup = {}
    for _, row in df.iterrows():
        # Convert tuple to string key (e.g., "Warfarin,Aspirin")
        key = f"{min(row['drug_name_1'], row['drug_name_2'])},{max(row['drug_name_1'], row['drug_name_2'])}"
        interactions_lookup[key] = {
            'severity': row['severity'],
            'interaction_type': row['interaction_type'],
            'clinical_effect': row['clinical_effect'],
            'mechanism': row['mechanism'],
            'management': row['management'],
            'confidence': row['confidence_score']
        }

    # Save as JSON for fast lookup
    with open('data/medications/interactions_lookup.json', 'w') as f:
        json.dump(interactions_lookup, f, indent=2)

    print(f"\n✅ Saved {len(interactions_lookup)} interactions to JSON")

    # Test some lookups
    print("\n🧪 Testing lookups:")
    test_pairs = [
        ('Warfarin', 'Aspirin'),
        ('Metformin', 'Insulin'),
        ('Simvastatin', 'Grapefruit')
    ]

    for d1, d2 in test_pairs:
        key = f"{min(d1, d2)},{max(d1, d2)}"
        if key in interactions_lookup:
            info = interactions_lookup[key]
            print(f"\n  {d1} + {d2}:")
            print(f"    Severity: {info['severity']}")
            print(f"    Effect: {info['clinical_effect']}")
            print(f"    Management: {info['management']}")
        else:
            print(f"\n  {d1} + {d2}: Not found")
else:
    print("❌ CSV file not found!")
