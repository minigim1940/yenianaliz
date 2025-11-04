# -*- coding: utf-8 -*-
"""
Train with Match Data + Synthetic Augmentation
===============================================
Combines real match data with synthetic data for robust training.

Author: AI Football Analytics  
Date: 4 Kasım 2025
"""

import os
import json
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Import ML modules
from feature_engineer import FeatureEngineer
from enhanced_ml_predictor import EnhancedMLPredictor

print("="*80)
print("HYBRID TRAINING: REAL DATA + SYNTHETIC AUGMENTATION")
print("="*80)

# ============================================================================
# Load Real Match Data
# ============================================================================

print(f"\n{'='*80}")
print("STEP 1: LOADING REAL MATCH DATA")
print(f"{'='*80}")

data_file = "match_learning_data.json"

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

matches = data.get('matches', [])
print(f"\n✓ Loaded {len(matches)} real historical matches")

# ============================================================================
# Extract Features from Real Data
# ============================================================================

print(f"\n{'='*80}")
print("STEP 2: EXTRACTING FEATURES FROM REAL DATA")
print(f"{'='*80}")

engineer = FeatureEngineer()

X_real = []
y_real = []

print(f"\nProcessing {len(matches)} real matches...")

for i, match in enumerate(matches):
    try:
        result = match.get('actual_result', {})
        winner = result.get('winner', 'draw')
        
        if winner == 'home':
            label = 0
        elif winner == 'away':
            label = 2
        else:
            label = 1
        
        factors = match.get('model_factors', {})
        prediction = match.get('prediction', {})
        
        home_data = {
            'match_stats': {'statistics': []},
            'goals_scored_avg': float(result.get('home_score', 1.5)),
            'goals_conceded_avg': float(result.get('away_score', 1.0)),
            'recent_results': ['W', 'W', 'D'] if factors.get('form_factor_a', 1.0) > 1.0 else ['L', 'D', 'L'],
            'top_scorer_goals': 12,
            'top_assists': 6,
            'clean_sheet_pct': 40.0 if prediction.get('win_a', 33) > 40 else 25.0,
            'recent_xg': [1.8, 1.5, 1.6]
        }
        
        away_data = {
            'match_stats': {'statistics': []},
            'goals_scored_avg': float(result.get('away_score', 1.3)),
            'goals_conceded_avg': float(result.get('home_score', 1.0)),
            'recent_results': ['W', 'D', 'W'] if factors.get('form_factor_b', 1.0) > 1.0 else ['L', 'L', 'D'],
            'top_scorer_goals': 10,
            'top_assists': 5,
            'clean_sheet_pct': 35.0 if prediction.get('win_b', 33) > 30 else 20.0,
            'recent_xg': [1.4, 1.2, 1.3]
        }
        
        features = engineer.extract_all_features(
            home_data=home_data,
            away_data=away_data,
            league_id=match.get('league_id', 39),
            h2h_data=None
        )
        
        feature_array = np.array(list(features.values()))
        
        # Add ELO and form factors
        feature_array = np.append(feature_array, [
            factors.get('elo_diff', 0) / 100.0,
            factors.get('form_factor_a', 1.0),
            factors.get('form_factor_b', 1.0),
            factors.get('home_advantage', 1.08)
        ])
        
        X_real.append(feature_array)
        y_real.append(label)
        
    except Exception as e:
        print(f"  ⚠ Error processing match {i}: {e}")
        continue

X_real = np.array(X_real)
y_real = np.array(y_real)

print(f"\n✓ Extracted features from {len(X_real)} real matches")
print(f"  Features: {X_real.shape[1]}")

# ============================================================================
# Generate Synthetic Data for Augmentation
# ============================================================================

print(f"\n{'='*80}")
print("STEP 3: GENERATING SYNTHETIC DATA FOR AUGMENTATION")
print(f"{'='*80}")

# Generate realistic synthetic data based on real data patterns
n_synthetic = 500  # Generate 500 synthetic matches

print(f"\nGenerating {n_synthetic} synthetic matches...")
print("  Using realistic distributions based on football statistics")

# Realistic outcome distribution (based on football data)
# Home wins: ~46%, Draws: ~27%, Away wins: ~27%
y_synthetic = np.random.choice([0, 1, 2], size=n_synthetic, p=[0.46, 0.27, 0.27])

# Generate synthetic features with realistic distributions
X_synthetic = []

for outcome in y_synthetic:
    # Base features around real data means and add noise
    if len(X_real) > 0:
        base = X_real.mean(axis=0)
        noise = np.random.randn(X_real.shape[1]) * X_real.std(axis=0) * 0.5
    else:
        base = np.zeros(90)
        noise = np.random.randn(90)
    
    synthetic_features = base + noise
    
    # Adjust based on outcome to create realistic patterns
    if outcome == 0:  # Home win
        synthetic_features[0:10] *= 1.2  # Boost home features
        synthetic_features[43:53] *= 0.9  # Reduce away features
    elif outcome == 2:  # Away win
        synthetic_features[0:10] *= 0.9
        synthetic_features[43:53] *= 1.2
    else:  # Draw
        synthetic_features[0:10] *= 1.0
        synthetic_features[43:53] *= 1.0
    
    X_synthetic.append(synthetic_features)

X_synthetic = np.array(X_synthetic)

print(f"✓ Generated {len(X_synthetic)} synthetic samples")

# ============================================================================
# Combine Real + Synthetic Data
# ============================================================================

print(f"\n{'='*80}")
print("STEP 4: COMBINING DATASETS")
print(f"{'='*80}")

# Combine datasets
X_combined = np.vstack([X_real, X_synthetic])
y_combined = np.hstack([y_real, y_synthetic])

print(f"\n✓ Combined dataset:")
print(f"  Real matches:      {len(X_real)}")
print(f"  Synthetic matches: {len(X_synthetic)}")
print(f"  Total samples:     {len(X_combined)}")
print(f"  Features:          {X_combined.shape[1]}")

print(f"\nClass distribution:")
print(f"  Home Wins: {list(y_combined).count(0)} ({list(y_combined).count(0)/len(y_combined)*100:.1f}%)")
print(f"  Draws:     {list(y_combined).count(1)} ({list(y_combined).count(1)/len(y_combined)*100:.1f}%)")
print(f"  Away Wins: {list(y_combined).count(2)} ({list(y_combined).count(2)/len(y_combined)*100:.1f}%)")

# Save combined data
data_dir = "training_data"
os.makedirs(data_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
np.save(os.path.join(data_dir, f"X_hybrid_{timestamp}.npy"), X_combined)
np.save(os.path.join(data_dir, f"y_hybrid_{timestamp}.npy"), y_combined)

# ============================================================================
# Train Models
# ============================================================================

print(f"\n{'='*80}")
print("STEP 5: TRAINING MODELS")
print(f"{'='*80}")

# Split data
X_train, X_val, y_train, y_val = train_test_split(
    X_combined, y_combined, test_size=0.2, random_state=42, stratify=y_combined
)

print(f"\nData split:")
print(f"  Training:   {X_train.shape[0]} samples")
print(f"  Validation: {X_val.shape[0]} samples")

# Create and train predictor
predictor = EnhancedMLPredictor()

print(f"\n[Training] All 5 models...")
print(f"  XGBoost, RandomForest, Neural Network, Logistic, Poisson")
print(f"  This will take 2-3 minutes...")

predictor.train_all_models(X_train, y_train, X_val, y_val)

print(f"\n✓ Training complete!")

# Save models
print(f"\n[Saving] Production models...")
predictor.save_models(suffix="hybrid")

print(f"  ✓ Models saved with suffix: hybrid")

# ============================================================================
# Evaluation
# ============================================================================

print(f"\n{'='*80}")
print("STEP 6: EVALUATION")
print(f"{'='*80}")

# Predictions using ensemble
from ensemble_manager import EnsembleManager

ensemble = EnsembleManager()
predictions = []
confidences = []

print(f"\n[Predicting] On {len(X_val)} validation samples...")

for i in range(len(X_val)):
    model_predictions = {
        'xgboost': predictor.xgb_model.predict_proba([X_val[i]]),
        'random_forest': predictor.rf_model.predict_proba([X_val[i]]),
        'neural_network': predictor.nn_model.predict_proba([X_val[i]]),
        'logistic': predictor.lr_model.predict_proba([X_val[i]]),
        'poisson': predictor.poisson_model.predict_proba([X_val[i]])
    }
    
    # Get class prediction
    pred_class = ensemble.weighted_vote(model_predictions)
    predictions.append(pred_class[0])
    
    # Get probabilities for confidence
    proba = ensemble.weighted_vote(model_predictions, return_probabilities=True)
    confidence = ensemble.calculate_confidence(proba[0])
    confidences.append(confidence)

predictions = np.array(predictions)
accuracy = accuracy_score(y_val, predictions)
avg_confidence = np.mean(confidences)

print(f"\n✓ Validation Results:")
print(f"  Accuracy: {accuracy:.1%}")
print(f"  Average Confidence: {avg_confidence:.1%}")

print(f"\nClassification Report:")
print(classification_report(
    y_val, 
    predictions, 
    target_names=['Home Win', 'Draw', 'Away Win'],
    digits=3
))

# ============================================================================
# Final Summary
# ============================================================================

print(f"\n{'='*80}")
print("✅ TRAINING COMPLETE!")
print(f"{'='*80}")

print(f"\n📊 Training Summary:")
print(f"  Real matches used: {len(X_real)}")
print(f"  Synthetic matches: {len(X_synthetic)}")
print(f"  Total training samples: {len(X_combined)}")
print(f"  Features: {X_combined.shape[1]} (86 base + 4 extra)")
print(f"  Models: 5 (XGBoost, RF, NN, LR, Poisson)")
print(f"  Validation accuracy: {accuracy:.1%}")
print(f"  Average confidence: {avg_confidence:.1%}")

if accuracy >= 0.45:
    status = "✅ EXCELLENT"
elif accuracy >= 0.40:
    status = "✅ GOOD"
elif accuracy >= 0.35:
    status = "⚠️  ACCEPTABLE"
else:
    status = "⚠️  LOW"

print(f"\n{status} - Accuracy: {accuracy:.1%}")

print(f"\n📁 Models Saved:")
print(f"  Location: models/")
print(f"  Pattern: *_hybrid.*")
print(f"  Count: 6 files (5 models + scaler)")

print(f"\n🚀 Next Steps:")
print(f"  1. ✅ Production models ready!")
print(f"  2. Start app: streamlit run app.py")
print(f"  3. Select any match to analyze")
print(f"  4. See ML prediction in 'Tahmin Özeti' tab")
print(f"  5. Models will auto-load latest version")

print(f"\n{'='*80}")
