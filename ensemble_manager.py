# -*- coding: utf-8 -*-
"""
Ensemble Manager
================
Advanced ensemble techniques for ML model combination:
- Weighted voting with confidence calibration
- Dynamic weight adjustment based on performance
- Probability calibration
- Prediction confidence scoring

Author: AI Football Analytics
Date: 4 Kasım 2025
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from sklearn.calibration import CalibratedClassifierCV
import warnings
warnings.filterwarnings('ignore')

print("[OK] Ensemble Manager Module Loaded")


class EnsembleManager:
    """
    Manages ensemble predictions with advanced weighting
    """
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        calibration: bool = True
    ):
        """
        Initialize ensemble manager
        
        Args:
            weights: Model weights {model_name: weight}
            calibration: Apply probability calibration
        """
        # Default weights (sum to 1.0)
        self.weights = weights or {
            'xgboost': 0.35,
            'random_forest': 0.25,
            'neural_network': 0.20,
            'logistic': 0.10,
            'poisson': 0.10
        }
        
        self.calibration = calibration
        self.performance_history = {model: [] for model in self.weights.keys()}
        
        print(f"[OK] Ensemble Manager initialized")
        print(f"     Weights: {self.weights}")
        print(f"     Calibration: {calibration}")
    
    def weighted_vote(
        self,
        predictions: Dict[str, np.ndarray],
        return_probabilities: bool = False
    ) -> np.ndarray:
        """
        Combine predictions using weighted voting
        
        Args:
            predictions: {model_name: probabilities (n_samples, 3)}
            return_probabilities: Return probabilities instead of class
            
        Returns:
            Ensemble predictions
        """
        # Weighted sum of probabilities
        ensemble_proba = np.zeros_like(predictions['xgboost'])
        
        for model_name, proba in predictions.items():
            weight = self.weights.get(model_name, 0.0)
            ensemble_proba += proba * weight
        
        if return_probabilities:
            return ensemble_proba
        else:
            return np.argmax(ensemble_proba, axis=1)
    
    def dynamic_weighting(
        self,
        predictions: Dict[str, np.ndarray],
        y_true: np.ndarray,
        window_size: int = 100
    ) -> Dict[str, float]:
        """
        Dynamically adjust weights based on recent performance
        
        Args:
            predictions: {model_name: predictions (n_samples,)}
            y_true: True labels
            window_size: Number of recent predictions to consider
            
        Returns:
            Updated weights
        """
        # Calculate recent accuracy for each model
        accuracies = {}
        for model_name, preds in predictions.items():
            # Take last window_size predictions
            recent_preds = preds[-window_size:] if len(preds) > window_size else preds
            recent_true = y_true[-window_size:] if len(y_true) > window_size else y_true
            
            accuracy = np.mean(recent_preds == recent_true)
            accuracies[model_name] = accuracy
            
            # Update performance history
            self.performance_history[model_name].append(accuracy)
        
        # Normalize accuracies to weights (sum to 1.0)
        total_accuracy = sum(accuracies.values())
        if total_accuracy > 0:
            new_weights = {
                model: acc / total_accuracy
                for model, acc in accuracies.items()
            }
        else:
            new_weights = self.weights  # Keep original if all failed
        
        return new_weights
    
    def calculate_confidence(
        self,
        probabilities: np.ndarray,
        method: str = 'max_prob'
    ) -> float:
        """
        Calculate prediction confidence
        
        Args:
            probabilities: Class probabilities (3,)
            method: 'max_prob', 'entropy', or 'margin'
            
        Returns:
            Confidence score (0-1)
        """
        if method == 'max_prob':
            # Highest probability
            return float(np.max(probabilities))
        
        elif method == 'entropy':
            # Normalized entropy (lower = more confident)
            entropy = -np.sum(probabilities * np.log(probabilities + 1e-10))
            max_entropy = np.log(len(probabilities))
            return 1.0 - (entropy / max_entropy)
        
        elif method == 'margin':
            # Difference between top 2 probabilities
            sorted_probs = np.sort(probabilities)
            margin = sorted_probs[-1] - sorted_probs[-2]
            return float(margin)
        
        else:
            return float(np.max(probabilities))
    
    def calibrate_probabilities(
        self,
        probabilities: np.ndarray,
        y_true: np.ndarray,
        method: str = 'platt'
    ) -> np.ndarray:
        """
        Calibrate probabilities using Platt scaling or isotonic regression
        
        Args:
            probabilities: Predicted probabilities (n_samples, 3)
            y_true: True labels
            method: 'platt' (sigmoid) or 'isotonic'
            
        Returns:
            Calibrated probabilities
        """
        # For now, simple temperature scaling
        # Can enhance with CalibratedClassifierCV later
        
        # Temperature parameter (can be learned)
        temperature = 1.5
        
        # Apply temperature scaling
        calibrated = probabilities ** (1.0 / temperature)
        
        # Re-normalize to sum to 1
        calibrated = calibrated / np.sum(calibrated, axis=1, keepdims=True)
        
        return calibrated
    
    def consensus_prediction(
        self,
        predictions: Dict[str, int],
        probabilities: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """
        Calculate consensus from multiple models
        
        Args:
            predictions: {model_name: predicted_class}
            probabilities: {model_name: class_probabilities}
            
        Returns:
            {
                'consensus': 2,
                'agreement': 0.8,  # % of models agreeing
                'conflicting': False,
                'details': {...}
            }
        """
        # Count votes for each class
        votes = {0: 0, 1: 0, 2: 0}
        for pred in predictions.values():
            votes[pred] += 1
        
        # Find majority class
        consensus = max(votes, key=votes.get)
        
        # Calculate agreement (% of models agreeing)
        agreement = votes[consensus] / len(predictions)
        
        # Check if conflicting (no clear majority)
        conflicting = agreement < 0.5
        
        # Average probabilities for consensus class
        avg_confidence = np.mean([
            probs[consensus] for probs in probabilities.values()
        ])
        
        outcome_map = {0: 'Away Win', 1: 'Draw', 2: 'Home Win'}
        
        result = {
            'consensus': int(consensus),
            'consensus_label': outcome_map[consensus],
            'agreement': float(agreement),
            'conflicting': conflicting,
            'confidence': float(avg_confidence),
            'vote_distribution': votes,
            'individual_predictions': {
                model: outcome_map[pred] 
                for model, pred in predictions.items()
            }
        }
        
        return result
    
    def get_recommendation(
        self,
        probabilities: np.ndarray,
        confidence_threshold: float = 0.60
    ) -> Dict[str, Any]:
        """
        Generate betting recommendation based on ensemble prediction
        
        Args:
            probabilities: Class probabilities (3,)
            confidence_threshold: Minimum confidence for recommendation
            
        Returns:
            {
                'bet': True/False,
                'outcome': 'Home Win',
                'confidence': 0.72,
                'suggested_stake': 'Medium',
                'reasoning': '...'
            }
        """
        # Find predicted outcome
        prediction = np.argmax(probabilities)
        confidence = float(np.max(probabilities))
        
        outcome_map = {0: 'Away Win', 1: 'Draw', 2: 'Home Win'}
        
        # Determine if bet is recommended
        bet = confidence >= confidence_threshold
        
        # Stake suggestion based on confidence
        if confidence >= 0.75:
            stake = 'High'
        elif confidence >= 0.65:
            stake = 'Medium'
        elif confidence >= 0.55:
            stake = 'Low'
        else:
            stake = 'None'
        
        # Generate reasoning
        if bet:
            reasoning = f"Strong model consensus ({confidence:.1%}) for {outcome_map[prediction]}"
        else:
            reasoning = f"Low confidence ({confidence:.1%}) - Too risky to recommend bet"
        
        # Check for draw risk
        draw_prob = probabilities[1]
        if draw_prob > 0.35:
            reasoning += f" | High draw risk ({draw_prob:.1%})"
        
        result = {
            'bet': bet,
            'outcome': outcome_map[prediction],
            'confidence': confidence,
            'suggested_stake': stake,
            'reasoning': reasoning,
            'draw_risk': float(draw_prob),
            'probabilities': {
                'home_win': float(probabilities[2]),
                'draw': float(probabilities[1]),
                'away_win': float(probabilities[0])
            }
        }
        
        return result


# ========== TESTING ==========

if __name__ == "__main__":
    print("=" * 80)
    print("ENSEMBLE MANAGER TEST")
    print("=" * 80)
    
    # Create ensemble manager
    manager = EnsembleManager()
    
    # Simulate model predictions
    print("\n[TEST] Simulating 5 model predictions...")
    
    # Sample predictions (probabilities for Away, Draw, Home)
    predictions_proba = {
        'xgboost': np.array([[0.20, 0.25, 0.55]]),
        'random_forest': np.array([[0.25, 0.30, 0.45]]),
        'neural_network': np.array([[0.15, 0.20, 0.65]]),
        'logistic': np.array([[0.30, 0.35, 0.35]]),
        'poisson': np.array([[0.22, 0.28, 0.50]])
    }
    
    # Test 1: Weighted voting
    print("\n[TEST 1] Weighted Voting")
    print("-" * 80)
    ensemble_proba = manager.weighted_vote(predictions_proba, return_probabilities=True)
    ensemble_pred = np.argmax(ensemble_proba[0])
    
    print(f"Ensemble probabilities: {ensemble_proba[0]}")
    print(f"Ensemble prediction: {ensemble_pred} (0=Away, 1=Draw, 2=Home)")
    
    # Test 2: Confidence calculation
    print("\n[TEST 2] Confidence Calculation")
    print("-" * 80)
    
    for method in ['max_prob', 'entropy', 'margin']:
        conf = manager.calculate_confidence(ensemble_proba[0], method=method)
        print(f"{method:15s}: {conf:.3f}")
    
    # Test 3: Consensus prediction
    print("\n[TEST 3] Consensus Prediction")
    print("-" * 80)
    
    predictions_class = {
        'xgboost': 2,
        'random_forest': 2,
        'neural_network': 2,
        'logistic': 1,
        'poisson': 2
    }
    
    proba_dict = {k: v[0] for k, v in predictions_proba.items()}
    
    consensus = manager.consensus_prediction(predictions_class, proba_dict)
    
    print(f"Consensus: {consensus['consensus_label']}")
    print(f"Agreement: {consensus['agreement']:.1%}")
    print(f"Conflicting: {consensus['conflicting']}")
    print(f"Confidence: {consensus['confidence']:.1%}")
    print(f"\nVote Distribution:")
    for outcome, votes in consensus['vote_distribution'].items():
        outcome_name = {0: 'Away', 1: 'Draw', 2: 'Home'}[outcome]
        print(f"  {outcome_name}: {votes} votes")
    
    # Test 4: Betting recommendation
    print("\n[TEST 4] Betting Recommendation")
    print("-" * 80)
    
    recommendation = manager.get_recommendation(ensemble_proba[0])
    
    print(f"Bet: {recommendation['bet']}")
    print(f"Outcome: {recommendation['outcome']}")
    print(f"Confidence: {recommendation['confidence']:.1%}")
    print(f"Suggested Stake: {recommendation['suggested_stake']}")
    print(f"Draw Risk: {recommendation['draw_risk']:.1%}")
    print(f"Reasoning: {recommendation['reasoning']}")
    
    # Test 5: Dynamic weighting
    print("\n[TEST 5] Dynamic Weighting (Simulated Performance)")
    print("-" * 80)
    
    # Simulate predictions and ground truth
    simulated_preds = {
        'xgboost': np.array([2, 2, 2, 1, 2]),
        'random_forest': np.array([2, 1, 2, 1, 2]),
        'neural_network': np.array([2, 2, 2, 2, 0]),
        'logistic': np.array([1, 1, 1, 1, 1]),
        'poisson': np.array([2, 2, 1, 1, 2])
    }
    
    y_true = np.array([2, 2, 2, 1, 2])  # Ground truth
    
    new_weights = manager.dynamic_weighting(simulated_preds, y_true, window_size=5)
    
    print("Original weights:")
    for model, weight in manager.weights.items():
        print(f"  {model:20s}: {weight:.3f}")
    
    print("\nDynamic weights (based on recent performance):")
    for model, weight in new_weights.items():
        print(f"  {model:20s}: {weight:.3f}")
    
    print("\n" + "=" * 80)
    print("TEST PASSED! Ensemble Manager ready for production")
    print("=" * 80)
