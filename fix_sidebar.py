# Sidebar butonlarını düzelt
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 5765-5793 satırları arasını değiştir (0-indexed: 5764-5792)
new_lines = [
    '\n',
    '        # Üçüncü sıra navigasyon butonları\n',
    '        nav_col9, nav_col10, nav_col11, nav_col12 = st.sidebar.columns(4)\n',
    '        with nav_col9:\n',
    '            if st.button("🤖", use_container_width=True, key="nav_ai_chat", help="AI Asistan"):\n',
    '                update_url_and_rerun(\'ai_chat\')\n',
    '        with nav_col10:\n',
    '            if st.button("📊", use_container_width=True, key="nav_momentum", help="Momentum"):\n',
    '                update_url_and_rerun(\'momentum\')\n',
    '        with nav_col11:\n',
    '            if st.button("🧠", use_container_width=True, key="nav_lstm", help="LSTM Tahmin"):\n',
    '                update_url_and_rerun(\'lstm_predict\')\n',
    '        with nav_col12:\n',
    '            if st.button("🎲", use_container_width=True, key="nav_monte_carlo", help="Monte Carlo"):\n',
    '                update_url_and_rerun(\'monte_carlo\')\n',
    '        \n',
    '        # Dördüncü sıra navigasyon butonları\n',
    '        nav_col13, nav_col14, nav_col15, nav_col16 = st.sidebar.columns(4)\n',
    '        with nav_col13:\n',
    '            if st.button("💎", use_container_width=True, key="nav_value_bets", help="Value Bet"):\n',
    '                update_url_and_rerun(\'value_bets\')\n',
    '        with nav_col14:\n',
    '            st.empty()\n',
    '        with nav_col15:\n',
    '            st.empty()\n',
    '        with nav_col16:\n',
    '            st.empty()\n',
    '        \n',
]

lines[5764:5793] = new_lines

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Sidebar düzeltildi!")
print(f"📝 Toplam {len(lines)} satır")
