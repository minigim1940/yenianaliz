"""
Poisson Dağılımı ve Monte Carlo Simülasyon Modülü
Futbol maçları için istatistiksel gol tahmini ve olasılık hesaplamaları
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy.stats import poisson
from collections import Counter
import warnings
warnings.filterwarnings('ignore')


class PoissonMatchSimulator:
    """
    Poisson dağılımı kullanarak maç sonucu simülasyonu
    
    Temel Prensipler:
    - Gol sayıları Poisson dağılımına uyar
    - Lambda (λ) = Beklenen gol sayısı
    - P(X=k) = (λ^k * e^-λ) / k!
    """
    
    def __init__(self, home_attack: float, home_defense: float,
                 away_attack: float, away_defense: float,
                 league_avg_goals: float = 2.7,
                 home_advantage: float = 1.15):
        """
        Args:
            home_attack: Ev sahibi hücum gücü (maç başı gol ortalaması)
            home_defense: Ev sahibi savunma gücü (yediği gol ortalaması)
            away_attack: Deplasman hücum gücü
            away_defense: Deplasman savunma gücü
            league_avg_goals: Lig ortalaması gol
            home_advantage: Ev sahibi avantaj çarpanı
        """
        self.home_attack = home_attack
        self.home_defense = home_defense
        self.away_attack = away_attack
        self.away_defense = away_defense
        self.league_avg = league_avg_goals
        self.home_advantage = home_advantage
        
        # Lambda (beklenen gol) hesapla
        self.lambda_home = self._calculate_lambda('home')
        self.lambda_away = self._calculate_lambda('away')
    
    def _calculate_lambda(self, team: str) -> float:
        """
        Beklenen gol sayısını hesapla (λ)
        
        Formula:
        λ_home = (Home_Attack / League_Avg) * (Away_Defense / League_Avg) * League_Avg * Home_Advantage
        λ_away = (Away_Attack / League_Avg) * (Home_Defense / League_Avg) * League_Avg
        """
        if team == 'home':
            attack_strength = self.home_attack / (self.league_avg / 2)
            defense_weakness = self.away_defense / (self.league_avg / 2)
            lambda_val = attack_strength * defense_weakness * (self.league_avg / 2) * self.home_advantage
        else:  # away
            attack_strength = self.away_attack / (self.league_avg / 2)
            defense_weakness = self.home_defense / (self.league_avg / 2)
            lambda_val = attack_strength * defense_weakness * (self.league_avg / 2)
        
        return max(0.1, lambda_val)  # Minimum 0.1
    
    def calculate_match_probabilities(self, max_goals: int = 10) -> Dict:
        """
        Maç sonucu olasılıklarını hesapla
        
        Args:
            max_goals: Maksimum gol sayısı (hesaplama için)
        
        Returns:
            Detaylı olasılık matrisi
        """
        # Olasılık matrisi oluştur
        prob_matrix = np.zeros((max_goals + 1, max_goals + 1))
        
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                # P(Home=h) * P(Away=a)
                prob_home = poisson.pmf(home_goals, self.lambda_home)
                prob_away = poisson.pmf(away_goals, self.lambda_away)
                prob_matrix[home_goals, away_goals] = prob_home * prob_away
        
        # Sonuç olasılıkları
        home_win_prob = np.sum(np.tril(prob_matrix, -1))  # Home > Away
        draw_prob = np.sum(np.diag(prob_matrix))  # Home = Away
        away_win_prob = np.sum(np.triu(prob_matrix, 1))  # Home < Away
        
        # Gol tahmini
        expected_home_goals = self.lambda_home
        expected_away_goals = self.lambda_away
        
        # En olası skor
        most_likely_score = self._find_most_likely_score(prob_matrix)
        
        # Over/Under olasılıkları
        over_under = self._calculate_over_under(prob_matrix)
        
        # Karşılıklı gol (BTTS - Both Teams To Score)
        btts_yes = 1 - (poisson.pmf(0, self.lambda_home) + poisson.pmf(0, self.lambda_away) - 
                        poisson.pmf(0, self.lambda_home) * poisson.pmf(0, self.lambda_away))
        btts_no = 1 - btts_yes
        
        return {
            'home_win': home_win_prob,
            'draw': draw_prob,
            'away_win': away_win_prob,
            'expected_home_goals': expected_home_goals,
            'expected_away_goals': expected_away_goals,
            'most_likely_score': most_likely_score,
            'probability_matrix': prob_matrix,
            'over_under': over_under,
            'btts_yes': btts_yes,
            'btts_no': btts_no,
            'lambda_home': self.lambda_home,
            'lambda_away': self.lambda_away
        }
    
    def _find_most_likely_score(self, prob_matrix: np.ndarray) -> Tuple[int, int]:
        """En yüksek olasılıklı skoru bul"""
        max_idx = np.unravel_index(prob_matrix.argmax(), prob_matrix.shape)
        return (int(max_idx[0]), int(max_idx[1]))
    
    def _calculate_over_under(self, prob_matrix: np.ndarray) -> Dict:
        """Over/Under olasılıklarını hesapla"""
        over_under = {}
        
        for threshold in [0.5, 1.5, 2.5, 3.5, 4.5]:
            over_prob = 0
            under_prob = 0
            
            for home_goals in range(prob_matrix.shape[0]):
                for away_goals in range(prob_matrix.shape[1]):
                    total_goals = home_goals + away_goals
                    prob = prob_matrix[home_goals, away_goals]
                    
                    if total_goals > threshold:
                        over_prob += prob
                    else:
                        under_prob += prob
            
            over_under[f'over_{threshold}'] = over_prob
            over_under[f'under_{threshold}'] = under_prob
        
        return over_under


class MonteCarloSimulator:
    """
    Monte Carlo simülasyonu ile maç sonucu tahmini
    Binlerce simülasyon yaparak olasılık dağılımı oluşturur
    """
    
    def __init__(self, poisson_sim: PoissonMatchSimulator):
        """
        Args:
            poisson_sim: PoissonMatchSimulator instance
        """
        self.poisson_sim = poisson_sim
    
    def run_simulation(self, n_simulations: int = 10000) -> Dict:
        """
        Monte Carlo simülasyonu çalıştır
        
        Args:
            n_simulations: Simülasyon sayısı
        
        Returns:
            Simülasyon sonuçları ve istatistikleri
        """
        # Simülasyon sonuçlarını sakla
        results = {
            'home_wins': 0,
            'draws': 0,
            'away_wins': 0,
            'scores': [],
            'home_goals_list': [],
            'away_goals_list': []
        }
        
        # Simülasyonları çalıştır
        for _ in range(n_simulations):
            # Poisson dağılımından rastgele gol sayısı üret
            home_goals = np.random.poisson(self.poisson_sim.lambda_home)
            away_goals = np.random.poisson(self.poisson_sim.lambda_away)
            
            # Sonuç kaydet
            results['scores'].append((home_goals, away_goals))
            results['home_goals_list'].append(home_goals)
            results['away_goals_list'].append(away_goals)
            
            # Kazananı belirle
            if home_goals > away_goals:
                results['home_wins'] += 1
            elif home_goals < away_goals:
                results['away_wins'] += 1
            else:
                results['draws'] += 1
        
        # Olasılıkları hesapla
        probabilities = {
            'home_win': results['home_wins'] / n_simulations,
            'draw': results['draws'] / n_simulations,
            'away_win': results['away_wins'] / n_simulations
        }
        
        # Skor dağılımı
        score_distribution = Counter(results['scores'])
        most_common_scores = score_distribution.most_common(10)
        
        # İstatistikler
        stats = {
            'avg_home_goals': np.mean(results['home_goals_list']),
            'avg_away_goals': np.mean(results['away_goals_list']),
            'median_home_goals': np.median(results['home_goals_list']),
            'median_away_goals': np.median(results['away_goals_list']),
            'std_home_goals': np.std(results['home_goals_list']),
            'std_away_goals': np.std(results['away_goals_list'])
        }
        
        # Over/Under simülasyon sonuçları
        over_under_sim = self._calculate_over_under_simulation(results)
        
        # BTTS (Both Teams To Score)
        btts_count = sum(1 for h, a in results['scores'] if h > 0 and a > 0)
        btts_yes = btts_count / n_simulations
        
        return {
            'probabilities': probabilities,
            'score_distribution': most_common_scores,
            'statistics': stats,
            'over_under': over_under_sim,
            'btts_yes': btts_yes,
            'btts_no': 1 - btts_yes,
            'total_simulations': n_simulations,
            'raw_scores': results['scores'][:100]  # İlk 100 sonuç
        }
    
    def _calculate_over_under_simulation(self, results: Dict) -> Dict:
        """Simülasyon sonuçlarından over/under hesapla"""
        over_under = {}
        
        for threshold in [0.5, 1.5, 2.5, 3.5, 4.5]:
            over_count = sum(1 for h, a in results['scores'] if h + a > threshold)
            under_count = len(results['scores']) - over_count
            
            over_under[f'over_{threshold}'] = over_count / len(results['scores'])
            over_under[f'under_{threshold}'] = under_count / len(results['scores'])
        
        return over_under


def compare_poisson_vs_monte_carlo(poisson_results: Dict, mc_results: Dict) -> pd.DataFrame:
    """
    Poisson ve Monte Carlo sonuçlarını karşılaştır
    
    Returns:
        Karşılaştırma DataFrame
    """
    comparison = {
        'Metrik': [
            'Ev Sahibi Kazanır',
            'Beraberlik',
            'Deplasman Kazanır',
            'Over 2.5',
            'Under 2.5',
            'BTTS Var'
        ],
        'Poisson (%)': [
            f"{poisson_results['home_win']*100:.2f}",
            f"{poisson_results['draw']*100:.2f}",
            f"{poisson_results['away_win']*100:.2f}",
            f"{poisson_results['over_under']['over_2.5']*100:.2f}",
            f"{poisson_results['over_under']['under_2.5']*100:.2f}",
            f"{poisson_results['btts_yes']*100:.2f}"
        ],
        'Monte Carlo (%)': [
            f"{mc_results['probabilities']['home_win']*100:.2f}",
            f"{mc_results['probabilities']['draw']*100:.2f}",
            f"{mc_results['probabilities']['away_win']*100:.2f}",
            f"{mc_results['over_under']['over_2.5']*100:.2f}",
            f"{mc_results['over_under']['under_2.5']*100:.2f}",
            f"{mc_results['btts_yes']*100:.2f}"
        ]
    }
    
    return pd.DataFrame(comparison)


# Test fonksiyonu
if __name__ == "__main__":
    print("🎲 Poisson & Monte Carlo Simülasyon Test")
    print("=" * 60)
    
    # Örnek takım istatistikleri
    home_attack = 1.8  # Ev sahibi maç başı attığı gol
    home_defense = 1.2  # Ev sahibi maç başı yediği gol
    away_attack = 1.5
    away_defense = 1.3
    
    # Poisson simülatörü oluştur
    poisson_sim = PoissonMatchSimulator(
        home_attack=home_attack,
        home_defense=home_defense,
        away_attack=away_attack,
        away_defense=away_defense,
        league_avg_goals=2.7
    )
    
    # Poisson olasılıkları
    poisson_results = poisson_sim.calculate_match_probabilities()
    
    print("\n📊 Poisson Dağılımı Sonuçları:")
    print(f"   Lambda (Ev Sahibi): {poisson_results['lambda_home']:.2f}")
    print(f"   Lambda (Deplasman): {poisson_results['lambda_away']:.2f}")
    print(f"   Ev Sahibi Kazanır: {poisson_results['home_win']*100:.2f}%")
    print(f"   Beraberlik: {poisson_results['draw']*100:.2f}%")
    print(f"   Deplasman Kazanır: {poisson_results['away_win']*100:.2f}%")
    print(f"   En Olası Skor: {poisson_results['most_likely_score'][0]}-{poisson_results['most_likely_score'][1]}")
    print(f"   Over 2.5: {poisson_results['over_under']['over_2.5']*100:.2f}%")
    print(f"   BTTS Var: {poisson_results['btts_yes']*100:.2f}%")
    
    # Monte Carlo simülasyonu
    mc_sim = MonteCarloSimulator(poisson_sim)
    mc_results = mc_sim.run_simulation(n_simulations=10000)
    
    print("\n🎲 Monte Carlo Simülasyon (10,000 maç):")
    print(f"   Ev Sahibi Kazanır: {mc_results['probabilities']['home_win']*100:.2f}%")
    print(f"   Beraberlik: {mc_results['probabilities']['draw']*100:.2f}%")
    print(f"   Deplasman Kazanır: {mc_results['probabilities']['away_win']*100:.2f}%")
    print(f"   Ortalama Ev Sahibi Gol: {mc_results['statistics']['avg_home_goals']:.2f}")
    print(f"   Ortalama Deplasman Gol: {mc_results['statistics']['avg_away_goals']:.2f}")
    
    print("\n🏆 En Sık Görülen 5 Skor:")
    for (home, away), count in mc_results['score_distribution'][:5]:
        percentage = (count / mc_results['total_simulations']) * 100
        print(f"   {home}-{away}: {percentage:.2f}% ({count} kez)")
    
    print("\n" + "=" * 60)
    print("✅ Test tamamlandı")
