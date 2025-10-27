"""
Value Bet Detector ve Kelly Criterion Modülü
Akıllı bahis önerileri, arbitrage detection ve bankroll yönetimi
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BettingOdds:
    """Bahis oranları veri sınıfı"""
    home_win: float
    draw: float
    away_win: float
    bookmaker: str = "Unknown"
    
    def get_implied_probabilities(self) -> Dict[str, float]:
        """Oran üzerinden implied probability hesapla"""
        return {
            'home_win': 1 / self.home_win if self.home_win > 0 else 0,
            'draw': 1 / self.draw if self.draw > 0 else 0,
            'away_win': 1 / self.away_win if self.away_win > 0 else 0
        }
    
    def get_margin(self) -> float:
        """Bahisçi marjını hesapla (overround)"""
        implied = self.get_implied_probabilities()
        total = sum(implied.values())
        return (total - 1.0) * 100  # Yüzde olarak
    
    def get_fair_odds(self) -> Dict[str, float]:
        """Marj çıkarılmış adil oranları hesapla"""
        implied = self.get_implied_probabilities()
        total = sum(implied.values())
        
        return {
            'home_win': total / implied['home_win'] if implied['home_win'] > 0 else 0,
            'draw': total / implied['draw'] if implied['draw'] > 0 else 0,
            'away_win': total / implied['away_win'] if implied['away_win'] > 0 else 0
        }


class KellyCriterion:
    """
    Kelly Criterion - Optimal bahis miktarı hesaplama
    
    Formula: f* = (bp - q) / b
    
    Nerede:
    - f* = Bankroll'un yüzdesi olarak optimal bahis
    - b = Kazanç oranı (oran - 1)
    - p = Kazanma olasılığı
    - q = Kaybetme olasılığı (1 - p)
    """
    
    def __init__(self, kelly_fraction: float = 0.25):
        """
        Args:
            kelly_fraction: Fractional Kelly (0.25 = Quarter Kelly)
        """
        self.kelly_fraction = kelly_fraction
    
    def calculate(self, win_probability: float, odds: float) -> Dict:
        """
        Kelly Criterion hesapla
        
        Args:
            win_probability: Gerçek kazanma olasılığı (0-1)
            odds: Bahis oranı (decimal)
        
        Returns:
            Detaylı Kelly analizi
        """
        if win_probability <= 0 or win_probability >= 1:
            return {
                'kelly_percentage': 0,
                'recommendation': 'Bahis yapma',
                'expected_value': 0,
                'risk_level': 'N/A'
            }
        
        # Kelly formülü
        b = odds - 1  # Kazanç oranı
        p = win_probability
        q = 1 - p
        
        kelly_full = (b * p - q) / b
        
        # Negatif Kelly = Bahis yapma
        if kelly_full <= 0:
            return {
                'kelly_percentage': 0,
                'recommendation': 'Bahis yapma (Negatif value)',
                'expected_value': (p * b - q) * 100,
                'risk_level': 'N/A'
            }
        
        # Fractional Kelly uygula
        kelly_adjusted = kelly_full * self.kelly_fraction
        
        # Expected Value (EV)
        ev = (p * b - q) * 100
        
        # Risk seviyesi
        if kelly_adjusted > 0.1:
            risk_level = 'Yüksek'
        elif kelly_adjusted > 0.05:
            risk_level = 'Orta'
        else:
            risk_level = 'Düşük'
        
        # Öneri
        if kelly_adjusted > 0.05:
            recommendation = f"Bankroll'un %{kelly_adjusted*100:.1f}'ını bahse yatır"
        elif kelly_adjusted > 0.02:
            recommendation = f"Küçük bahis (%{kelly_adjusted*100:.1f})"
        else:
            recommendation = "Çok küçük value, atla"
        
        return {
            'kelly_percentage': kelly_adjusted * 100,
            'kelly_full': kelly_full * 100,
            'recommendation': recommendation,
            'expected_value': ev,
            'risk_level': risk_level,
            'fractional_used': self.kelly_fraction
        }


class ValueBetDetector:
    """
    Value Bet tespiti - Gerçek olasılık vs Bahisçi oranları
    """
    
    def __init__(self, min_value: float = 0.05, min_ev: float = 5.0):
        """
        Args:
            min_value: Minimum value yüzdesi (varsayılan %5)
            min_ev: Minimum Expected Value (varsayılan %5)
        """
        self.min_value = min_value
        self.min_ev = min_ev
    
    def find_value_bets(self, betting_odds: BettingOdds,
                       true_probabilities: Dict[str, float],
                       kelly_fraction: float = 0.25) -> List[Dict]:
        """
        Value betleri bul
        
        Args:
            betting_odds: Bahisçi oranları
            true_probabilities: Gerçek olasılıklar (model tahmini)
            kelly_fraction: Kelly Criterion fraksiyonu (varsayılan Quarter Kelly = 0.25)
        
        Returns:
            Value bet listesi
        """
        value_bets = []
        
        # Her sonuç için kontrol et
        outcomes = {
            'Ev Sahibi Kazanır': ('home_win', betting_odds.home_win),
            'Beraberlik': ('draw', betting_odds.draw),
            'Deplasman Kazanır': ('away_win', betting_odds.away_win)
        }
        
        for outcome_name, (prob_key, odds) in outcomes.items():
            true_prob = true_probabilities.get(prob_key, 0)
            
            if true_prob <= 0 or odds <= 1:
                continue
            
            # Expected Value hesapla
            ev = (true_prob * odds - 1) * 100
            
            # Value yüzdesi
            implied_prob = 1 / odds
            value_percentage = ((true_prob - implied_prob) / implied_prob) * 100
            
            # Value bet mi?
            if ev >= self.min_ev and value_percentage >= self.min_value * 100:
                # Kelly Criterion hesapla
                kelly_calculator = KellyCriterion(kelly_fraction=kelly_fraction)
                kelly_info = kelly_calculator.calculate(
                    win_probability=true_prob,
                    odds=odds
                )
                
                value_bets.append({
                    'outcome': outcome_name,
                    'odds': odds,
                    'true_probability': true_prob,
                    'implied_probability': implied_prob,
                    'expected_value': ev,
                    'value_percentage': value_percentage,
                    'kelly_stake': kelly_info['kelly_percentage'],
                    'recommendation': kelly_info['recommendation'],
                    'risk_level': kelly_info['risk_level']
                })
        
        # EV'ye göre sırala
        value_bets.sort(key=lambda x: x['expected_value'], reverse=True)
        
        return value_bets
    
    def calculate_value_rating(self, value_bet: Dict) -> str:
        """Value bet'i değerlendir"""
        ev = value_bet['expected_value']
        
        if ev >= 15:
            return "⭐⭐⭐ Mükemmel"
        elif ev >= 10:
            return "⭐⭐ Çok İyi"
        elif ev >= 5:
            return "⭐ İyi"
        else:
            return "💡 Düşük"


class ArbitrageDetector:
    """
    Arbitrage (Kesin Kazanç) fırsatları tespit eder
    """
    
    @staticmethod
    def detect_arbitrage(odds_list: List[BettingOdds]) -> Optional[Dict]:
        """
        Farklı bahisçilerdeki oranlardan arbitrage bul
        
        Args:
            odds_list: Farklı bahisçilerin oranları
        
        Returns:
            Arbitrage fırsatı varsa detayları
        """
        if len(odds_list) < 2:
            return None
        
        # Her sonuç için en iyi oranı bul
        best_odds = {
            'home_win': max(odds.home_win for odds in odds_list),
            'draw': max(odds.draw for odds in odds_list),
            'away_win': max(odds.away_win for odds in odds_list)
        }
        
        # Arbitrage hesapla
        arb_percentage = (
            1 / best_odds['home_win'] +
            1 / best_odds['draw'] +
            1 / best_odds['away_win']
        )
        
        # Arbitrage var mı? (toplam < 1 olmalı)
        if arb_percentage < 1.0:
            profit_percentage = ((1 / arb_percentage) - 1) * 100
            
            # Optimal stake dağılımı (100 birim bahis için)
            total_stake = 100
            stakes = {
                'home_win': (total_stake / best_odds['home_win']) / arb_percentage,
                'draw': (total_stake / best_odds['draw']) / arb_percentage,
                'away_win': (total_stake / best_odds['away_win']) / arb_percentage
            }
            
            return {
                'is_arbitrage': True,
                'profit_percentage': profit_percentage,
                'best_odds': best_odds,
                'stakes': stakes,
                'total_stake': sum(stakes.values()),
                'guaranteed_profit': profit_percentage
            }
        
        return None


class BankrollManager:
    """
    Bankroll (Bahis sermayesi) yönetimi
    """
    
    def __init__(self, initial_bankroll: float):
        """
        Args:
            initial_bankroll: Başlangıç sermayesi
        """
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.bet_history = []
    
    def calculate_stake(self, kelly_percentage: float, 
                       max_stake_percentage: float = 5.0) -> float:
        """
        Bahis miktarını hesapla
        
        Args:
            kelly_percentage: Kelly Criterion yüzdesi
            max_stake_percentage: Maksimum bahis yüzdesi
        
        Returns:
            Bahis miktarı
        """
        # Kelly'yi sınırla
        safe_percentage = min(kelly_percentage, max_stake_percentage)
        
        return self.current_bankroll * (safe_percentage / 100)
    
    def record_bet(self, stake: float, odds: float, won: bool):
        """Bahis sonucunu kaydet"""
        if won:
            profit = stake * (odds - 1)
            self.current_bankroll += profit
        else:
            self.current_bankroll -= stake
        
        self.bet_history.append({
            'stake': stake,
            'odds': odds,
            'won': won,
            'profit': profit if won else -stake,
            'bankroll_after': self.current_bankroll
        })
    
    def get_statistics(self) -> Dict:
        """Bahis istatistikleri"""
        if not self.bet_history:
            return {
                'total_bets': 0,
                'win_rate': 0,
                'total_profit': 0,
                'roi': 0
            }
        
        total_bets = len(self.bet_history)
        wins = sum(1 for bet in self.bet_history if bet['won'])
        total_profit = self.current_bankroll - self.initial_bankroll
        roi = (total_profit / self.initial_bankroll) * 100
        
        return {
            'total_bets': total_bets,
            'wins': wins,
            'losses': total_bets - wins,
            'win_rate': (wins / total_bets) * 100,
            'total_profit': total_profit,
            'roi': roi,
            'current_bankroll': self.current_bankroll
        }


# Test fonksiyonu
if __name__ == "__main__":
    print("💰 Value Bet Detector Test")
    print("=" * 60)
    
    # Örnek: Model tahmini
    true_probs = {
        'home_win': 0.55,  # Model %55 şans veriyor
        'draw': 0.25,
        'away_win': 0.20
    }
    
    # Bahisçi oranları
    odds = BettingOdds(
        home_win=2.10,  # İmplied prob: %47.6
        draw=3.50,
        away_win=3.80,
        bookmaker="Bahisçi A"
    )
    
    print(f"\n📊 Bahisçi Analizi:")
    print(f"   Margin: {odds.get_margin():.2f}%")
    
    # Value bet detector
    detector = ValueBetDetector(min_value=0.05, min_ev=5.0)
    value_bets = detector.find_value_bets(true_probs, odds)
    
    print(f"\n💎 Bulunan Value Betler: {len(value_bets)}")
    for vb in value_bets:
        print(f"\n   {vb['outcome']}:")
        print(f"   Oran: {vb['odds']:.2f}")
        print(f"   Gerçek Olasılık: {vb['true_probability']*100:.1f}%")
        print(f"   EV: {vb['expected_value']:.2f}%")
        print(f"   Value: {vb['value_percentage']:.2f}%")
        print(f"   Kelly Stake: {vb['kelly_stake']:.2f}%")
        print(f"   Öneri: {vb['recommendation']}")
    
    # Kelly Criterion
    kelly_result = KellyCriterion.calculate(0.55, 2.10, fractional=0.25)
    print(f"\n🎯 Kelly Criterion:")
    print(f"   Optimal Stake: {kelly_result['kelly_percentage']:.2f}%")
    print(f"   EV: {kelly_result['expected_value']:.2f}%")
    print(f"   Öneri: {kelly_result['recommendation']}")
    
    print("\n" + "=" * 60)
    print("✅ Test tamamlandı")
