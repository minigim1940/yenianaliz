"""
ENSEMBLE PREDICTOR - Birden Fazla Modeli Birleştiren Tahmin Sistemi
Phase 6: XGBoost + LightGBM + Ağırlıklı Tahmin kombinasyonu
"""
from typing import Dict, List, Tuple
from ml_model_manager import get_ml_manager
from weighted_prediction import calculate_weighted_score, calculate_win_probability
from factor_weights import get_weight_manager
import numpy as np

class EnsemblePredictor:
    """Birden fazla tahmin yöntemini birleştir"""
    
    def __init__(self):
        self.ml_manager = get_ml_manager()
        self.weight_manager = get_weight_manager()
        
    def predict_ensemble(self, 
                        team1_factors: Dict[str, float],
                        team2_factors: Dict[str, float],
                        league: str = 'super_lig',
                        match_type: str = 'mid_table',
                        ensemble_method: str = 'voting') -> Dict:
        """
        Ensemble tahmin - Birden fazla yöntemi birleştir
        
        Args:
            team1_factors: Ev sahibi faktörleri
            team2_factors: Deplasman faktörleri
            league: Lig profili
            match_type: Maç tipi
            ensemble_method: 'voting', 'averaging', 'weighted'
        
        Returns:
            Birleşik tahmin sonucu
        """
        predictions = {}
        
        # 1. ML Tahminleri (XGBoost + LightGBM)
        ml_predictions = self._get_ml_predictions(team1_factors, team2_factors)
        predictions['ml'] = ml_predictions
        
        # 2. Ağırlıklı Tahmin
        weighted_pred = self._get_weighted_prediction(
            team1_factors, team2_factors, league, match_type
        )
        predictions['weighted'] = weighted_pred
        
        # 3. Ensemble yöntemi uygula
        if ensemble_method == 'voting':
            final_pred = self._voting_ensemble(ml_predictions, weighted_pred)
        elif ensemble_method == 'averaging':
            final_pred = self._averaging_ensemble(ml_predictions, weighted_pred)
        elif ensemble_method == 'weighted':
            final_pred = self._weighted_ensemble(ml_predictions, weighted_pred)
        else:
            # Default: voting
            final_pred = self._voting_ensemble(ml_predictions, weighted_pred)
        
        return {
            'ensemble_prediction': final_pred,
            'individual_predictions': predictions,
            'ensemble_method': ensemble_method,
            'confidence': final_pred['confidence']
        }
    
    def _get_ml_predictions(self, team1_factors: Dict, team2_factors: Dict) -> Dict:
        """ML modellerinden tahminleri al"""
        ml_results = {}
        
        # XGBoost
        try:
            xgb_pred = self.ml_manager.predict(
                team1_factors, team2_factors, 'xgb_real_v1'
            )
            ml_results['xgboost'] = xgb_pred
        except Exception as e:
            # Fallback: demo model
            try:
                xgb_pred = self.ml_manager.predict(
                    team1_factors, team2_factors, 'xgb_v1'
                )
                ml_results['xgboost'] = xgb_pred
            except:
                ml_results['xgboost'] = None
        
        # LightGBM
        try:
            lgb_pred = self.ml_manager.predict(
                team1_factors, team2_factors, 'lgb_real_v1'
            )
            ml_results['lightgbm'] = lgb_pred
        except Exception as e:
            # Fallback: demo model
            try:
                lgb_pred = self.ml_manager.predict(
                    team1_factors, team2_factors, 'lgb_v1'
                )
                ml_results['lightgbm'] = lgb_pred
            except:
                ml_results['lightgbm'] = None
        
        return ml_results
    
    def _get_weighted_prediction(self, team1_factors: Dict, team2_factors: Dict,
                                 league: str, match_type: str) -> Dict:
        """Ağırlıklı tahmin sisteminden tahmin al"""
        # Skorları hesapla (fonksiyon kendi ağırlıkları alır)
        team1_score, _ = calculate_weighted_score(team1_factors, league, match_type)
        team2_score, _ = calculate_weighted_score(team2_factors, league, match_type)
        
        # Kazanma olasılıkları
        home_prob, draw_prob, away_prob = calculate_win_probability(
            team1_score, team2_score
        )
        
        # Tahmin
        probs = {'home_win': home_prob, 'draw': draw_prob, 'away_win': away_prob}
        prediction = max(probs, key=probs.get)
        
        return {
            'prediction': prediction,
            'probabilities': probs,
            'confidence': probs[prediction],
            'scores': {'home': team1_score, 'away': team2_score}
        }
    
    def _voting_ensemble(self, ml_preds: Dict, weighted_pred: Dict) -> Dict:
        """Çoğunluk oylaması ile ensemble"""
        votes = []
        confidences = []
        
        # ML tahminleri
        for model_name, pred in ml_preds.items():
            if pred:
                votes.append(pred['prediction'])
                confidences.append(pred['confidence'])
        
        # Ağırlıklı tahmin
        votes.append(weighted_pred['prediction'])
        confidences.append(weighted_pred['confidence'])
        
        # En çok oy alan tahmin
        from collections import Counter
        vote_counts = Counter(votes)
        final_prediction = vote_counts.most_common(1)[0][0]
        
        # Güven: ilgili tahminlerin ortalama güveni
        relevant_confidences = [c for v, c in zip(votes, confidences) if v == final_prediction]
        avg_confidence = np.mean(relevant_confidences) if relevant_confidences else 0.5
        
        # Olasılık dağılımı
        total_votes = len(votes)
        probabilities = {
            'home_win': votes.count('home_win') / total_votes,
            'draw': votes.count('draw') / total_votes,
            'away_win': votes.count('away_win') / total_votes
        }
        
        return {
            'prediction': final_prediction,
            'confidence': avg_confidence,
            'probabilities': probabilities,
            'method': 'voting',
            'votes': dict(vote_counts)
        }
    
    def _averaging_ensemble(self, ml_preds: Dict, weighted_pred: Dict) -> Dict:
        """Olasılık ortalaması ile ensemble"""
        all_probs = []
        
        # ML tahminleri
        for model_name, pred in ml_preds.items():
            if pred:
                all_probs.append(pred['probabilities'])
        
        # Ağırlıklı tahmin
        all_probs.append(weighted_pred['probabilities'])
        
        # Ortalama olasılıklar
        avg_probs = {
            'home_win': np.mean([p['home_win'] for p in all_probs]),
            'draw': np.mean([p['draw'] for p in all_probs]),
            'away_win': np.mean([p['away_win'] for p in all_probs])
        }
        
        # En yüksek olasılık
        final_prediction = max(avg_probs, key=avg_probs.get)
        
        return {
            'prediction': final_prediction,
            'confidence': avg_probs[final_prediction],
            'probabilities': avg_probs,
            'method': 'averaging',
            'n_models': len(all_probs)
        }
    
    def _weighted_ensemble(self, ml_preds: Dict, weighted_pred: Dict) -> Dict:
        """Ağırlıklı kombinasyon (ML %70, Weighted %30)"""
        ml_weight = 0.7
        weighted_weight = 0.3
        
        # ML tahminlerini birleştir (XGB + LGB ortalama)
        ml_probs_list = [p['probabilities'] for p in ml_preds.values() if p]
        
        if ml_probs_list:
            ml_avg_probs = {
                'home_win': np.mean([p['home_win'] for p in ml_probs_list]),
                'draw': np.mean([p['draw'] for p in ml_probs_list]),
                'away_win': np.mean([p['away_win'] for p in ml_probs_list])
            }
        else:
            # ML yoksa sadece weighted kullan
            return weighted_pred
        
        # Weighted probs
        w_probs = weighted_pred['probabilities']
        
        # Kombine et
        final_probs = {
            'home_win': ml_avg_probs['home_win'] * ml_weight + w_probs['home_win'] * weighted_weight,
            'draw': ml_avg_probs['draw'] * ml_weight + w_probs['draw'] * weighted_weight,
            'away_win': ml_avg_probs['away_win'] * ml_weight + w_probs['away_win'] * weighted_weight
        }
        
        # En yüksek olasılık
        final_prediction = max(final_probs, key=final_probs.get)
        
        return {
            'prediction': final_prediction,
            'confidence': final_probs[final_prediction],
            'probabilities': final_probs,
            'method': 'weighted_combination',
            'weights': {'ml': ml_weight, 'rule_based': weighted_weight}
        }
    
    def explain_ensemble(self, prediction_result: Dict) -> str:
        """Ensemble tahminini açıkla"""
        explanation = []
        
        explanation.append("🔮 ENSEMBLE TAHMİN ANALİZİ")
        explanation.append("=" * 60)
        
        # Final tahmin
        final = prediction_result['ensemble_prediction']
        explanation.append(f"\n✅ Final Tahmin: {final['prediction'].upper()}")
        explanation.append(f"📊 Güven: {final['confidence']:.1%}")
        explanation.append(f"🎯 Yöntem: {final['method']}")
        
        # Olasılıklar
        explanation.append(f"\n📈 Olasılık Dağılımı:")
        for outcome, prob in final['probabilities'].items():
            bar = "█" * int(prob * 40)
            explanation.append(f"  {outcome:12s}: {prob:>6.1%} {bar}")
        
        # Bireysel tahminler
        explanation.append(f"\n🤖 Bireysel Model Tahminleri:")
        
        # ML modeller
        ml_preds = prediction_result['individual_predictions']['ml']
        for model_name, pred in ml_preds.items():
            if pred:
                explanation.append(f"\n  {model_name.upper()}:")
                explanation.append(f"    Tahmin: {pred['prediction']}")
                explanation.append(f"    Güven: {pred['confidence']:.1%}")
        
        # Weighted
        w_pred = prediction_result['individual_predictions']['weighted']
        explanation.append(f"\n  WEIGHTED SYSTEM:")
        explanation.append(f"    Tahmin: {w_pred['prediction']}")
        explanation.append(f"    Güven: {w_pred['confidence']:.1%}")
        explanation.append(f"    Skorlar: Home {w_pred['scores']['home']:.2f} - Away {w_pred['scores']['away']:.2f}")
        
        # Voting detayı (eğer varsa)
        if 'votes' in final:
            explanation.append(f"\n📊 Oy Dağılımı:")
            for outcome, count in final['votes'].items():
                explanation.append(f"  {outcome}: {count} oy")
        
        return "\n".join(explanation)


# Singleton instance
_ensemble_predictor = None

def get_ensemble_predictor() -> EnsemblePredictor:
    """Global ensemble predictor instance"""
    global _ensemble_predictor
    if _ensemble_predictor is None:
        _ensemble_predictor = EnsemblePredictor()
    return _ensemble_predictor


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔮 ENSEMBLE PREDICTOR TEST")
    print("="*70)
    
    # Test verileri
    team1_factors = {
        'form': 0.75, 'elo_diff': 100, 'home_advantage': 0.7,
        'h2h': 0.65, 'league_position': 0.8, 'injuries': 0.3,
        'motivation': 0.7, 'recent_xg': 0.6, 'weather': 0.5,
        'referee': 0.5, 'betting_odds': 0.6, 'tactical_matchup': 0.65,
        'transfer_impact': 0.6, 'squad_experience': 0.7,
        'match_importance': 0.6, 'fatigue': 0.4, 'recent_performance': 0.7
    }
    
    team2_factors = {
        'form': 0.4, 'elo_diff': -100, 'home_advantage': 0.3,
        'h2h': 0.35, 'league_position': 0.4, 'injuries': 0.6,
        'motivation': 0.5, 'recent_xg': 0.4, 'weather': 0.5,
        'referee': 0.5, 'betting_odds': 0.4, 'tactical_matchup': 0.4,
        'transfer_impact': 0.5, 'squad_experience': 0.5,
        'match_importance': 0.6, 'fatigue': 0.6, 'recent_performance': 0.4
    }
    
    # Ensemble predictor
    predictor = get_ensemble_predictor()
    
    # Test: Her 3 yöntem
    for method in ['voting', 'averaging', 'weighted']:
        print(f"\n{'─'*70}")
        print(f"🎯 Yöntem: {method.upper()}")
        print(f"{'─'*70}")
        
        result = predictor.predict_ensemble(
            team1_factors, team2_factors,
            league='super_lig',
            match_type='mid_table',
            ensemble_method=method
        )
        
        # Açıklama
        explanation = predictor.explain_ensemble(result)
        print(explanation)
    
    print("\n" + "="*70)
    print("✅ TEST TAMAMLANDI!")
    print("="*70)
