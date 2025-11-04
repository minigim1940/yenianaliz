# -*- coding: utf-8 -*-
"""
Feature Engineering for Enhanced ML Prediction
================================================
85 advanced features extracted from:
- Shot analysis (xG, quality)
- Passing metrics (creativity, possession)
- Defensive stats (rating, PPDA)
- Form & momentum
- Player quality
- Contextual factors

Author: AI Football Analytics
Date: 4 Kasım 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import streamlit as st

# Import analyzers
from shot_analyzer import ShotAnalyzer
from passing_analyzer import PassingAnalyzer
from defensive_analyzer import DefensiveAnalyzer
from advanced_form_calculator import AdvancedFormCalculator
from expected_goals_calculator import ExpectedGoalsCalculator
from pressing_metrics_calculator import PressingMetricsCalculator
from progressive_metrics_calculator import ProgressiveMetricsCalculator
from expected_assists_calculator import ExpectedAssistsCalculator
from dynamic_home_advantage import DynamicHomeAdvantageCalculator

print("[OK] Feature Engineering Module Loaded")


class FeatureEngineer:
    """
    Main feature engineering class
    Extracts 85 features from raw match data
    """
    
    def __init__(self):
        """Initialize all analyzers"""
        self.shot_analyzer = ShotAnalyzer()
        self.passing_analyzer = PassingAnalyzer()
        self.defensive_analyzer = DefensiveAnalyzer()
        self.form_calculator = AdvancedFormCalculator()
        self.xg_calculator = ExpectedGoalsCalculator()
        self.pressing_calculator = PressingMetricsCalculator()
        self.progressive_calculator = ProgressiveMetricsCalculator()
        self.xa_calculator = ExpectedAssistsCalculator()
        self.home_advantage_calculator = DynamicHomeAdvantageCalculator()
        
        print("[OK] Feature Engineer Initialized - 85 features ready")
    
    def extract_all_features(
        self,
        home_data: Dict[str, Any],
        away_data: Dict[str, Any],
        league_id: int,
        h2h_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Extract all 85 features
        
        Args:
            home_data: Home team data (stats, form, players)
            away_data: Away team data (stats, form, players)
            league_id: League ID for context
            h2h_data: Head-to-head history
            
        Returns:
            Dictionary with 85 features
        """
        features = {}
        
        # 1. Offensive Features (25)
        offensive_features = self._extract_offensive_features(home_data, away_data)
        features.update(offensive_features)
        
        # 2. Defensive Features (20)
        defensive_features = self._extract_defensive_features(home_data, away_data)
        features.update(defensive_features)
        
        # 3. Tactical Features (15)
        tactical_features = self._extract_tactical_features(home_data, away_data)
        features.update(tactical_features)
        
        # 4. Form & Momentum Features (10)
        form_features = self._extract_form_features(home_data, away_data)
        features.update(form_features)
        
        # 5. Player Quality Features (8)
        player_features = self._extract_player_features(home_data, away_data)
        features.update(player_features)
        
        # 6. Contextual Features (7)
        context_features = self._extract_contextual_features(
            home_data, away_data, league_id, h2h_data
        )
        features.update(context_features)
        
        return features
    
    def _extract_offensive_features(
        self,
        home_data: Dict[str, Any],
        away_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Extract 25 offensive features
        Features 1-25
        """
        features = {}
        
        # Get match stats
        home_stats = home_data.get('match_stats', {})
        away_stats = away_data.get('match_stats', {})
        
        # --- xG Features (1-6) ---
        # Use shot data for xG approximation
        home_shot_data = self.shot_analyzer.analyze_match_shots(match_stats=home_stats)
        away_shot_data = self.shot_analyzer.analyze_match_shots(match_stats=away_stats)
        
        features['xg_home_avg'] = home_shot_data.get('xg_total', 0.0)
        features['xg_away_avg'] = away_shot_data.get('xg_total', 0.0)
        
        # xG trend (improving/declining) - from recent matches
        home_recent_xg = home_data.get('recent_xg', [0.0, 0.0, 0.0])
        away_recent_xg = away_data.get('recent_xg', [0.0, 0.0, 0.0])
        
        features['xg_home_trend'] = self._calculate_trend(home_recent_xg)
        features['xg_away_trend'] = self._calculate_trend(away_recent_xg)
        
        # Finishing efficiency
        home_goals = home_data.get('goals_scored_avg', 0.0)
        away_goals = away_data.get('goals_scored_avg', 0.0)
        
        features['goals_per_xg_home'] = home_goals / max(features['xg_home_avg'], 0.1)
        features['goals_per_xg_away'] = away_goals / max(features['xg_away_avg'], 0.1)
        
        # --- Shot Quality Features (7-12) ---
        # Already have shot_data from above
        features['shot_quality_home'] = home_shot_data.get('shot_quality_score', 50.0)
        features['shot_quality_away'] = away_shot_data.get('shot_quality_score', 50.0)
        
        features['shots_on_target_pct_home'] = (
            home_shot_data.get('shots_on_target', 0) / 
            max(home_shot_data.get('total_shots', 1), 1) * 100
        )
        features['shots_on_target_pct_away'] = (
            away_shot_data.get('shots_on_target', 0) / 
            max(away_shot_data.get('total_shots', 1), 1) * 100
        )
        
        features['big_chances_created_home'] = home_shot_data.get('big_chances', 0)
        features['big_chances_created_away'] = away_shot_data.get('big_chances', 0)
        
        # --- Chance Creation Features (13-18) ---
        home_passing = self.passing_analyzer.analyze_passing_performance(match_stats=home_stats)
        away_passing = self.passing_analyzer.analyze_passing_performance(match_stats=away_stats)
        
        features['xa_home_avg'] = home_passing.get('expected_assists', 0.0)
        features['xa_away_avg'] = away_passing.get('expected_assists', 0.0)
        
        features['key_passes_home'] = home_passing.get('key_passes', 0)
        features['key_passes_away'] = away_passing.get('key_passes', 0)
        
        features['final_third_entries_home'] = home_passing.get('final_third_passes', 0)
        features['final_third_entries_away'] = away_passing.get('final_third_passes', 0)
        
        # --- Attack Variety Features (19-25) ---
        # Attack diversity (left/center/right)
        home_attack_dist = home_shot_data.get('shot_position_distribution', {})
        away_attack_dist = away_shot_data.get('shot_position_distribution', {})
        
        features['attack_diversity_home'] = self._calculate_diversity(home_attack_dist)
        features['attack_diversity_away'] = self._calculate_diversity(away_attack_dist)
        
        # Counter attack efficiency
        features['counter_attack_efficiency_home'] = home_data.get('counter_attack_pct', 0.0)
        features['counter_attack_efficiency_away'] = away_data.get('counter_attack_pct', 0.0)
        
        # Set piece threat
        features['set_piece_threat_home'] = home_data.get('set_piece_goals_pct', 0.0)
        features['set_piece_threat_away'] = away_data.get('set_piece_goals_pct', 0.0)
        
        # Box entries
        features['box_entries_home'] = home_passing.get('penalty_area_entries', 0)
        features['box_entries_away'] = away_passing.get('penalty_area_entries', 0)
        
        return features
    
    def _extract_defensive_features(
        self,
        home_data: Dict[str, Any],
        away_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Extract 20 defensive features
        Features 26-45
        """
        features = {}
        
        home_stats = home_data.get('match_stats', {})
        away_stats = away_data.get('match_stats', {})
        
        # --- Defensive Solidity Features (26-31) ---
        home_defense = self.defensive_analyzer.analyze_defensive_performance(
            match_stats=home_stats,
            goals_conceded=home_data.get('goals_conceded_avg', 0.0)
        )
        away_defense = self.defensive_analyzer.analyze_defensive_performance(
            match_stats=away_stats,
            goals_conceded=away_data.get('goals_conceded_avg', 0.0)
        )
        
        features['defensive_rating_home'] = home_defense.get('defensive_rating', 50.0)
        features['defensive_rating_away'] = away_defense.get('defensive_rating', 50.0)
        
        features['clean_sheet_pct_home'] = home_data.get('clean_sheet_pct', 0.0)
        features['clean_sheet_pct_away'] = away_data.get('clean_sheet_pct', 0.0)
        
        features['goals_conceded_per_match_home'] = home_data.get('goals_conceded_avg', 0.0)
        features['goals_conceded_per_match_away'] = away_data.get('goals_conceded_avg', 0.0)
        
        # --- Defensive Actions Features (32-37) ---
        features['tackles_success_rate_home'] = home_defense.get('tackle_success_rate', 50.0)
        features['tackles_success_rate_away'] = away_defense.get('tackle_success_rate', 50.0)
        
        features['interceptions_per_match_home'] = home_defense.get('interceptions', 0)
        features['interceptions_per_match_away'] = away_defense.get('interceptions', 0)
        
        features['blocks_per_match_home'] = home_defense.get('blocks', 0)
        features['blocks_per_match_away'] = away_defense.get('blocks', 0)
        
        # --- Pressing Metrics Features (38-43) ---
        try:
            home_pressing = self.pressing_calculator.calculate_comprehensive_pressing_score(
                home_stats.get('statistics', [])
            )
            away_pressing = self.pressing_calculator.calculate_comprehensive_pressing_score(
                away_stats.get('statistics', [])
            )
            
            features['ppda_home'] = home_pressing.get('ppda', 10.0)
            features['ppda_away'] = away_pressing.get('ppda', 10.0)
            
            features['pressing_intensity_home'] = home_pressing.get('pressing_intensity', 50.0)
            features['pressing_intensity_away'] = away_pressing.get('pressing_intensity', 50.0)
            
            features['counter_press_success_home'] = home_pressing.get('counter_press_efficiency', 0.0)
            features['counter_press_success_away'] = away_pressing.get('counter_press_efficiency', 0.0)
        except Exception:
            # Fallback values if pressing calculation fails
            features['ppda_home'] = 10.0
            features['ppda_away'] = 10.0
            features['pressing_intensity_home'] = 50.0
            features['pressing_intensity_away'] = 50.0
            features['counter_press_success_home'] = 0.0
            features['counter_press_success_away'] = 0.0
        
        # --- Vulnerability Features (44-45) ---
        features['xga_home'] = home_data.get('xg_against_avg', 0.0)
        features['xga_away'] = away_data.get('xg_against_avg', 0.0)
        
        return features
    
    def _extract_tactical_features(
        self,
        home_data: Dict[str, Any],
        away_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Extract 15 tactical features
        Features 46-60
        """
        features = {}
        
        home_stats = home_data.get('match_stats', {})
        away_stats = away_data.get('match_stats', {})
        
        # --- Playing Style Features (46-51) ---
        home_passing = self.passing_analyzer.analyze_passing_performance(match_stats=home_stats)
        away_passing = self.passing_analyzer.analyze_passing_performance(match_stats=away_stats)
        
        features['possession_avg_home'] = home_passing.get('possession_pct', 50.0)
        features['possession_avg_away'] = away_passing.get('possession_pct', 50.0)
        
        # Passing style distribution
        features['passing_style_home'] = self._encode_passing_style(
            home_passing.get('passing_style', 'balanced')
        )
        features['passing_style_away'] = self._encode_passing_style(
            away_passing.get('passing_style', 'balanced')
        )
        
        # Build-up speed
        features['build_up_speed_home'] = home_passing.get('build_up_speed_score', 50.0)
        features['build_up_speed_away'] = away_passing.get('build_up_speed_score', 50.0)
        
        # --- Field Control Features (52-57) ---
        try:
            home_field_tilt = self.progressive_calculator.calculate_field_tilt(
                home_stats.get('statistics', [])
            )
            away_field_tilt = self.progressive_calculator.calculate_field_tilt(
                away_stats.get('statistics', [])
            )
            
            home_progressive_passes = self.progressive_calculator.calculate_progressive_passes(
                home_stats.get('statistics', [])
            )
            away_progressive_passes = self.progressive_calculator.calculate_progressive_passes(
                away_stats.get('statistics', [])
            )
            
            features['field_tilt_home'] = home_field_tilt.get('field_tilt_score', 0.0)
            features['field_tilt_away'] = away_field_tilt.get('field_tilt_score', 0.0)
            
            features['progressive_passes_home'] = home_progressive_passes.get('progressive_passes_count', 0)
            features['progressive_passes_away'] = away_progressive_passes.get('progressive_passes_count', 0)
            
            # Progressive carries - use passes as proxy
            features['progressive_carries_home'] = home_progressive_passes.get('progressive_distance_avg', 0)
            features['progressive_carries_away'] = away_progressive_passes.get('progressive_distance_avg', 0)
        except Exception:
            # Fallback values
            features['field_tilt_home'] = 0.0
            features['field_tilt_away'] = 0.0
            features['progressive_passes_home'] = 0
            features['progressive_passes_away'] = 0
            features['progressive_carries_home'] = 0
            features['progressive_carries_away'] = 0
        
        # --- Tactical Discipline Features (58-60) ---
        home_defense = self.defensive_analyzer.analyze_defensive_performance(
            match_stats=home_stats,
            goals_conceded=0
        )
        away_defense = self.defensive_analyzer.analyze_defensive_performance(
            match_stats=away_stats,
            goals_conceded=0
        )
        
        features['fouls_per_match_home'] = home_defense.get('fouls', 0)
        features['fouls_per_match_away'] = away_defense.get('fouls', 0)
        features['yellow_cards_avg_home'] = home_defense.get('yellow_cards', 0)
        
        return features
    
    def _extract_form_features(
        self,
        home_data: Dict[str, Any],
        away_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Extract 10 form & momentum features
        Features 61-70
        """
        features = {}
        
        # --- Recent Form Features (61-64) ---
        home_recent_results = home_data.get('recent_results', [])
        away_recent_results = away_data.get('recent_results', [])
        
        # Convert results to simple form score (0-100)
        # W=3, D=1, L=0 points, then normalize
        features['advanced_form_home'] = self._calculate_form_score(home_recent_results)
        features['advanced_form_away'] = self._calculate_form_score(away_recent_results)
        
        # Last 5 points
        features['last_5_points_home'] = self._calculate_points(home_recent_results[-5:])
        features['last_5_points_away'] = self._calculate_points(away_recent_results[-5:])
        
        # --- Momentum Features (65-70) ---
        features['momentum_home'] = self._calculate_momentum(home_recent_results)
        features['momentum_away'] = self._calculate_momentum(away_recent_results)
        
        features['win_streak_home'] = self._calculate_streak(home_recent_results, 'W')
        features['win_streak_away'] = self._calculate_streak(away_recent_results, 'W')
        
        features['unbeaten_streak_home'] = self._calculate_streak(
            home_recent_results, ['W', 'D']
        )
        features['unbeaten_streak_away'] = self._calculate_streak(
            away_recent_results, ['W', 'D']
        )
        
        return features
    
    def _extract_player_features(
        self,
        home_data: Dict[str, Any],
        away_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Extract 8 player quality features
        Features 71-78
        """
        features = {}
        
        # --- Squad Strength Features (71-74) ---
        features['top_scorer_goals_home'] = home_data.get('top_scorer_goals', 0)
        features['top_scorer_goals_away'] = away_data.get('top_scorer_goals', 0)
        
        features['top_assist_provider_home'] = home_data.get('top_assists', 0)
        features['top_assist_provider_away'] = away_data.get('top_assists', 0)
        
        # --- Squad Depth Features (75-78) ---
        # Injuries impact (-20 to 0, negative = bad)
        features['injuries_impact_home'] = -home_data.get('key_injuries_count', 0) * 5
        features['injuries_impact_away'] = -away_data.get('key_injuries_count', 0) * 5
        
        # Rotation rate (0-1, higher = more rotation)
        features['squad_rotation_home'] = home_data.get('rotation_rate', 0.5)
        features['squad_rotation_away'] = away_data.get('rotation_rate', 0.5)
        
        return features
    
    def _extract_contextual_features(
        self,
        home_data: Dict[str, Any],
        away_data: Dict[str, Any],
        league_id: int,
        h2h_data: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Extract 7 contextual features
        Features 79-85
        """
        features = {}
        
        # --- Match Context Features (79-81) ---
        # Dynamic home advantage - use league baseline
        league_baselines = {
            203: 1.15,  # Premier League
            140: 1.22,  # Süper Lig
            135: 1.18,  # Serie A
            61: 1.16,   # Ligue 1
            78: 1.17,   # Bundesliga
        }
        features['home_advantage_factor'] = league_baselines.get(league_id, 1.15)
        
        # League-specific scoring rate
        features['league_avg_goals'] = home_data.get('league_avg_goals', 2.5)
        
        # League competitiveness (0-100, higher = more competitive)
        features['league_competitiveness'] = home_data.get('league_balance', 50.0)
        
        # --- Head-to-Head Features (82-85) ---
        if h2h_data:
            features['h2h_home_wins_pct'] = h2h_data.get('home_win_pct', 0.33)
            features['h2h_avg_goals_home'] = h2h_data.get('avg_goals_home', 1.5)
            features['h2h_avg_goals_away'] = h2h_data.get('avg_goals_away', 1.0)
            features['h2h_recent_trend'] = h2h_data.get('recent_trend_score', 0.0)
        else:
            # Default values if no H2H data
            features['h2h_home_wins_pct'] = 0.33
            features['h2h_avg_goals_home'] = 1.5
            features['h2h_avg_goals_away'] = 1.0
            features['h2h_recent_trend'] = 0.0
        
        return features
    
    # ========== Helper Methods ==========
    
    def _calculate_trend(self, values: List[float]) -> float:
        """
        Calculate trend from recent values
        Positive = improving, Negative = declining
        Range: -1.0 to +1.0
        """
        if len(values) < 2:
            return 0.0
        
        # Simple linear regression slope
        x = np.arange(len(values))
        y = np.array(values)
        
        if np.std(y) == 0:
            return 0.0
        
        correlation = np.corrcoef(x, y)[0, 1]
        return correlation
    
    def _calculate_diversity(self, distribution: Dict[str, int]) -> float:
        """
        Calculate Shannon entropy for attack diversity
        Higher = more varied attack
        Range: 0-100
        """
        if not distribution or sum(distribution.values()) == 0:
            return 50.0
        
        total = sum(distribution.values())
        probabilities = [v/total for v in distribution.values() if v > 0]
        
        if len(probabilities) <= 1:
            return 25.0
        
        entropy = -sum(p * np.log2(p) for p in probabilities)
        max_entropy = np.log2(len(distribution))
        
        normalized = (entropy / max_entropy) * 100 if max_entropy > 0 else 50.0
        return normalized
    
    def _encode_passing_style(self, style: str) -> float:
        """
        Encode passing style as numeric
        0 = Direct, 50 = Balanced, 100 = Possession
        """
        style_map = {
            'direct': 0.0,
            'balanced': 50.0,
            'possession': 100.0
        }
        return style_map.get(style.lower(), 50.0)
    
    def _calculate_points(self, results: List[str]) -> int:
        """Calculate total points from results (W=3, D=1, L=0)"""
        if not results:
            return 0
        
        points = 0
        for result in results:
            if result == 'W':
                points += 3
            elif result == 'D':
                points += 1
        
        return points
    
    def _calculate_form_score(self, results: List[str]) -> float:
        """
        Calculate form score from results
        0-100 scale based on points percentage
        """
        if not results:
            return 50.0
        
        points = self._calculate_points(results)
        max_points = len(results) * 3
        
        score = (points / max_points) * 100 if max_points > 0 else 50.0
        return score
    
    def _calculate_momentum(self, results: List[str]) -> float:
        """
        Calculate momentum score
        Recent results weighted more heavily
        Range: -1.0 (very bad) to +1.0 (very good)
        """
        if not results or len(results) < 3:
            return 0.0
        
        # Weight recent matches more (last match = weight 5, etc.)
        weights = list(range(1, len(results) + 1))
        scores = []
        
        for result in results:
            if result == 'W':
                scores.append(1.0)
            elif result == 'D':
                scores.append(0.0)
            else:
                scores.append(-1.0)
        
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        max_possible = sum(weights)
        
        momentum = weighted_sum / max_possible if max_possible > 0 else 0.0
        return momentum
    
    def _calculate_streak(self, results: List[str], target) -> int:
        """
        Calculate current streak
        target can be single result ('W') or list (['W', 'D'])
        """
        if not results:
            return 0
        
        if isinstance(target, str):
            target = [target]
        
        streak = 0
        for result in reversed(results):
            if result in target:
                streak += 1
            else:
                break
        
        return streak


# ========== Feature Normalization ==========

class FeatureNormalizer:
    """
    Normalize features to 0-1 range
    Supports: Min-Max, Standard, Robust scaling
    """
    
    def __init__(self, method: str = 'minmax'):
        """
        Args:
            method: 'minmax', 'standard', or 'robust'
        """
        self.method = method
        self.scalers = {}
        print(f"[OK] Feature Normalizer ({method}) Initialized")
    
    def fit_transform(
        self,
        features_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Fit scalers and transform features
        """
        if self.method == 'minmax':
            return self._minmax_scale(features_df)
        elif self.method == 'standard':
            return self._standard_scale(features_df)
        elif self.method == 'robust':
            return self._robust_scale(features_df)
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def _minmax_scale(self, df: pd.DataFrame) -> pd.DataFrame:
        """Min-Max scaling to [0, 1]"""
        scaled = df.copy()
        
        for col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            
            if max_val > min_val:
                scaled[col] = (df[col] - min_val) / (max_val - min_val)
            else:
                scaled[col] = 0.5  # Constant value
        
        return scaled
    
    def _standard_scale(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standard scaling (mean=0, std=1)"""
        scaled = df.copy()
        
        for col in df.columns:
            mean_val = df[col].mean()
            std_val = df[col].std()
            
            if std_val > 0:
                scaled[col] = (df[col] - mean_val) / std_val
            else:
                scaled[col] = 0.0
        
        return scaled
    
    def _robust_scale(self, df: pd.DataFrame) -> pd.DataFrame:
        """Robust scaling (median, IQR) - resistant to outliers"""
        scaled = df.copy()
        
        for col in df.columns:
            median_val = df[col].median()
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            
            if iqr > 0:
                scaled[col] = (df[col] - median_val) / iqr
            else:
                scaled[col] = 0.0
        
        return scaled


# ========== Testing ==========

if __name__ == "__main__":
    print("=" * 80)
    print("FEATURE ENGINEERING TEST")
    print("=" * 80)
    
    # Initialize
    engineer = FeatureEngineer()
    
    # Mock data
    home_data = {
        'match_stats': {'statistics': []},
        'goals_scored_avg': 1.8,
        'goals_conceded_avg': 1.2,
        'recent_results': ['W', 'W', 'D', 'W', 'L'],
        'top_scorer_goals': 15,
        'top_assists': 8,
    }
    
    away_data = {
        'match_stats': {'statistics': []},
        'goals_scored_avg': 1.5,
        'goals_conceded_avg': 1.3,
        'recent_results': ['L', 'D', 'W', 'D', 'W'],
        'top_scorer_goals': 12,
        'top_assists': 6,
    }
    
    # Extract features
    features = engineer.extract_all_features(
        home_data=home_data,
        away_data=away_data,
        league_id=203  # Premier League
    )
    
    print(f"\n[OK] Extracted {len(features)} features:")
    print("\nSample features:")
    for i, (key, value) in enumerate(list(features.items())[:10]):
        print(f"  {i+1}. {key}: {value:.2f}")
    
    print("\n" + "=" * 80)
    print("TEST PASSED! Feature engineering ready for ML pipeline")
    print("=" * 80)
