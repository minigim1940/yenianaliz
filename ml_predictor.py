# -*- coding: utf-8 -*-
"""
Makine Öğrenmesi Bazlı Tahmin Sistemi
Gerçek maç sonuçlarından öğrenen adaptif model
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import math

class MatchLearningSystem:
    """Geçmiş maç sonuçlarından öğrenen sistem"""
    
    def __init__(self, data_file: str = "match_learning_data.json"):
        self.data_file = data_file
        self.learning_data = self.load_learning_data()
        
    def load_learning_data(self) -> Dict:
        """Öğrenme verilerini yükle"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "matches": [],
            "team_patterns": {},
            "league_patterns": {},
            "success_rate": 0.0,
            "total_predictions": 0,
            "correct_predictions": 0,
            "last_update": datetime.now().isoformat()
        }
    
    def save_learning_data(self):
        """Öğrenme verilerini kaydet"""
        self.learning_data["last_update"] = datetime.now().isoformat()
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.learning_data, f, ensure_ascii=False, indent=2)
    
    def add_match_result(self, team_a_id: int, team_b_id: int, league_id: int,
                        prediction: Dict, actual_result: Dict, 
                        model_factors: Dict):
        """
        Maç sonucunu ve model tahminini kaydet
        
        Args:
            prediction: Model tahmini {'win_a': 45, 'draw': 30, 'win_b': 25}
            actual_result: Gerçek sonuç {'home_score': 2, 'away_score': 1, 'winner': 'home'}
            model_factors: Model faktörleri (form, elo, etc.)
        """
        
        # Tahmin doğruluğunu kontrol et
        predicted_winner = max(prediction, key=prediction.get)
        actual_winner = actual_result.get('winner', 'draw')
        
        is_correct = (
            (predicted_winner == 'win_a' and actual_winner == 'home') or
            (predicted_winner == 'win_b' and actual_winner == 'away') or
            (predicted_winner == 'draw' and actual_winner == 'draw')
        )
        
        # Maç verisini kaydet
        match_data = {
            "date": datetime.now().isoformat(),
            "team_a_id": team_a_id,
            "team_b_id": team_b_id,
            "league_id": league_id,
            "prediction": prediction,
            "actual_result": actual_result,
            "model_factors": model_factors,
            "is_correct": is_correct,
            "confidence": prediction[predicted_winner] - sorted(prediction.values(), reverse=True)[1]
        }
        
        self.learning_data["matches"].append(match_data)
        
        # İstatistikleri güncelle
        self.learning_data["total_predictions"] += 1
        if is_correct:
            self.learning_data["correct_predictions"] += 1
        
        self.learning_data["success_rate"] = (
            self.learning_data["correct_predictions"] / 
            self.learning_data["total_predictions"] * 100
        )
        
        # Takım öğrenme verilerini güncelle
        self._update_team_patterns(team_a_id, team_b_id, match_data)
        
        # Lig öğrenme verilerini güncelle  
        self._update_league_patterns(league_id, match_data)
        
        # Eski verileri temizle (son 500 maç)
        if len(self.learning_data["matches"]) > 500:
            self.learning_data["matches"] = self.learning_data["matches"][-500:]
        
        self.save_learning_data()
    
    def _update_team_patterns(self, team_a_id: int, team_b_id: int, match_data: Dict):
        """Takım bazlı öğrenme verilerini güncelle"""
        
        for team_id in [team_a_id, team_b_id]:
            team_key = str(team_id)
            
            if team_key not in self.learning_data["team_patterns"]:
                self.learning_data["team_patterns"][team_key] = {
                    "matches_played": 0,
                    "home_performance": {"wins": 0, "draws": 0, "losses": 0, "total": 0},
                    "away_performance": {"wins": 0, "draws": 0, "losses": 0, "total": 0},
                    "goal_patterns": {"avg_scored": 0.0, "avg_conceded": 0.0},
                    "form_effectiveness": {"good_form_wins": 0, "bad_form_losses": 0},
                    "vs_strong_teams": {"wins": 0, "total": 0},
                    "vs_weak_teams": {"wins": 0, "total": 0}
                }
            
            pattern = self.learning_data["team_patterns"][team_key]
            pattern["matches_played"] += 1
            
            # Ev sahibi/deplasman performansı
            is_home = (team_id == team_a_id)
            location_key = "home_performance" if is_home else "away_performance"
            
            actual_winner = match_data["actual_result"].get("winner")
            if (is_home and actual_winner == "home") or (not is_home and actual_winner == "away"):
                pattern[location_key]["wins"] += 1
            elif actual_winner == "draw":
                pattern[location_key]["draws"] += 1
            else:
                pattern[location_key]["losses"] += 1
            
            pattern[location_key]["total"] += 1
    
    def _update_league_patterns(self, league_id: int, match_data: Dict):
        """Lig bazlı öğrenme verilerini güncelle"""
        
        league_key = str(league_id)
        
        if league_key not in self.learning_data["league_patterns"]:
            self.learning_data["league_patterns"][league_key] = {
                "matches_analyzed": 0,
                "home_advantage": {"wins": 0, "total": 0},
                "high_scoring": {"over_2_5": 0, "total": 0},
                "upsets": {"count": 0, "total_favorites": 0}
            }
        
        league_pattern = self.learning_data["league_patterns"][league_key]
        league_pattern["matches_analyzed"] += 1
        
        # Ev sahibi avantajı
        actual_winner = match_data["actual_result"].get("winner")
        if actual_winner == "home":
            league_pattern["home_advantage"]["wins"] += 1
        league_pattern["home_advantage"]["total"] += 1
        
        # Gol ortalaması
        home_score = match_data["actual_result"].get("home_score", 0)
        away_score = match_data["actual_result"].get("away_score", 0)
        total_goals = home_score + away_score
        
        if total_goals > 2:
            league_pattern["high_scoring"]["over_2_5"] += 1
        league_pattern["high_scoring"]["total"] += 1
    
    def get_team_learning_adjustment(self, team_a_id: int, team_b_id: int, 
                                   location: str = "home") -> Dict[str, float]:
        """
        Takım öğrenme verilerine dayalı ayarlama faktörleri
        
        Returns:
            Dict: {'attack_adj': 1.05, 'defense_adj': 0.95, 'confidence_adj': 1.1}
        """
        
        team_id = team_a_id if location == "home" else team_b_id
        team_key = str(team_id)
        
        if team_key not in self.learning_data["team_patterns"]:
            return {"attack_adj": 1.0, "defense_adj": 1.0, "confidence_adj": 1.0}
        
        pattern = self.learning_data["team_patterns"][team_key]
        
        # Lokasyon bazlı performans
        location_key = f"{location}_performance"
        location_data = pattern.get(location_key, {"wins": 0, "total": 1})
        
        if location_data["total"] < 5:  # Yeterli veri yok
            return {"attack_adj": 1.0, "defense_adj": 1.0, "confidence_adj": 1.0}
        
        win_rate = location_data["wins"] / location_data["total"]
        
        # Başarı oranına göre ayarlama
        if win_rate > 0.7:  # %70+ başarı
            attack_adj = 1.08
            defense_adj = 1.05
            confidence_adj = 1.15
        elif win_rate > 0.5:  # %50-70 başarı
            attack_adj = 1.04
            defense_adj = 1.02
            confidence_adj = 1.08
        elif win_rate < 0.3:  # %30- başarı
            attack_adj = 0.92
            defense_adj = 0.95
            confidence_adj = 0.85
        else:
            attack_adj = 0.96
            defense_adj = 0.98
            confidence_adj = 0.92
        
        return {
            "attack_adj": attack_adj,
            "defense_adj": defense_adj, 
            "confidence_adj": confidence_adj
        }
    
    def get_league_learning_adjustment(self, league_id: int) -> Dict[str, float]:
        """Lig öğrenme verilerine dayalı ayarlama"""
        
        league_key = str(league_id)
        
        if league_key not in self.learning_data["league_patterns"]:
            return {"home_advantage_adj": 1.0, "goal_expectancy_adj": 1.0}
        
        league_pattern = self.learning_data["league_patterns"][league_key]
        
        # Ev sahibi avantajı ayarlaması
        home_data = league_pattern["home_advantage"]
        if home_data["total"] > 10:
            home_win_rate = home_data["wins"] / home_data["total"]
            
            if home_win_rate > 0.6:  # Güçlü ev avantajı
                home_advantage_adj = 1.12
            elif home_win_rate < 0.4:  # Zayıf ev avantajı
                home_advantage_adj = 0.92
            else:
                home_advantage_adj = 1.0
        else:
            home_advantage_adj = 1.0
        
        # Gol beklentisi ayarlaması
        scoring_data = league_pattern["high_scoring"]
        if scoring_data["total"] > 10:
            high_scoring_rate = scoring_data["over_2_5"] / scoring_data["total"]
            
            if high_scoring_rate > 0.6:  # Yüksek skorlu lig
                goal_expectancy_adj = 1.10
            elif high_scoring_rate < 0.4:  # Düşük skorlu lig
                goal_expectancy_adj = 0.90
            else:
                goal_expectancy_adj = 1.0
        else:
            goal_expectancy_adj = 1.0
        
        return {
            "home_advantage_adj": home_advantage_adj,
            "goal_expectancy_adj": goal_expectancy_adj
        }
    
    def get_prediction_confidence_multiplier(self, prediction_factors: Dict) -> float:
        """
        Geçmiş başarılara göre tahmin güven çarpanı
        
        Args:
            prediction_factors: Model faktörleri
            
        Returns:
            0.7-1.3 arası güven çarpanı
        """
        
        if self.learning_data["total_predictions"] < 10:
            return 1.0  # Yeterli veri yok
        
        success_rate = self.learning_data["success_rate"]
        
        # Başarı oranına göre güven ayarlaması
        if success_rate > 75:
            base_multiplier = 1.20  # Yüksek başarı = yüksek güven
        elif success_rate > 65:
            base_multiplier = 1.10
        elif success_rate > 55:
            base_multiplier = 1.05
        elif success_rate < 45:
            base_multiplier = 0.80  # Düşük başarı = düşük güven
        else:
            base_multiplier = 0.90
        
        # Son 10 maçın performansına göre ince ayar
        recent_matches = self.learning_data["matches"][-10:]
        if len(recent_matches) >= 5:
            recent_success = sum(1 for m in recent_matches if m["is_correct"]) / len(recent_matches)
            
            if recent_success > success_rate / 100 + 0.1:  # Son form iyi
                base_multiplier *= 1.05
            elif recent_success < success_rate / 100 - 0.1:  # Son form kötü
                base_multiplier *= 0.95
        
        return max(0.7, min(1.3, base_multiplier))
    
    def get_system_stats(self) -> Dict:
        """Sistem istatistiklerini döndür"""
        return {
            "total_matches": len(self.learning_data["matches"]),
            "success_rate": self.learning_data["success_rate"],
            "total_predictions": self.learning_data["total_predictions"],
            "correct_predictions": self.learning_data["correct_predictions"],
            "teams_analyzed": len(self.learning_data["team_patterns"]),
            "leagues_analyzed": len(self.learning_data["league_patterns"])
        }

# Global instance
ml_system = MatchLearningSystem()