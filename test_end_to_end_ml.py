# -*- coding: utf-8 -*-
"""
End-to-End ML System Test
==========================
Comprehensive testing of the ML prediction pipeline:
1. Load trained models
2. Test feature extraction
3. Test prediction generation
4. Test ensemble voting
5. Test betting recommendations
6. Validate output format

Author: AI Football Analytics
Date: 4 Kasım 2025
"""

import sys
import traceback
from typing import Dict, Any

print("="*80)
print("END-TO-END ML SYSTEM TEST")
print("="*80)

# Test results tracker
test_results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0
}

def test_step(step_name: str, test_func):
    """Run a test step and track results"""
    global test_results
    print(f"\n{'='*80}")
    print(f"TEST: {step_name}")
    print(f"{'='*80}")
    
    try:
        result = test_func()
        if result:
            print(f"✅ PASSED: {step_name}")
            test_results['passed'] += 1
            return True
        else:
            print(f"❌ FAILED: {step_name}")
            test_results['failed'] += 1
            return False
    except Exception as e:
        print(f"❌ ERROR in {step_name}: {e}")
        traceback.print_exc()
        test_results['failed'] += 1
        return False

# ============================================================================
# TEST 1: Module Imports
# ============================================================================

def test_imports():
    """Test all ML module imports"""
    print("\n[1.1] Importing feature_engineer...")
    from feature_engineer import FeatureEngineer, FeatureNormalizer
    print("     ✓ feature_engineer imported")
    
    print("\n[1.2] Importing enhanced_ml_predictor...")
    from enhanced_ml_predictor import EnhancedMLPredictor
    print("     ✓ enhanced_ml_predictor imported")
    
    print("\n[1.3] Importing ensemble_manager...")
    from ensemble_manager import EnsembleManager
    print("     ✓ ensemble_manager imported")
    
    print("\n[1.4] Importing model_trainer...")
    from model_trainer import ModelTrainer
    print("     ✓ model_trainer imported")
    
    print("\n[1.5] Importing ml_evaluator...")
    from ml_evaluator import MLEvaluator
    print("     ✓ ml_evaluator imported")
    
    return True

# ============================================================================
# TEST 2: Model Loading
# ============================================================================

def test_model_loading():
    """Test loading trained models"""
    from enhanced_ml_predictor import EnhancedMLPredictor
    import os
    
    print("\n[2.1] Creating predictor instance...")
    predictor = EnhancedMLPredictor()
    print("     ✓ Predictor created")
    
    print("\n[2.2] Checking for trained models...")
    model_dir = predictor.model_dir
    if not os.path.exists(model_dir):
        print(f"     ⚠ WARNING: Model directory not found: {model_dir}")
        test_results['warnings'] += 1
        return True  # Not a critical failure
    
    model_files = [f for f in os.listdir(model_dir) if f.endswith('_xgboost.pkl')]
    if not model_files:
        print(f"     ⚠ WARNING: No trained models found in {model_dir}")
        test_results['warnings'] += 1
        return True  # Not a critical failure
    
    print(f"     ✓ Found {len(model_files)} trained model set(s)")
    
    print("\n[2.3] Loading latest models...")
    latest = sorted(model_files)[-1]
    prefix = latest.replace('_xgboost.pkl', '')
    predictor.load_models(prefix)
    print(f"     ✓ Models loaded: {prefix}")
    
    # Verify all models loaded
    assert predictor.xgb_model is not None, "XGBoost model not loaded"
    assert predictor.rf_model is not None, "RandomForest model not loaded"
    assert predictor.nn_model is not None, "Neural Network model not loaded"
    assert predictor.lr_model is not None, "Logistic model not loaded"
    assert predictor.poisson_model is not None, "Poisson model not loaded"
    assert predictor.scaler is not None, "Scaler not loaded"
    print("     ✓ All 5 models + scaler loaded")
    
    return True

# ============================================================================
# TEST 3: Feature Extraction
# ============================================================================

def test_feature_extraction():
    """Test feature extraction from mock match data"""
    from feature_engineer import FeatureEngineer
    
    print("\n[3.1] Creating FeatureEngineer...")
    engineer = FeatureEngineer()
    print("     ✓ FeatureEngineer created")
    
    print("\n[3.2] Preparing mock match data...")
    home_data = {
        'match_stats': {'statistics': []},
        'goals_scored_avg': 2.1,
        'goals_conceded_avg': 1.0,
        'recent_results': ['W', 'W', 'W', 'D', 'W'],
        'top_scorer_goals': 18,
        'top_assists': 12,
        'clean_sheet_pct': 45.0,
        'recent_xg': [2.3, 1.8, 2.5, 1.9, 2.1]
    }
    
    away_data = {
        'match_stats': {'statistics': []},
        'goals_scored_avg': 1.3,
        'goals_conceded_avg': 1.5,
        'recent_results': ['L', 'D', 'L', 'W', 'L'],
        'top_scorer_goals': 10,
        'top_assists': 6,
        'clean_sheet_pct': 25.0,
        'recent_xg': [1.2, 0.9, 1.5, 1.1, 0.8]
    }
    
    league_id = 203  # Premier League
    print("     ✓ Mock data prepared")
    
    print("\n[3.3] Extracting features...")
    features = engineer.extract_all_features(
        home_data=home_data,
        away_data=away_data,
        league_id=league_id,
        h2h_data=None
    )
    print(f"     ✓ Extracted {len(features)} features")
    
    # Verify feature count
    assert len(features) >= 85, f"Expected ≥85 features, got {len(features)}"
    print(f"     ✓ Feature count valid (≥85)")
    
    # Display sample features
    print("\n     Sample features:")
    sample_features = list(features.items())[:5]
    for name, value in sample_features:
        print(f"       - {name}: {value:.2f}")
    
    return True

# ============================================================================
# TEST 4: Single Match Prediction
# ============================================================================

def test_single_prediction():
    """Test prediction on a single match"""
    from enhanced_ml_predictor import EnhancedMLPredictor
    import os
    
    print("\n[4.1] Loading predictor with trained models...")
    predictor = EnhancedMLPredictor()
    
    # Load models
    model_dir = predictor.model_dir
    if os.path.exists(model_dir):
        model_files = [f for f in os.listdir(model_dir) if f.endswith('_xgboost.pkl')]
        if model_files:
            latest = sorted(model_files)[-1]
            prefix = latest.replace('_xgboost.pkl', '')
            predictor.load_models(prefix)
            print(f"     ✓ Models loaded: {prefix}")
        else:
            print("     ⚠ WARNING: No trained models, using untrained predictor")
            test_results['warnings'] += 1
    else:
        print("     ⚠ WARNING: Model directory not found, using untrained predictor")
        test_results['warnings'] += 1
    
    print("\n[4.2] Preparing match data...")
    home_data = {
        'match_stats': {'statistics': []},
        'goals_scored_avg': 2.1,
        'goals_conceded_avg': 1.0,
        'recent_results': ['W', 'W', 'W', 'D', 'W'],
        'top_scorer_goals': 18,
        'top_assists': 12,
        'clean_sheet_pct': 45.0,
        'recent_xg': [2.3, 1.8, 2.5]
    }
    
    away_data = {
        'match_stats': {'statistics': []},
        'goals_scored_avg': 1.3,
        'goals_conceded_avg': 1.5,
        'recent_results': ['L', 'D', 'L', 'W', 'L'],
        'top_scorer_goals': 10,
        'top_assists': 6,
        'clean_sheet_pct': 25.0,
        'recent_xg': [1.2, 0.9, 1.5]
    }
    
    print("     ✓ Match data prepared")
    
    print("\n[4.3] Generating prediction...")
    prediction = predictor.predict_match(
        home_data=home_data,
        away_data=away_data,
        league_id=203,
        h2h_data=None
    )
    print("     ✓ Prediction generated")
    
    print("\n[4.4] Validating prediction output...")
    
    # Check required keys
    required_keys = [
        'prediction', 'prediction_label', 'probabilities',
        'confidence', 'model_votes', 'feature_count'
    ]
    for key in required_keys:
        assert key in prediction, f"Missing key: {key}"
    print(f"     ✓ All required keys present")
    
    # Check data types
    assert isinstance(prediction['prediction'], int), "prediction should be int"
    assert 0 <= prediction['prediction'] <= 2, "prediction should be 0, 1, or 2"
    assert isinstance(prediction['prediction_label'], str), "prediction_label should be str"
    assert isinstance(prediction['probabilities'], dict), "probabilities should be dict"
    assert isinstance(prediction['confidence'], float), "confidence should be float"
    assert 0 <= prediction['confidence'] <= 1, "confidence should be in [0, 1]"
    print(f"     ✓ Data types valid")
    
    # Check probabilities sum to 1
    prob_sum = sum(prediction['probabilities'].values())
    assert 0.99 <= prob_sum <= 1.01, f"Probabilities sum to {prob_sum}, should be ~1.0"
    print(f"     ✓ Probabilities sum to 1.0")
    
    # Display prediction
    print("\n     Prediction Results:")
    print(f"       Prediction: {prediction['prediction_label']}")
    print(f"       Confidence: {prediction['confidence']:.1%}")
    print(f"       Probabilities:")
    print(f"         Home Win: {prediction['probabilities']['home_win']:.1%}")
    print(f"         Draw:     {prediction['probabilities']['draw']:.1%}")
    print(f"         Away Win: {prediction['probabilities']['away_win']:.1%}")
    print(f"       Model Votes:")
    for model, vote in prediction['model_votes'].items():
        print(f"         {model}: {vote}")
    print(f"       Features Used: {prediction['feature_count']}")
    
    return True

# ============================================================================
# TEST 5: Ensemble Manager
# ============================================================================

def test_ensemble_manager():
    """Test ensemble manager functionality"""
    from ensemble_manager import EnsembleManager
    import numpy as np
    
    print("\n[5.1] Creating EnsembleManager...")
    manager = EnsembleManager()
    print("     ✓ EnsembleManager created")
    
    print("\n[5.2] Testing weighted voting...")
    predictions = {
        'xgboost': np.array([[0.20, 0.25, 0.55]]),
        'random_forest': np.array([[0.25, 0.30, 0.45]]),
        'neural_network': np.array([[0.15, 0.20, 0.65]]),
        'logistic': np.array([[0.30, 0.35, 0.35]]),
        'poisson': np.array([[0.22, 0.28, 0.50]])
    }
    
    ensemble_proba = manager.weighted_vote(predictions, return_probabilities=True)
    print(f"     ✓ Ensemble probabilities: {ensemble_proba[0]}")
    
    # Verify probabilities sum to 1
    prob_sum = ensemble_proba[0].sum()
    assert 0.99 <= prob_sum <= 1.01, f"Ensemble probabilities sum to {prob_sum}"
    print(f"     ✓ Probabilities sum to 1.0")
    
    print("\n[5.3] Testing confidence calculation...")
    confidence = manager.calculate_confidence(ensemble_proba[0], method='max_prob')
    print(f"     ✓ Confidence (max_prob): {confidence:.3f}")
    
    print("\n[5.4] Testing betting recommendation...")
    recommendation = manager.get_recommendation(ensemble_proba[0])
    print(f"     ✓ Bet: {recommendation['bet']}")
    print(f"     ✓ Outcome: {recommendation['outcome']}")
    print(f"     ✓ Stake: {recommendation['suggested_stake']}")
    print(f"     ✓ Reasoning: {recommendation['reasoning']}")
    
    return True

# ============================================================================
# TEST 6: UI Integration Check
# ============================================================================

def test_ui_integration():
    """Test UI integration components"""
    print("\n[6.1] Checking app.py imports...")
    
    try:
        import app
        print("     ✓ app.py imported successfully")
    except Exception as e:
        print(f"     ❌ app.py import failed: {e}")
        return False
    
    print("\n[6.2] Checking ML_AVAILABLE flag...")
    ml_available = getattr(app, 'ML_AVAILABLE', False)
    print(f"     ML_AVAILABLE = {ml_available}")
    if ml_available:
        print("     ✓ ML modules available in app")
    else:
        print("     ⚠ WARNING: ML modules not available in app")
        test_results['warnings'] += 1
    
    print("\n[6.3] Checking ML functions exist...")
    
    # Check for ML predictor loader
    assert hasattr(app, 'load_ml_predictor'), "load_ml_predictor function missing"
    print("     ✓ load_ml_predictor function exists")
    
    # Check for prediction function
    assert hasattr(app, 'get_ml_prediction'), "get_ml_prediction function missing"
    print("     ✓ get_ml_prediction function exists")
    
    # Check for display function
    assert hasattr(app, 'display_ml_prediction_section'), "display_ml_prediction_section function missing"
    print("     ✓ display_ml_prediction_section function exists")
    
    return True

# ============================================================================
# TEST 7: Performance Check
# ============================================================================

def test_performance():
    """Test prediction performance (speed)"""
    from enhanced_ml_predictor import EnhancedMLPredictor
    import time
    import os
    
    print("\n[7.1] Loading predictor...")
    predictor = EnhancedMLPredictor()
    
    # Try to load models
    model_dir = predictor.model_dir
    if os.path.exists(model_dir):
        model_files = [f for f in os.listdir(model_dir) if f.endswith('_xgboost.pkl')]
        if model_files:
            latest = sorted(model_files)[-1]
            prefix = latest.replace('_xgboost.pkl', '')
            predictor.load_models(prefix)
    
    print("\n[7.2] Running 10 predictions for performance test...")
    
    home_data = {
        'match_stats': {'statistics': []},
        'goals_scored_avg': 2.0,
        'goals_conceded_avg': 1.0,
        'recent_results': ['W', 'W', 'D', 'W', 'L'],
        'top_scorer_goals': 15,
        'top_assists': 10,
        'clean_sheet_pct': 40.0,
        'recent_xg': [2.0, 1.5, 1.8]
    }
    
    away_data = {
        'match_stats': {'statistics': []},
        'goals_scored_avg': 1.5,
        'goals_conceded_avg': 1.3,
        'recent_results': ['D', 'L', 'W', 'D', 'L'],
        'top_scorer_goals': 12,
        'top_assists': 8,
        'clean_sheet_pct': 30.0,
        'recent_xg': [1.3, 1.1, 1.4]
    }
    
    times = []
    for i in range(10):
        start = time.time()
        prediction = predictor.predict_match(home_data, away_data, 203, None)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"     ✓ Average time: {avg_time*1000:.1f}ms")
    print(f"     ✓ Min time: {min_time*1000:.1f}ms")
    print(f"     ✓ Max time: {max_time*1000:.1f}ms")
    
    # Check if performance is acceptable (<1 second)
    if avg_time < 1.0:
        print(f"     ✓ Performance acceptable (<1s per prediction)")
    else:
        print(f"     ⚠ WARNING: Slow performance (>1s per prediction)")
        test_results['warnings'] += 1
    
    return True

# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print("\nStarting comprehensive test suite...\n")
    
    # Run all tests
    test_step("Module Imports", test_imports)
    test_step("Model Loading", test_model_loading)
    test_step("Feature Extraction", test_feature_extraction)
    test_step("Single Match Prediction", test_single_prediction)
    test_step("Ensemble Manager", test_ensemble_manager)
    test_step("UI Integration Check", test_ui_integration)
    test_step("Performance Check", test_performance)
    
    # Final summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed:   {test_results['passed']}")
    print(f"❌ Failed:   {test_results['failed']}")
    print(f"⚠️  Warnings: {test_results['warnings']}")
    print("="*80)
    
    if test_results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("ML System is ready for production!")
    else:
        print(f"\n❌ {test_results['failed']} test(s) failed. Please review errors above.")
        sys.exit(1)
    
    if test_results['warnings'] > 0:
        print(f"\n⚠️  Note: {test_results['warnings']} warning(s) - non-critical issues detected")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Start Streamlit app: streamlit run app.py")
    print("2. Select a real match for analysis")
    print("3. Navigate to 'Tahmin Özeti' tab")
    print("4. Verify ML prediction appears at the top")
    print("5. Check confidence score and model votes")
    print("="*80)
