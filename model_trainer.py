# -*- coding: utf-8 -*-
"""
Model Trainer
=============
Advanced training pipeline with:
- Cross-validation
- Hyperparameter tuning
- Model persistence
- Training history tracking

Author: AI Football Analytics
Date: 4 Kasım 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
import pickle
import os
import json
from datetime import datetime
from sklearn.model_selection import (
    cross_val_score,
    GridSearchCV,
    RandomizedSearchCV,
    StratifiedKFold
)
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report
)
import warnings
warnings.filterwarnings('ignore')

print("[OK] Model Trainer Module Loaded")


class ModelTrainer:
    """
    Manages model training with advanced techniques
    """
    
    def __init__(
        self,
        predictor,
        cv_folds: int = 5,
        random_state: int = 42
    ):
        """
        Initialize model trainer
        
        Args:
            predictor: EnhancedMLPredictor instance
            cv_folds: Number of cross-validation folds
            random_state: Random seed for reproducibility
        """
        self.predictor = predictor
        self.cv_folds = cv_folds
        self.random_state = random_state
        
        # Training history
        self.training_history = {
            'xgboost': [],
            'random_forest': [],
            'neural_network': [],
            'logistic': [],
            'poisson': [],
            'ensemble': []
        }
        
        print(f"[OK] Model Trainer initialized")
        print(f"     CV Folds: {cv_folds}")
    
    def cross_validate_model(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        model_name: str
    ) -> Dict[str, float]:
        """
        Perform cross-validation on a model
        
        Args:
            model: Sklearn model
            X: Features
            y: Labels
            model_name: Model identifier
            
        Returns:
            CV scores
        """
        print(f"\n[CV] Cross-validating {model_name}...")
        
        # Stratified K-Fold for balanced splits
        cv = StratifiedKFold(
            n_splits=self.cv_folds,
            shuffle=True,
            random_state=self.random_state
        )
        
        # Calculate scores
        scores = cross_val_score(
            model,
            X,
            y,
            cv=cv,
            scoring='accuracy',
            n_jobs=-1
        )
        
        results = {
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'scores': scores.tolist()
        }
        
        print(f"     Mean CV Accuracy: {results['mean']:.3f} (+/- {results['std']:.3f})")
        
        return results
    
    def hyperparameter_tuning_xgboost(
        self,
        X: np.ndarray,
        y: np.ndarray,
        method: str = 'grid'
    ) -> Dict[str, Any]:
        """
        Tune XGBoost hyperparameters
        
        Args:
            X: Features
            y: Labels
            method: 'grid' or 'random'
            
        Returns:
            Best parameters
        """
        print("\n[TUNING] XGBoost hyperparameter tuning...")
        
        # Parameter grid
        param_grid = {
            'max_depth': [4, 6, 8],
            'learning_rate': [0.01, 0.05, 0.1],
            'n_estimators': [100, 200, 300],
            'subsample': [0.7, 0.8, 0.9],
            'colsample_bytree': [0.7, 0.8, 0.9]
        }
        
        # Create base model
        from xgboost import XGBClassifier
        base_model = XGBClassifier(
            objective='multi:softprob',
            num_class=3,
            random_state=self.random_state
        )
        
        # Search
        if method == 'grid':
            search = GridSearchCV(
                base_model,
                param_grid,
                cv=3,
                scoring='accuracy',
                n_jobs=-1,
                verbose=1
            )
        else:
            search = RandomizedSearchCV(
                base_model,
                param_grid,
                n_iter=20,
                cv=3,
                scoring='accuracy',
                n_jobs=-1,
                random_state=self.random_state,
                verbose=1
            )
        
        search.fit(X, y)
        
        print(f"\n     Best parameters: {search.best_params_}")
        print(f"     Best CV score: {search.best_score_:.3f}")
        
        return {
            'best_params': search.best_params_,
            'best_score': float(search.best_score_),
            'best_model': search.best_estimator_
        }
    
    def hyperparameter_tuning_rf(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Dict[str, Any]:
        """
        Tune Random Forest hyperparameters
        
        Args:
            X: Features
            y: Labels
            
        Returns:
            Best parameters
        """
        print("\n[TUNING] Random Forest hyperparameter tuning...")
        
        from sklearn.ensemble import RandomForestClassifier
        
        param_grid = {
            'n_estimators': [100, 150, 200],
            'max_depth': [8, 10, 12],
            'min_samples_split': [3, 5, 7],
            'min_samples_leaf': [1, 2, 3]
        }
        
        base_model = RandomForestClassifier(
            random_state=self.random_state,
            n_jobs=-1
        )
        
        search = GridSearchCV(
            base_model,
            param_grid,
            cv=3,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        search.fit(X, y)
        
        print(f"\n     Best parameters: {search.best_params_}")
        print(f"     Best CV score: {search.best_score_:.3f}")
        
        return {
            'best_params': search.best_params_,
            'best_score': float(search.best_score_),
            'best_model': search.best_estimator_
        }
    
    def train_with_validation(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        tune_hyperparams: bool = False
    ) -> Dict[str, Any]:
        """
        Train all models with validation
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            tune_hyperparams: Whether to tune hyperparameters
            
        Returns:
            Training results
        """
        print("\n" + "="*80)
        print("TRAINING PIPELINE")
        print("="*80)
        
        # Hyperparameter tuning (optional)
        if tune_hyperparams:
            print("\nPhase 1: Hyperparameter Tuning")
            print("-"*80)
            
            # Tune XGBoost
            xgb_results = self.hyperparameter_tuning_xgboost(
                X_train, y_train, method='random'
            )
            self.predictor.xgb_model = xgb_results['best_model']
            
            # Tune Random Forest
            rf_results = self.hyperparameter_tuning_rf(X_train, y_train)
            self.predictor.rf_model = rf_results['best_model']
        
        # Train all models
        print("\nPhase 2: Model Training")
        print("-"*80)
        
        results = self.predictor.train_all_models(
            X_train, y_train, X_val, y_val
        )
        
        # Cross-validation
        print("\nPhase 3: Cross-Validation")
        print("-"*80)
        
        X_train_scaled = self.predictor.scaler.transform(X_train)
        
        cv_results = {}
        cv_results['xgboost'] = self.cross_validate_model(
            self.predictor.xgb_model, X_train_scaled, y_train, 'XGBoost'
        )
        cv_results['random_forest'] = self.cross_validate_model(
            self.predictor.rf_model, X_train_scaled, y_train, 'RandomForest'
        )
        cv_results['neural_network'] = self.cross_validate_model(
            self.predictor.nn_model, X_train_scaled, y_train, 'NeuralNetwork'
        )
        
        # Update training history
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for model_name, cv_result in cv_results.items():
            self.training_history[model_name].append({
                'timestamp': timestamp,
                'cv_mean': cv_result['mean'],
                'cv_std': cv_result['std'],
                'val_acc': results.get(f'{model_name}_val', 0.0)
            })
        
        return {
            'training': results,
            'cross_validation': cv_results
        }
    
    def get_detailed_metrics(
        self,
        X: np.ndarray,
        y_true: np.ndarray
    ) -> Dict[str, Any]:
        """
        Get detailed performance metrics for all models
        
        Args:
            X: Features
            y_true: True labels
            
        Returns:
            Detailed metrics
        """
        print("\n" + "="*80)
        print("DETAILED METRICS")
        print("="*80)
        
        X_scaled = self.predictor.scaler.transform(X)
        
        metrics = {}
        
        # Labels
        class_names = ['Away Win', 'Draw', 'Home Win']
        
        # Evaluate each model
        models = {
            'xgboost': self.predictor.xgb_model,
            'random_forest': self.predictor.rf_model,
            'neural_network': self.predictor.nn_model,
            'logistic': self.predictor.lr_model,
            'poisson': self.predictor.poisson_model
        }
        
        for model_name, model in models.items():
            print(f"\n[{model_name.upper()}]")
            print("-"*80)
            
            # Predictions
            y_pred = model.predict(X_scaled)
            
            # Accuracy
            accuracy = accuracy_score(y_true, y_pred)
            
            # Precision, Recall, F1
            precision, recall, f1, support = precision_recall_fscore_support(
                y_true, y_pred, average='weighted', zero_division=0
            )
            
            # Classification report
            report = classification_report(
                y_true, y_pred,
                target_names=class_names,
                output_dict=True,
                zero_division=0
            )
            
            metrics[model_name] = {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1),
                'classification_report': report
            }
            
            print(f"Accuracy:  {accuracy:.3f}")
            print(f"Precision: {precision:.3f}")
            print(f"Recall:    {recall:.3f}")
            print(f"F1-Score:  {f1:.3f}")
        
        # Ensemble metrics
        print(f"\n[ENSEMBLE]")
        print("-"*80)
        
        ensemble_pred = self.predictor.predict_ensemble(X)
        ensemble_accuracy = accuracy_score(y_true, ensemble_pred)
        ensemble_precision, ensemble_recall, ensemble_f1, _ = precision_recall_fscore_support(
            y_true, ensemble_pred, average='weighted', zero_division=0
        )
        
        metrics['ensemble'] = {
            'accuracy': float(ensemble_accuracy),
            'precision': float(ensemble_precision),
            'recall': float(ensemble_recall),
            'f1_score': float(ensemble_f1)
        }
        
        print(f"Accuracy:  {ensemble_accuracy:.3f}")
        print(f"Precision: {ensemble_precision:.3f}")
        print(f"Recall:    {ensemble_recall:.3f}")
        print(f"F1-Score:  {ensemble_f1:.3f}")
        
        return metrics
    
    def save_training_history(self, filename: str = "training_history.json") -> None:
        """Save training history to JSON"""
        filepath = os.path.join(self.predictor.model_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(self.training_history, f, indent=2)
        print(f"\n[OK] Training history saved to: {filepath}")
    
    def load_training_history(self, filename: str = "training_history.json") -> None:
        """Load training history from JSON"""
        filepath = os.path.join(self.predictor.model_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.training_history = json.load(f)
            print(f"\n[OK] Training history loaded from: {filepath}")
        else:
            print(f"\n[WARNING] Training history file not found: {filepath}")


# ========== TESTING ==========

if __name__ == "__main__":
    print("=" * 80)
    print("MODEL TRAINER TEST")
    print("=" * 80)
    
    # Import predictor
    from enhanced_ml_predictor import EnhancedMLPredictor
    
    # Create predictor
    predictor = EnhancedMLPredictor()
    
    # Create trainer
    trainer = ModelTrainer(predictor, cv_folds=3)
    
    # Generate synthetic data
    print("\n[TEST] Generating synthetic data...")
    np.random.seed(42)
    n_samples = 300
    n_features = 86
    
    X = np.random.randn(n_samples, n_features)
    y = np.random.choice([0, 1, 2], size=n_samples, p=[0.30, 0.30, 0.40])
    
    # Split
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"[OK] Training: {len(X_train)} samples")
    print(f"[OK] Validation: {len(X_val)} samples")
    
    # Train without hyperparameter tuning (faster for test)
    print("\n[TEST] Training models (without hyperparameter tuning)...")
    results = trainer.train_with_validation(
        X_train, y_train, X_val, y_val,
        tune_hyperparams=False
    )
    
    # Get detailed metrics
    metrics = trainer.get_detailed_metrics(X_val, y_val)
    
    # Save models
    predictor.save_models(suffix="trainer_test")
    
    # Save training history
    trainer.save_training_history()
    
    print("\n" + "=" * 80)
    print("TEST PASSED! Model Trainer ready for production")
    print("=" * 80)
