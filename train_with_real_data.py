# -*- coding: utf-8 -*-
"""
Real Data Training Script for ML Models
========================================
Fetches historical match data from API-Football and trains production models.

Features:
- Fetch historical matches from major leagues
- Extract comprehensive features for each match
- Train all 5 ML models
- Save production-ready models
- Generate training report

Author: AI Football Analytics
Date: 4 Kasım 2025
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from tqdm import tqdm

# Import ML modules
from feature_engineer import FeatureEngineer
from enhanced_ml_predictor import EnhancedMLPredictor
from model_trainer import ModelTrainer
from ml_evaluator import MLEvaluator
import api_utils

print("="*80)
print("REAL DATA TRAINING SCRIPT")
print("="*80)

# ============================================================================
# Configuration
# ============================================================================

# API Configuration
API_KEY = os.environ.get("API_KEY", "6336fb21e17dea87880d3b133132a13f")
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

# Training Configuration
TARGET_MATCHES = 1000  # Target number of matches to collect
MAX_MATCHES = 1500     # Maximum to prevent over-collection

# Major leagues to include
MAJOR_LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    203: "Süper Lig",
    94: "Primeira Liga",
    88: "Eredivisie"
}

# Seasons to fetch
CURRENT_SEASON = 2024
SEASONS = [2024, 2023, 2022]  # Last 3 seasons

# Output directory
DATA_DIR = "training_data"
MODEL_DIR = "models"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# ============================================================================
# Data Collection Functions
# ============================================================================

def fetch_finished_fixtures(league_id: int, season: int, max_fixtures: int = 200) -> List[Dict]:
    """Fetch finished fixtures from a league/season"""
    print(f"\n[Fetching] League {league_id} - Season {season}")
    
    params = {
        'league': league_id,
        'season': season,
        'status': 'FT'  # Finished matches only
    }
    
    try:
        fixtures, error = api_utils.make_api_request(
            API_KEY, BASE_URL, "fixtures", params, skip_limit=True
        )
        
        if error:
            print(f"  ⚠ Error: {error}")
            return []
        
        if not fixtures or 'response' not in fixtures:
            print(f"  ⚠ No fixtures found")
            return []
        
        finished = fixtures['response'][:max_fixtures]
        print(f"  ✓ Found {len(finished)} finished fixtures")
        return finished
        
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        return []


def extract_match_features_and_label(fixture: Dict, league_id: int) -> Tuple[Dict, int]:
    """Extract features and label from a finished fixture"""
    
    try:
        fixture_id = fixture['fixture']['id']
        home_team = fixture['teams']['home']
        away_team = fixture['teams']['away']
        goals = fixture['goals']
        
        # Determine match outcome (label)
        home_score = goals['home']
        away_score = goals['away']
        
        if home_score > away_score:
            label = 0  # Home win
        elif home_score < away_score:
            label = 2  # Away win
        else:
            label = 1  # Draw
        
        # Get team statistics
        home_stats, _ = api_utils.get_team_statistics(
            API_KEY, BASE_URL, home_team['id'], league_id, CURRENT_SEASON, skip_limit=True
        )
        
        away_stats, _ = api_utils.get_team_statistics(
            API_KEY, BASE_URL, away_team['id'], league_id, CURRENT_SEASON, skip_limit=True
        )
        
        # Get recent matches
        home_recent, _ = api_utils.get_team_last_matches_stats(
            API_KEY, BASE_URL, home_team['id'], limit=5, skip_limit=True
        )
        
        away_recent, _ = api_utils.get_team_last_matches_stats(
            API_KEY, BASE_URL, away_team['id'], limit=5, skip_limit=True
        )
        
        # Prepare data structure for feature extraction
        home_data = prepare_team_data(home_team, home_stats, home_recent)
        away_data = prepare_team_data(away_team, away_stats, away_recent)
        
        # Get H2H data
        h2h_data, _ = api_utils.get_h2h_matches(
            API_KEY, BASE_URL, home_team['id'], away_team['id'], 5
        )
        
        return {
            'fixture_id': fixture_id,
            'home_data': home_data,
            'away_data': away_data,
            'league_id': league_id,
            'h2h_data': h2h_data,
            'home_team': home_team['name'],
            'away_team': away_team['name'],
            'home_score': home_score,
            'away_score': away_score
        }, label
        
    except Exception as e:
        print(f"  ⚠ Error extracting features: {e}")
        return None, None


def prepare_team_data(team: Dict, stats: Dict, recent_matches: List) -> Dict:
    """Prepare team data structure for feature extraction"""
    
    data = {
        'match_stats': {'statistics': []},
        'goals_scored_avg': 0.0,
        'goals_conceded_avg': 0.0,
        'recent_results': [],
        'top_scorer_goals': 0,
        'top_assists': 0,
        'clean_sheet_pct': 0.0,
        'recent_xg': []
    }
    
    # Extract from stats
    if stats and 'response' in stats and stats['response']:
        stats_response = stats['response']
        
        if 'fixtures' in stats_response:
            fixtures = stats_response['fixtures']
            played = fixtures.get('played', {}).get('total', 1)
            
            # Goals
            goals_for = stats_response.get('goals', {}).get('for', {}).get('total', {}).get('total', 0)
            goals_against = stats_response.get('goals', {}).get('against', {}).get('total', {}).get('total', 0)
            
            data['goals_scored_avg'] = goals_for / max(played, 1)
            data['goals_conceded_avg'] = goals_against / max(played, 1)
            
            # Clean sheets
            clean_sheets = stats_response.get('clean_sheet', {}).get('total', 0)
            data['clean_sheet_pct'] = (clean_sheets / max(played, 1)) * 100
    
    # Extract from recent matches
    if recent_matches:
        for match in recent_matches[:5]:
            # Determine result
            if match.get('teams', {}).get('home', {}).get('id') == team['id']:
                home_goals = match.get('goals', {}).get('home', 0)
                away_goals = match.get('goals', {}).get('away', 0)
            else:
                home_goals = match.get('goals', {}).get('away', 0)
                away_goals = match.get('goals', {}).get('home', 0)
            
            if home_goals > away_goals:
                data['recent_results'].append('W')
            elif home_goals < away_goals:
                data['recent_results'].append('L')
            else:
                data['recent_results'].append('D')
            
            # xG if available
            xg = match.get('statistics', {}).get('expected_goals', 0)
            if xg > 0:
                data['recent_xg'].append(xg)
    
    return data


def collect_training_data(target_matches: int) -> Tuple[List[Dict], List[int]]:
    """Collect training data from API"""
    
    print(f"\n{'='*80}")
    print(f"COLLECTING TRAINING DATA")
    print(f"{'='*80}")
    print(f"Target: {target_matches} matches")
    print(f"Leagues: {len(MAJOR_LEAGUES)}")
    print(f"Seasons: {len(SEASONS)}")
    
    all_match_data = []
    all_labels = []
    
    matches_per_league = target_matches // len(MAJOR_LEAGUES)
    
    for league_id, league_name in MAJOR_LEAGUES.items():
        print(f"\n[League] {league_name} (ID: {league_id})")
        
        league_matches = []
        league_labels = []
        
        for season in SEASONS:
            if len(league_matches) >= matches_per_league:
                break
            
            # Fetch fixtures
            fixtures = fetch_finished_fixtures(league_id, season, max_fixtures=100)
            
            if not fixtures:
                continue
            
            # Process each fixture
            for fixture in tqdm(fixtures, desc=f"  Season {season}", leave=False):
                if len(league_matches) >= matches_per_league:
                    break
                
                # Extract features and label
                match_data, label = extract_match_features_and_label(fixture, league_id)
                
                if match_data and label is not None:
                    league_matches.append(match_data)
                    league_labels.append(label)
                
                # Rate limiting (API has limits)
                time.sleep(0.1)
        
        print(f"  ✓ Collected {len(league_matches)} matches from {league_name}")
        
        all_match_data.extend(league_matches)
        all_labels.extend(league_labels)
        
        # Progress update
        print(f"\n[Progress] Total: {len(all_match_data)}/{target_matches} matches")
        
        if len(all_match_data) >= target_matches:
            break
    
    print(f"\n{'='*80}")
    print(f"DATA COLLECTION COMPLETE")
    print(f"{'='*80}")
    print(f"Total Matches: {len(all_match_data)}")
    print(f"  Home Wins: {all_labels.count(0)} ({all_labels.count(0)/len(all_labels)*100:.1f}%)")
    print(f"  Draws:     {all_labels.count(1)} ({all_labels.count(1)/len(all_labels)*100:.1f}%)")
    print(f"  Away Wins: {all_labels.count(2)} ({all_labels.count(2)/len(all_labels)*100:.1f}%)")
    
    return all_match_data, all_labels


def save_collected_data(match_data: List[Dict], labels: List[int]):
    """Save collected data to disk"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_file = os.path.join(DATA_DIR, f"match_data_{timestamp}.json")
    labels_file = os.path.join(DATA_DIR, f"labels_{timestamp}.json")
    
    print(f"\n[Saving] Collected data...")
    
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(match_data, f, ensure_ascii=False, indent=2)
    
    with open(labels_file, 'w', encoding='utf-8') as f:
        json.dump(labels, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Data saved to: {data_file}")
    print(f"  ✓ Labels saved to: {labels_file}")
    
    return data_file, labels_file


# ============================================================================
# Feature Extraction
# ============================================================================

def extract_features_from_data(match_data: List[Dict], labels: List[int]) -> Tuple[np.ndarray, np.ndarray]:
    """Extract features from collected match data"""
    
    print(f"\n{'='*80}")
    print(f"FEATURE EXTRACTION")
    print(f"{'='*80}")
    
    engineer = FeatureEngineer()
    
    X_list = []
    y_list = []
    
    for i, (data, label) in enumerate(tqdm(zip(match_data, labels), total=len(match_data), desc="Extracting features")):
        try:
            # Extract features
            features = engineer.extract_all_features(
                home_data=data['home_data'],
                away_data=data['away_data'],
                league_id=data['league_id'],
                h2h_data=data.get('h2h_data')
            )
            
            # Convert to array
            feature_array = np.array(list(features.values()))
            
            X_list.append(feature_array)
            y_list.append(label)
            
        except Exception as e:
            print(f"\n  ⚠ Error extracting features for match {i}: {e}")
            continue
    
    X = np.array(X_list)
    y = np.array(y_list)
    
    print(f"\n✓ Feature extraction complete")
    print(f"  Feature matrix shape: {X.shape}")
    print(f"  Labels shape: {y.shape}")
    print(f"  Features per match: {X.shape[1]}")
    
    return X, y


# ============================================================================
# Model Training
# ============================================================================

def train_production_models(X: np.ndarray, y: np.ndarray) -> str:
    """Train production models with real data"""
    
    print(f"\n{'='*80}")
    print(f"MODEL TRAINING")
    print(f"{'='*80}")
    
    # Create trainer
    trainer = ModelTrainer()
    
    # Train all models with cross-validation
    print("\n[Training] All models with 5-fold CV...")
    cv_results = trainer.train_with_cross_validation(X, y, n_folds=5)
    
    # Display CV results
    print(f"\n[CV Results]")
    for model_name, scores in cv_results.items():
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        print(f"  {model_name:15s}: {mean_score:.3f} ± {std_score:.3f}")
    
    # Hyperparameter tuning for best models
    print(f"\n[Tuning] XGBoost hyperparameters...")
    best_params_xgb = trainer.tune_xgboost(X, y)
    print(f"  ✓ Best XGBoost params: {best_params_xgb}")
    
    print(f"\n[Tuning] RandomForest hyperparameters...")
    best_params_rf = trainer.tune_random_forest(X, y)
    print(f"  ✓ Best RandomForest params: {best_params_rf}")
    
    # Final training with full data
    print(f"\n[Training] Final models with full dataset...")
    from sklearn.model_selection import train_test_split
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    predictor = EnhancedMLPredictor()
    predictor.train_all_models(X_train, y_train, X_val, y_val)
    
    # Save models
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_prefix = f"{timestamp}_production"
    
    print(f"\n[Saving] Production models...")
    predictor.save_models(suffix="production")
    
    print(f"  ✓ Models saved with prefix: {model_prefix}")
    
    return model_prefix


# ============================================================================
# Evaluation
# ============================================================================

def evaluate_production_models(X: np.ndarray, y: np.ndarray, model_prefix: str):
    """Evaluate trained models"""
    
    print(f"\n{'='*80}")
    print(f"MODEL EVALUATION")
    print(f"{'='*80}")
    
    # Load models
    predictor = EnhancedMLPredictor()
    predictor.load_models(model_prefix)
    
    # Split data
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Create evaluator
    evaluator = MLEvaluator()
    
    # Evaluate
    print("\n[Evaluating] On test set...")
    results = evaluator.evaluate_all_models(
        predictor.xgb_model,
        predictor.rf_model,
        predictor.nn_model,
        predictor.lr_model,
        predictor.poisson_model,
        X_test,
        y_test
    )
    
    # Display results
    print(f"\n[Test Results]")
    for model_name, metrics in results.items():
        print(f"\n{model_name}:")
        print(f"  Accuracy:  {metrics['accuracy']:.3f}")
        print(f"  Precision: {metrics['precision']:.3f}")
        print(f"  Recall:    {metrics['recall']:.3f}")
        print(f"  F1 Score:  {metrics['f1']:.3f}")
    
    # Save evaluation report
    report_file = os.path.join(MODEL_DIR, f"{model_prefix}_evaluation.json")
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n  ✓ Evaluation report saved: {report_file}")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main training pipeline"""
    
    start_time = time.time()
    
    print(f"\n[START] Real data training pipeline")
    print(f"  API Key: {'✓ Set' if API_KEY else '✗ Missing'}")
    print(f"  Target matches: {TARGET_MATCHES}")
    print(f"  Leagues: {len(MAJOR_LEAGUES)}")
    
    # Step 1: Collect data
    print(f"\n{'='*80}")
    print(f"STEP 1: DATA COLLECTION")
    print(f"{'='*80}")
    
    match_data, labels = collect_training_data(TARGET_MATCHES)
    
    if len(match_data) < 100:
        print(f"\n❌ ERROR: Not enough data collected ({len(match_data)} matches)")
        print(f"  Minimum required: 100 matches")
        return
    
    # Save collected data
    data_file, labels_file = save_collected_data(match_data, labels)
    
    # Step 2: Extract features
    print(f"\n{'='*80}")
    print(f"STEP 2: FEATURE EXTRACTION")
    print(f"{'='*80}")
    
    X, y = extract_features_from_data(match_data, labels)
    
    # Step 3: Train models
    print(f"\n{'='*80}")
    print(f"STEP 3: MODEL TRAINING")
    print(f"{'='*80}")
    
    model_prefix = train_production_models(X, y)
    
    # Step 4: Evaluate models
    print(f"\n{'='*80}")
    print(f"STEP 4: EVALUATION")
    print(f"{'='*80}")
    
    evaluate_production_models(X, y, model_prefix)
    
    # Summary
    elapsed = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"TRAINING COMPLETE")
    print(f"{'='*80}")
    print(f"  Matches collected: {len(match_data)}")
    print(f"  Features extracted: {X.shape[1]}")
    print(f"  Models trained: 5 (XGB, RF, NN, LR, Poisson)")
    print(f"  Model prefix: {model_prefix}")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print(f"\n✅ Production models ready for deployment!")
    

if __name__ == "__main__":
    main()
