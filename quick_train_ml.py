# -*- coding: utf-8 -*-
"""
Quick ML Model Training
=======================
Train a simple ML model for testing the UI integration
"""

import numpy as np
from enhanced_ml_predictor import EnhancedMLPredictor
from sklearn.model_selection import train_test_split

print("="*80)
print("QUICK ML MODEL TRAINING FOR UI TEST")
print("="*80)

# Create predictor
predictor = EnhancedMLPredictor()

# Generate synthetic data (more samples for better training)
print("\nGenerating training data...")
np.random.seed(42)
n_samples = 1000
n_features = 86

# Random features
X = np.random.randn(n_samples, n_features)

# More realistic labels (Home advantage)
# Home: 45%, Draw: 28%, Away: 27%
y = np.random.choice([0, 1, 2], size=n_samples, p=[0.27, 0.28, 0.45])

# Split
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training samples: {len(X_train)}")
print(f"Validation samples: {len(X_val)}")

# Train
print("\nTraining models...")
results = predictor.train_all_models(X_train, y_train, X_val, y_val)

# Save models
print("\nSaving models...")
predictor.save_models(suffix="ui_test")

print("\n" + "="*80)
print("✅ MODELS TRAINED AND SAVED!")
print("="*80)
print("\nModel files saved in: models/")
print("You can now test the UI integration with these trained models.")
print("\nTo test: Run streamlit app and select a match for analysis")
print("="*80)
