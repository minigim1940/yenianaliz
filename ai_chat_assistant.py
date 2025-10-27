# -*- coding: utf-8 -*-
"""
AI Football Chat Assistant
===========================
Futbol analizi için doğal dil işleme tabanlı sohbet asistanı
OpenAI/Gemini entegrasyonu
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import re


class FootballKnowledgeBase:
    """Futbol bilgi tabanı"""
    
    def __init__(self):
        self.teams_db = self._load_teams_database()
        self.leagues_db = self._load_leagues_database()
        self.glossary = self._load_football_glossary()
    
    def _load_teams_database(self) -> Dict:
        """Takım veritabanı"""
        return {
            'galatasaray': {
                'full_name': 'Galatasaray SK',
                'country': 'Turkey',
                'league': 'Süper Lig',
                'founded': 1905,
                'stadium': 'Ali Sami Yen RAMS Park',
                'api_id': 548,
                'aliases': ['gs', 'gala', 'cimbom', 'aslan']
            },
            'fenerbahce': {
                'full_name': 'Fenerbahçe SK',
                'country': 'Turkey',
                'league': 'Süper Lig',
                'founded': 1907,
                'stadium': 'Şükrü Saracoğlu',
                'api_id': 549,
                'aliases': ['fb', 'fener', 'kanarya']
            },
            'besiktas': {
                'full_name': 'Beşiktaş JK',
                'country': 'Turkey',
                'league': 'Süper Lig',
                'founded': 1903,
                'stadium': 'Vodafone Park',
                'api_id': 550,
                'aliases': ['bjk', 'kartal']
            },
            'trabzonspor': {
                'full_name': 'Trabzonspor',
                'country': 'Turkey',
                'league': 'Süper Lig',
                'founded': 1967,
                'stadium': 'Şenol Güneş Stadyumu',
                'api_id': 609,
                'aliases': ['trabzon', 'ts', 'bordo mavili']
            },
            'real_madrid': {
                'full_name': 'Real Madrid CF',
                'country': 'Spain',
                'league': 'La Liga',
                'founded': 1902,
                'stadium': 'Santiago Bernabéu',
                'api_id': 541,
                'aliases': ['real', 'madrid', 'los blancos', 'merengues']
            },
            'barcelona': {
                'full_name': 'FC Barcelona',
                'country': 'Spain',
                'league': 'La Liga',
                'founded': 1899,
                'stadium': 'Camp Nou',
                'api_id': 529,
                'aliases': ['barca', 'blaugrana', 'fcb', 'barça']
            },
            'manchester_united': {
                'full_name': 'Manchester United',
                'country': 'England',
                'league': 'Premier League',
                'founded': 1878,
                'stadium': 'Old Trafford',
                'api_id': 33,
                'aliases': ['man utd', 'united', 'red devils', 'mufc']
            },
            'liverpool': {
                'full_name': 'Liverpool FC',
                'country': 'England',
                'league': 'Premier League',
                'founded': 1892,
                'stadium': 'Anfield',
                'api_id': 40,
                'aliases': ['liverpool', 'reds', 'lfc', 'pool']
            },
            'bayern': {
                'full_name': 'Bayern München',
                'country': 'Germany',
                'league': 'Bundesliga',
                'founded': 1900,
                'stadium': 'Allianz Arena',
                'api_id': 157,
                'aliases': ['bayern munich', 'fcb', 'bavarians']
            },
            'juventus': {
                'full_name': 'Juventus FC',
                'country': 'Italy',
                'league': 'Serie A',
                'founded': 1897,
                'stadium': 'Allianz Stadium',
                'api_id': 496,
                'aliases': ['juve', 'bianconeri', 'old lady']
            },
        }
    
    def _load_leagues_database(self) -> Dict:
        """Lig veritabanı"""
        return {
            'super_lig': {
                'name': 'Süper Lig',
                'country': 'Turkey',
                'api_id': 203,
                'level': 1
            },
            'premier_league': {
                'name': 'Premier League',
                'country': 'England',
                'api_id': 39,
                'level': 1
            },
            'la_liga': {
                'name': 'La Liga',
                'country': 'Spain',
                'api_id': 140,
                'level': 1
            },
            'serie_a': {
                'name': 'Serie A',
                'country': 'Italy',
                'api_id': 135,
                'level': 1
            },
            'bundesliga': {
                'name': 'Bundesliga',
                'country': 'Germany',
                'api_id': 78,
                'level': 1
            },
        }
    
    def _load_football_glossary(self) -> Dict:
        """Futbol terimleri sözlüğü"""
        return {
            'xg': 'Expected Goals - Beklenen Gol metriği. Bir şutun gol olma olasılığını belirtir.',
            'xa': 'Expected Assists - Beklenen asist metriği.',
            'momentum': 'Maç içindeki üstünlük ve enerji akışı. Hangi takımın daha baskın olduğunu gösterir.',
            'btts': 'Both Teams To Score - Her İki Takım Gol Atar',
            'clean_sheet': 'Gol yemeden maç bitirme',
            'possession': 'Top hakimiyeti yüzdesi',
            'pressing': 'Rakip üzerine baskı uygulama',
            'counter_attack': 'Kontra atak - Hızlı karşı hücum',
            'park_the_bus': 'Savunma yapma taktiği - Defansif oyun',
            'tiki_taka': 'Kısa paslarla oyun kurma',
            'false_nine': 'Sahte dokuz - Geri çekilerek oynayan forvet',
            'wingback': 'Kanat bek - Hem savunma hem hücumda görev alan kanat oyuncusu',
            'pressing_trap': 'Baskı tuzağı - Rakibi belirli bölgede kıstırma',
            'gegenpress': 'Top kaybedildikten hemen sonra yoğun baskı',
            'low_block': 'Alçak savunma bloku - Kendi yarı sahasında defansif durma',
            'overload': 'Aşırı yükleme - Sahada belirli bölgeye çok oyuncu yerleştirme',
            'underlap': 'İç geçiş - Oyuncunun içerden koşusu',
            'overlap': 'Dış geçiş - Oyuncunun dışardan koşusu',
            'pivot': 'Pivot - Orta sahanın önündeki tek defansif orta saha',
            'box_to_box': 'Kale kulesi arası koşan, her iki ceza sahasında da etkili olan orta saha oyuncusu',
        }
    
    def find_team(self, query: str) -> Optional[Dict]:
        """Takım ara"""
        query_lower = query.lower().strip()
        
        # Türkçe karakter normalizasyonu
        tr_chars = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
                   'İ': 'i', 'Ğ': 'g', 'Ü': 'u', 'Ş': 's', 'Ö': 'o', 'Ç': 'c'}
        
        for tr_char, en_char in tr_chars.items():
            query_lower = query_lower.replace(tr_char, en_char)
        
        for team_key, team_data in self.teams_db.items():
            # Team key kontrolü
            if query_lower in team_key or team_key in query_lower:
                return team_data
            
            # Alias kontrolü
            for alias in team_data.get('aliases', []):
                if alias.lower() in query_lower or query_lower in alias.lower():
                    return team_data
            
            # Full name kontrolü (normalize edilmiş)
            full_name_normalized = team_data['full_name'].lower()
            for tr_char, en_char in tr_chars.items():
                full_name_normalized = full_name_normalized.replace(tr_char, en_char)
            
            if query_lower in full_name_normalized or full_name_normalized in query_lower:
                return team_data
        
        return None
    
    def find_league(self, query: str) -> Optional[Dict]:
        """Lig ara"""
        query_lower = query.lower().strip()
        
        for league_key, league_data in self.leagues_db.items():
            if query_lower in league_key:
                return league_data
            if query_lower in league_data['name'].lower():
                return league_data
        
        return None


class FootballChatAssistant:
    """AI Futbol Sohbet Asistanı"""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = 'openai'):
        """
        Args:
            api_key: OpenAI veya Gemini API anahtarı
            provider: 'openai' veya 'gemini'
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY') or os.getenv('GEMINI_API_KEY')
        self.provider = provider
        self.knowledge_base = FootballKnowledgeBase()
        self.conversation_history = []
        
        # API client (eğer varsa)
        self.client = None
        if self.api_key and provider == 'openai':
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                print("OpenAI paketi yüklü değil. pip install openai")
        elif self.api_key and provider == 'gemini':
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel('gemini-pro')
            except ImportError:
                print("Gemini paketi yüklü değil. pip install google-generativeai")
    
    def chat(self, user_message: str, context: Optional[Dict] = None) -> str:
        """
        Kullanıcı mesajına cevap ver
        
        Args:
            user_message: Kullanıcı sorusu
            context: Ek bağlam (maç verileri, takım istatistikleri vb.)
            
        Returns:
            AI cevabı
        """
        # Önce rule-based intent detection yap
        intent, entities = self._detect_intent(user_message)
        
        # Eğer basit soruysa, direct cevap ver
        if intent == 'team_info':
            return self._handle_team_info(entities)
        elif intent == 'league_info':
            return self._handle_league_info(entities)
        elif intent == 'glossary':
            return self._handle_glossary(entities)
        elif intent == 'match_prediction':
            return self._handle_match_prediction(entities, context)
        
        # Kompleks sorular için AI kullan
        if self.client:
            return self._ask_ai(user_message, context)
        else:
            return self._fallback_response(user_message, intent, entities)
    
    def _detect_intent(self, message: str) -> Tuple[str, Dict]:
        """Intent ve entity tespiti"""
        message_lower = message.lower()
        entities = {'message': message_lower}
        
        # Takım tespiti
        team = self.knowledge_base.find_team(message_lower)
        if team:
            entities['team'] = team
        
        # Lig tespiti
        league = self.knowledge_base.find_league(message_lower)
        if league:
            entities['league'] = league
        
        # Eğer takım bulunduysa ve bilgi isteniyorsa
        if team and any(word in message_lower for word in ['hakkında', 'hakkinda', 'bilgi', 'nedir', 'anlat']):
            return 'team_info', entities
        
        # Eğer lig bulunduysa ve bilgi isteniyorsa
        if league and any(word in message_lower for word in ['hakkında', 'hakkinda', 'bilgi', 'nedir', 'anlat']):
            return 'league_info', entities
        
        # Intent patterns
        if any(word in message_lower for word in ['nedir', 'ne demek', 'açıkla']):
            # Önce glossary terimlerini kontrol et
            for term in self.knowledge_base.glossary.keys():
                if term in message_lower:
                    entities['term'] = term
                    return 'glossary', entities
        
        if any(word in message_lower for word in ['tahmin', 'kazanır', 'kaybeder', 'beraberlik', 'skor']):
            return 'match_prediction', entities
        
        if any(word in message_lower for word in ['istatistik', 'performans', 'form']):
            return 'statistics', entities
        
        if any(word in message_lower for word in ['analiz', 'değerlendir', 'karşılaştır']):
            return 'analysis', entities
        
        if any(word in message_lower for word in ['yaklaşan', 'gelecek', 'sonraki maç']):
            return 'upcoming_matches', entities
        
        return 'general', entities
    
    def _handle_team_info(self, entities: Dict) -> str:
        """Takım bilgisi ver"""
        team = entities.get('team')
        if not team:
            return "Hangi takım hakkında bilgi istiyorsunuz? Örnek: Galatasaray, Fenerbahçe, Real Madrid"
        
        info = f"""
📊 **{team['full_name']}**

🏆 **Kuruluş:** {team['founded']}
🌍 **Ülke:** {team['country']}
🏟️ **Stadyum:** {team['stadium']}
⚽ **Lig:** {team['league']}
🆔 **API ID:** {team['api_id']}

Bu takım hakkında daha fazla bilgi için sorularınızı sorabilirsiniz!
        """
        return info.strip()
    
    def _handle_league_info(self, entities: Dict) -> str:
        """Lig bilgisi ver"""
        league = entities.get('league')
        if not league:
            return "Hangi lig hakkında bilgi istiyorsunuz?"
        
        info = f"""
🏆 **{league['name']}**

🌍 Ülke: {league['country']}
📊 Seviye: {league['level']}

Bu lig hakkında daha fazla bilgi için sorularınızı sorabilirsiniz!
        """
        return info.strip()
    
    def _handle_glossary(self, entities: Dict) -> str:
        """Futbol terimi açıkla"""
        term = entities.get('term')
        
        if term and term in self.knowledge_base.glossary:
            explanation = self.knowledge_base.glossary[term]
            return f"**{term.upper()}**: {explanation}"
        
        # Eğer term bulunamadıysa message'dan ara
        message_lower = entities.get('message', '').lower()
        for term, explanation in self.knowledge_base.glossary.items():
            if term in message_lower:
                return f"**{term.upper()}**: {explanation}"
        
        return "Bu terim hakkında bilgi bulunamadı. Mevcut terimler: " + ", ".join(self.knowledge_base.glossary.keys())
    
    def _handle_match_prediction(self, entities: Dict, context: Optional[Dict]) -> str:
        """Maç tahmini yap"""
        team = entities.get('team')
        
        if not team and not context:
            return "Maç tahmini için takım ismi belirtin veya maç seçin."
        
        # Basit tahmin
        response = f"""
🎯 **Maç Tahmini Analizi**

Tahmin için daha detaylı analiz yapılıyor...

💡 **Öneriler:**
- xG (Expected Goals) değerlerini kontrol edin
- Son 5 maç formunu inceleyin
- Kafa kafaya istatistikleri gözden geçirin
- Sakatlık/ceza durumlarını değerlendirin

Daha detaylı tahmin için 'Gelişmiş Analiz' sekmesini kullanın.
        """
        return response.strip()
    
    def _ask_ai(self, message: str, context: Optional[Dict]) -> str:
        """AI'ya sor (OpenAI/Gemini)"""
        
        # System prompt
        system_prompt = """
Sen profesyonel bir futbol analisti ve AI asistanısın. 
Futbol maçları, takımlar, istatistikler ve tahminler hakkında uzman bilgiye sahipsin.
Kullanıcılara açık, anlaşılır ve profesyonel cevaplar veriyorsun.
xG, momentum, taktik analiz gibi gelişmiş kavramları açıklayabiliyorsun.
        """
        
        # Context ekle
        context_str = ""
        if context:
            context_str = f"\n\nMevcut Bağlam:\n{json.dumps(context, indent=2, ensure_ascii=False)}"
        
        try:
            if self.provider == 'openai' and self.client:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message + context_str}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif self.provider == 'gemini' and self.client:
                prompt = f"{system_prompt}\n\nKullanıcı: {message}{context_str}"
                response = self.client.generate_content(prompt)
                return response.text
            
        except Exception as e:
            return f"AI hatası: {str(e)}\n\nFallback cevap kullanılıyor..."
        
        return self._fallback_response(message, 'general', {})
    
    def _fallback_response(self, message: str, intent: str, entities: Dict) -> str:
        """AI olmadığında fallback cevap"""
        
        responses = {
            'general': """
İlginç bir soru! Bu konuda size şu bilgileri verebilirim:

📊 Analiz sistemi şu özelliklere sahip:
- xG (Beklenen Gol) hesaplama
- Canlı momentum takibi
- Detaylı istatistiksel analiz
- Takım ve oyuncu performans değerlendirmesi

Daha spesifik sorular sorabilir veya menüden ilgili analiz bölümüne gidebilirsiniz.
            """,
            'statistics': """
📈 İstatistik analizi için:
- Takım istatistikleri sekmesine gidin
- Son maçlar, form grafiği ve detaylı metrikleri inceleyin
- Karşılaştırmalı analiz yapın
            """,
            'analysis': """
🔍 Detaylı analiz için:
- Gelişmiş Analiz sekmesini kullanın
- xG ve Momentum analizlerini inceleyin
- AI tahminlerini kontrol edin
            """
        }
        
        return responses.get(intent, responses['general']).strip()
    
    def get_quick_suggestions(self, current_page: str = 'home') -> List[str]:
        """Hızlı soru önerileri"""
        
        suggestions = {
            'home': [
                "Bugünün en iyi maç tahmini nedir?",
                "xG nedir ve nasıl hesaplanır?",
                "Galatasaray son formu nasıl?",
                "Premier League puan durumu",
            ],
            'match': [
                "Bu maçın kazananını tahmin et",
                "xG analizi göster",
                "Momentum kimde?",
                "Kritik anlar nelerdi?",
            ],
            'team': [
                "Bu takımın güçlü yönleri neler?",
                "Son 5 maç performansı nasıl?",
                "Sakatlık durumu var mı?",
                "Yaklaşan maçlar neler?",
            ]
        }
        
        return suggestions.get(current_page, suggestions['home'])
    
    def add_to_history(self, user_message: str, ai_response: str):
        """Konuşma geçmişine ekle"""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user': user_message,
            'assistant': ai_response
        })
        
        # Son 20 mesajı tut
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def get_conversation_summary(self) -> str:
        """Konuşma özeti"""
        if not self.conversation_history:
            return "Henüz konuşma geçmişi yok."
        
        summary = "📝 **Konuşma Özeti:**\n\n"
        for i, exchange in enumerate(self.conversation_history[-5:], 1):
            summary += f"{i}. Soru: {exchange['user'][:50]}...\n"
        
        return summary


# Streamlit entegrasyonu
def create_chat_widget(assistant: FootballChatAssistant, context: Optional[Dict] = None):
    """Streamlit chat widget"""
    import streamlit as st
    
    st.markdown("### 💬 AI Futbol Asistanı")
    
    # Hızlı öneriler
    st.markdown("#### 🎯 Hızlı Sorular")
    suggestions = assistant.get_quick_suggestions()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(suggestions[0], use_container_width=True, key="sug1"):
            st.session_state.user_input = suggestions[0]
    with col2:
        if st.button(suggestions[1], use_container_width=True, key="sug2"):
            st.session_state.user_input = suggestions[1]
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button(suggestions[2], use_container_width=True, key="sug3"):
            st.session_state.user_input = suggestions[2]
    with col4:
        if st.button(suggestions[3], use_container_width=True, key="sug4"):
            st.session_state.user_input = suggestions[3]
    
    st.markdown("---")
    
    # Input
    user_input = st.text_input(
        "Sorunuzu yazın:", 
        placeholder="Örn: Galatasaray hakkında bilgi ver",
        key="chat_input",
        value=st.session_state.get('user_input', '')
    )
    
    # Temizle
    if 'user_input' in st.session_state:
        del st.session_state.user_input
    
    # Gönder butonu
    if st.button("📤 Gönder", type="primary", use_container_width=True) and user_input:
        with st.spinner("AI düşünüyor..."):
            response = assistant.chat(user_input, context)
            assistant.add_to_history(user_input, response)
        
        # Cevabı göster
        st.markdown("---")
        st.markdown(f"**👤 Siz:** {user_input}")
        st.markdown(f"**🤖 AI Asistan:**\n\n{response}")
        st.markdown("---")
    
    # Geçmiş konuşmalar
    if assistant.conversation_history:
        with st.expander("📜 Konuşma Geçmişi", expanded=False):
            for i, exchange in enumerate(reversed(assistant.conversation_history[-5:]), 1):
                st.markdown(f"**{i}. Soru:** {exchange['user']}")
                st.markdown(f"**Cevap:** {exchange['assistant'][:300]}...")
                st.markdown("---")


# Demo
if __name__ == "__main__":
    # API key olmadan test
    assistant = FootballChatAssistant()
    
    print("🤖 AI Futbol Asistanı Test")
    print("=" * 50)
    
    test_questions = [
        "Galatasaray hakkında bilgi ver",
        "xG nedir?",
        "Fenerbahçe Galatasaray maçını kim kazanır?",
    ]
    
    for question in test_questions:
        print(f"\n❓ Soru: {question}")
        response = assistant.chat(question)
        print(f"🤖 Cevap: {response}")
        print("-" * 50)
