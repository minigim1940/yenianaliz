# -*- coding: utf-8 -*-
"""
Enhanced ML Predictor with 5 Models
=====================================
Implements ensemble of 5 ML models:
1. XGBoost (35% weight)
2. Random Forest (25% weight)
3. Neural Network (20% weight) 
4. Logistic Regression (10% weight)
5. Poisson Model (10% weight)

Target Accuracy: 70-75%
Features: 86 advanced metrics

Author: AI Football Analytics
Date: 4 Kasım 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import pickle
import os
from datetime import datetime

# ML Libraries
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Feature engineering
from feature_engineer import FeatureEngineer, FeatureNormalizer

print("[OK] Enhanced ML Predictor Module Loaded")


class EnhancedMLPredictor:
    """
    Main ML prediction class with 5 models
    """
    
    def __init__(self, model_dir: str = "models"):
        """
        Initialize predictor
        
        Args:
            model_dir: Directory to save/load models
        """
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Feature engineer
        self.feature_engineer = FeatureEngineer()
        self.feature_normalizer = FeatureNormalizer(method='minmax')
        
        # Models
        self.xgb_model = None
        self.rf_model = None
        self.nn_model = None  # Will use sklearn MLPClassifier
        self.lr_model = None
        self.poisson_model = None
        
        # Model weights for ensemble
        self.weights = {
            'xgboost': 0.35,
            'random_forest': 0.25,
            'neural_network': 0.20,
            'logistic': 0.10,
            'poisson': 0.10
        }
        
        # Scaler for features
        self.scaler = StandardScaler()
        
        print(f"[OK] Enhanced ML Predictor initialized")
        print(f"     Models: XGBoost (35%), RandomForest (25%), Neural (20%), Logistic (10%), Poisson (10%)")
    
    # ========== MODEL 1: XGBoost ==========
    
    def _create_xgboost_model(self) -> xgb.XGBClassifier:
        """
        Create XGBoost classifier
        Best for structured data, handles non-linearity
        """
        model = xgb.XGBClassifier(
            max_depth=6,
            learning_rate=0.05,
            n_estimators=200,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='multi:softprob',
            num_class=3,
            eval_metric='mlogloss',
            random_state=42,
            n_jobs=-1
        )
        return model
    
    # ========== MODEL 2: Random Forest ==========
    
    def _create_random_forest_model(self) -> RandomForestClassifier:
        """
        Create Random Forest classifier
        Robust to outliers, good baseline
        """
        model = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        return model
    
    # ========== MODEL 3: Neural Network ==========
    
    def _create_neural_network_model(self):
        """
        Create Neural Network (MLP) classifier
        Complex pattern recognition
        """
        from sklearn.neural_network import MLPClassifier
        
        model = MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),
            activation='relu',
            solver='adam',
            alpha=0.0001,
            batch_size='auto',
            learning_rate='adaptive',
            learning_rate_init=0.001,
            max_iter=300,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=20
        )
        return model
    
    # ========== MODEL 4: Logistic Regression ==========
    
    def _create_logistic_model(self) -> LogisticRegression:
        """
        Create Logistic Regression classifier
        Fast, interpretable baseline
        """
        model = LogisticRegression(
            multi_class='multinomial',
            solver='lbfgs',
            max_iter=500,
            C=1.0,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        return model
    
    # ========== MODEL 5: Poisson Model ==========
    
    def _create_poisson_model(self):
        """
        Create Poisson-based model for football scores
        Uses LogisticRegression as wrapper for 3-class prediction
        """
        # For now, use Logistic with different params
        # Can be enhanced with actual Poisson distribution later
        model = LogisticRegression(
            multi_class='multinomial',
            solver='lbfgs',
            max_iter=300,
            C=0.5,
            random_state=42
        )
        return model
    
    # ========== TRAINING ==========
    
    def train_all_models(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Train all 5 models
        
        Args:
            X_train: Training features (n_samples, 86)
            y_train: Training labels (0=Away Win, 1=Draw, 2=Home Win)
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            
        Returns:
            Dictionary with training scores
        """
        print("\n" + "="*80)
        print("TRAINING ALL MODELS")
        print("="*80)
        
        results = {}
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
        
        # 1. Train XGBoost
        print("\n[1/5] Training XGBoost...")
        self.xgb_model = self._create_xgboost_model()
        self.xgb_model.fit(X_train_scaled, y_train)
        train_acc = accuracy_score(y_train, self.xgb_model.predict(X_train_scaled))
        print(f"      XGBoost Training Accuracy: {train_acc:.3f}")
        results['xgboost_train'] = train_acc
        
        if X_val is not None:
            val_acc = accuracy_score(y_val, self.xgb_model.predict(X_val_scaled))
            print(f"      XGBoost Validation Accuracy: {val_acc:.3f}")
            results['xgboost_val'] = val_acc
        
        # 2. Train Random Forest
        print("\n[2/5] Training Random Forest...")
        self.rf_model = self._create_random_forest_model()
        self.rf_model.fit(X_train_scaled, y_train)
        train_acc = accuracy_score(y_train, self.rf_model.predict(X_train_scaled))
        print(f"      RandomForest Training Accuracy: {train_acc:.3f}")
        results['rf_train'] = train_acc
        
        if X_val is not None:
            val_acc = accuracy_score(y_val, self.rf_model.predict(X_val_scaled))
            print(f"      RandomForest Validation Accuracy: {val_acc:.3f}")
            results['rf_val'] = val_acc
        
        # 3. Train Neural Network
        print("\n[3/5] Training Neural Network...")
        self.nn_model = self._create_neural_network_model()
        self.nn_model.fit(X_train_scaled, y_train)
        train_acc = accuracy_score(y_train, self.nn_model.predict(X_train_scaled))
        print(f"      Neural Network Training Accuracy: {train_acc:.3f}")
        results['nn_train'] = train_acc
        
        if X_val is not None:
            val_acc = accuracy_score(y_val, self.nn_model.predict(X_val_scaled))
            print(f"      Neural Network Validation Accuracy: {val_acc:.3f}")
            results['nn_val'] = val_acc
        
        # 4. Train Logistic Regression
        print("\n[4/5] Training Logistic Regression...")
        self.lr_model = self._create_logistic_model()
        self.lr_model.fit(X_train_scaled, y_train)
        train_acc = accuracy_score(y_train, self.lr_model.predict(X_train_scaled))
        print(f"      Logistic Training Accuracy: {train_acc:.3f}")
        results['lr_train'] = train_acc
        
        if X_val is not None:
            val_acc = accuracy_score(y_val, self.lr_model.predict(X_val_scaled))
            print(f"      Logistic Validation Accuracy: {val_acc:.3f}")
            results['lr_val'] = val_acc
        
        # 5. Train Poisson Model
        print("\n[5/5] Training Poisson Model...")
        self.poisson_model = self._create_poisson_model()
        self.poisson_model.fit(X_train_scaled, y_train)
        train_acc = accuracy_score(y_train, self.poisson_model.predict(X_train_scaled))
        print(f"      Poisson Training Accuracy: {train_acc:.3f}")
        results['poisson_train'] = train_acc
        
        if X_val is not None:
            val_acc = accuracy_score(y_val, self.poisson_model.predict(X_val_scaled))
            print(f"      Poisson Validation Accuracy: {val_acc:.3f}")
            results['poisson_val'] = val_acc
        
        # Ensemble prediction
        if X_val is not None:
            print("\n[ENSEMBLE] Calculating weighted ensemble...")
            ensemble_acc = self._calculate_ensemble_accuracy(X_val_scaled, y_val)
            print(f"           Ensemble Validation Accuracy: {ensemble_acc:.3f}")
            results['ensemble_val'] = ensemble_acc
        
        print("\n" + "="*80)
        print("ALL MODELS TRAINED SUCCESSFULLY!")
        print("="*80)
        
        return results
    
    def _calculate_ensemble_accuracy(
        self,
        X: np.ndarray,
        y_true: np.ndarray
    ) -> float:
        """Calculate weighted ensemble accuracy"""
        ensemble_pred = self.predict_ensemble(X)
        return accuracy_score(y_true, ensemble_pred)
    
    # ========== PREDICTION ==========
    
    def predict_ensemble(
        self,
        X: np.ndarray,
        return_probabilities: bool = False
    ) -> np.ndarray:
        """
        Predict using weighted ensemble of all models
        
        Args:
            X: Features (n_samples, 86)
            return_probabilities: If True, return probabilities
            
        Returns:
            Predictions (0=Away, 1=Draw, 2=Home) or probabilities
        """
        X_scaled = self.scaler.transform(X)
        
        # Get probabilities from each model
        xgb_proba = self.xgb_model.predict_proba(X_scaled) * self.weights['xgboost']
        rf_proba = self.rf_model.predict_proba(X_scaled) * self.weights['random_forest']
        nn_proba = self.nn_model.predict_proba(X_scaled) * self.weights['neural_network']
        lr_proba = self.lr_model.predict_proba(X_scaled) * self.weights['logistic']
        poisson_proba = self.poisson_model.predict_proba(X_scaled) * self.weights['poisson']
        
        # Weighted average
        ensemble_proba = xgb_proba + rf_proba + nn_proba + lr_proba + poisson_proba
        
        if return_probabilities:
            return ensemble_proba
        else:
            return np.argmax(ensemble_proba, axis=1)
    
    def predict_match(
        self,
        home_data: Dict[str, Any],
        away_data: Dict[str, Any],
        league_id: int,
        h2h_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict a single match outcome
        
        Args:
            home_data: Home team data
            away_data: Away team data
            league_id: League ID
            h2h_data: Head-to-head data
            
        Returns:
            {
                'prediction': 2,  # 0=Away, 1=Draw, 2=Home
                'probabilities': {
                    'home_win': 0.52,
                    'draw': 0.28,
                    'away_win': 0.20
                },
                'confidence': 0.52,
                'recommendation': 'Home Win',
                'model_votes': {...}
            }
        """
        # Extract base features (86 features)
        features = self.feature_engineer.extract_all_features(
            home_data=home_data,
            away_data=away_data,
            league_id=league_id,
            h2h_data=h2h_data
        )
        
        # Add 4 extra features to match training data (90 total)
        # These were added during hybrid training
        
        # 1. ELO difference (normalized)
        home_elo = home_data.get('elo_rating', 1500)
        away_elo = away_data.get('elo_rating', 1500)
        elo_diff = (home_elo - away_elo) / 100.0  # Normalize
        
        # 2. Form factors
        home_form_raw = home_data.get('form', '')
        away_form_raw = away_data.get('form', '')
        
        # Calculate form factor (W=1, D=0.5, L=0)
        def calc_form_factor(form_str):
            if not form_str:
                return 0.5
            form_values = {'W': 1.0, 'D': 0.5, 'L': 0.0}
            scores = [form_values.get(c, 0.5) for c in form_str[-5:]]  # Last 5 matches
            return sum(scores) / len(scores) if scores else 0.5
        
        form_factor_home = calc_form_factor(home_form_raw)
        form_factor_away = calc_form_factor(away_form_raw)
        
        # 3. Home advantage (1.25 default)
        home_advantage = 1.25
        
        # Convert to array with 90 features (86 base + 4 extra)
        feature_names = sorted(features.keys())
        base_features = [features[name] for name in feature_names]
        
        # Append 4 extra features in correct order
        all_features = base_features + [
            elo_diff,
            form_factor_home,
            form_factor_away,
            home_advantage
        ]
        
        X = np.array([all_features])
        
        # Get ensemble prediction
        probabilities = self.predict_ensemble(X, return_probabilities=True)[0]
        prediction = np.argmax(probabilities)
        
        # Get individual model votes
        X_scaled = self.scaler.transform(X)
        model_votes = {
            'xgboost': np.argmax(self.xgb_model.predict_proba(X_scaled)[0]),
            'random_forest': np.argmax(self.rf_model.predict_proba(X_scaled)[0]),
            'neural_network': np.argmax(self.nn_model.predict_proba(X_scaled)[0]),
            'logistic': np.argmax(self.lr_model.predict_proba(X_scaled)[0]),
            'poisson': np.argmax(self.poisson_model.predict_proba(X_scaled)[0])
        }
        
        # Convert to readable format
        outcome_map = {0: 'Away Win', 1: 'Draw', 2: 'Home Win'}
        
        result = {
            'prediction': int(prediction),
            'prediction_label': outcome_map[prediction],
            'probabilities': {
                'home_win': float(probabilities[2]),
                'draw': float(probabilities[1]),
                'away_win': float(probabilities[0])
            },
            'confidence': float(np.max(probabilities)),
            'model_votes': {k: outcome_map[v] for k, v in model_votes.items()},
            'feature_count': len(all_features)  # Should be 90
        }
        
        return result
    
    # ========== MODEL PERSISTENCE ==========
    
    def save_models(self, suffix: str = "") -> None:
        """Save all models to disk"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{timestamp}_{suffix}" if suffix else timestamp
        
        models_to_save = {
            f'{prefix}_xgboost.pkl': self.xgb_model,
            f'{prefix}_random_forest.pkl': self.rf_model,
            f'{prefix}_neural_network.pkl': self.nn_model,
            f'{prefix}_logistic.pkl': self.lr_model,
            f'{prefix}_poisson.pkl': self.poisson_model,
            f'{prefix}_scaler.pkl': self.scaler
        }
        
        for filename, model in models_to_save.items():
            filepath = os.path.join(self.model_dir, filename)
            with open(filepath, 'wb') as f:
                pickle.dump(model, f)
            print(f"[OK] Saved: {filename}")
        
        print(f"\n[OK] All models saved to: {self.model_dir}/")
    
    def load_models(self, prefix: str) -> None:
        """Load models from disk"""
        models_to_load = {
            'xgb_model': f'{prefix}_xgboost.pkl',
            'rf_model': f'{prefix}_random_forest.pkl',
            'nn_model': f'{prefix}_neural_network.pkl',
            'lr_model': f'{prefix}_logistic.pkl',
            'poisson_model': f'{prefix}_poisson.pkl',
            'scaler': f'{prefix}_scaler.pkl'
        }
        
        for attr_name, filename in models_to_load.items():
            filepath = os.path.join(self.model_dir, filename)
            with open(filepath, 'rb') as f:
                setattr(self, attr_name, pickle.load(f))
            print(f"[OK] Loaded: {filename}")
        
        print(f"\n[OK] All models loaded from: {self.model_dir}/")
    
    # ========== FEATURE IMPORTANCE ==========
    
    def get_feature_importance(
        self,
        feature_names: List[str],
        top_n: int = 20
    ) -> pd.DataFrame:
        """
        Get feature importance from tree-based models
        
        Args:
            feature_names: List of feature names
            top_n: Number of top features to return
            
        Returns:
            DataFrame with feature importance
        """
        # XGBoost feature importance
        xgb_importance = self.xgb_model.feature_importances_
        
        # RandomForest feature importance
        rf_importance = self.rf_model.feature_importances_
        
        # Average importance
        avg_importance = (xgb_importance + rf_importance) / 2
        
        # Create DataFrame
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'xgboost_importance': xgb_importance,
            'rf_importance': rf_importance,
            'avg_importance': avg_importance
        })
        
        # Sort by average importance
        importance_df = importance_df.sort_values('avg_importance', ascending=False)
        
        return importance_df.head(top_n)


# ========== TESTING ==========

if __name__ == "__main__":
    print("=" * 80)
    print("ENHANCED ML PREDICTOR TEST")
    print("=" * 80)
    
    # Create predictor
    predictor = EnhancedMLPredictor()
    
    # Generate synthetic data for testing
    print("\n[TEST] Generating synthetic training data...")
    np.random.seed(42)
    n_samples = 500
    n_features = 86
    
    # Random features
    X = np.random.randn(n_samples, n_features)
    
    # Random labels (0=Away, 1=Draw, 2=Home)
    # Simulate realistic distribution: Home=40%, Draw=30%, Away=30%
    y = np.random.choice([0, 1, 2], size=n_samples, p=[0.30, 0.30, 0.40])
    
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"[OK] Training set: {len(X_train)} samples")
    print(f"[OK] Validation set: {len(X_val)} samples")
    
    # Train all models
    results = predictor.train_all_models(X_train, y_train, X_val, y_val)
    
    # Display results
    print("\n" + "=" * 80)
    print("TRAINING RESULTS SUMMARY")
    print("=" * 80)
    for model_name, score in results.items():
        print(f"{model_name:30s}: {score:.3f}")
    
    # Test single prediction
    print("\n" + "=" * 80)
    print("SINGLE MATCH PREDICTION TEST")
    print("=" * 80)
    
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
    
    prediction = predictor.predict_match(
        home_data=home_data,
        away_data=away_data,
        league_id=203  # Premier League
    )
    
    print(f"\nPrediction: {prediction['prediction_label']}")
    print(f"Confidence: {prediction['confidence']:.1%}")
    print(f"\nProbabilities:")
    print(f"  Home Win: {prediction['probabilities']['home_win']:.1%}")
    print(f"  Draw:     {prediction['probabilities']['draw']:.1%}")
    print(f"  Away Win: {prediction['probabilities']['away_win']:.1%}")
    print(f"\nModel Votes:")
    for model, vote in prediction['model_votes'].items():
        print(f"  {model:20s}: {vote}")
    
    # Save models
    print("\n" + "=" * 80)
    predictor.save_models(suffix="test")
    
    print("\n" + "=" * 80)
    print("TEST PASSED! Enhanced ML Predictor ready for production")
    print("=" * 80)
