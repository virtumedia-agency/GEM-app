import os
import pandas as pd
from datetime import date
from typing import Dict

class Reporter:
    def __init__(self, output_dir: str = "app/reports"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate_report_content(self, decision: Dict, analysis_date: pd.Timestamp, tickers_map: Dict[str, str]) -> str:
        """
        Generates the Markdown content for the report.
        """
        mode = decision['mode']
        selected = decision['selected_asset_key']
        ticker = decision['selected_ticker']
        mom = decision['momentum']
        
        # Formatting percentages
        fmt_pct = lambda x: f"{x:.2%}"
        
        # Determine signals
        us_signal = "BUY" if selected == "US" else "HOLD/SELL"
        exus_signal = "BUY" if selected == "EXUS" else "HOLD/SELL"
        bonds_signal = "BUY" if selected == "BONDS" else "HOLD/SELL"
        
        # Build Markdown
        report = f"""# GEM ETF – Decyzja za {analysis_date.strftime('%Y-%m')}

**Data analizy (punkt pomiaru):** {analysis_date.strftime('%Y-%m-%d')}
**Decyzja:** **{selected}** ({ticker})
**Tryb:** **{mode}**

---

## 1. Rekomendacja
Na podstawie danych z zamknięcia miesiąca, strategia GEM wskazuje, aby w nadchodzącym miesiącu ulokować kapitał w:
# **{ticker}** ({selected})

## 2. Uzasadnienie (Logika GEM)
1. **Analiza Rynku (US vs Cash):**
   - Zwrot US (S&P 500): {fmt_pct(mom['US'])}
   - Zwrot Cash (T-Bills): {fmt_pct(mom['CASH_PROXY'])}
   - **Wynik:** {"Rynek silniejszy od gotówki (RISK-ON)" if mom['US'] > mom['CASH_PROXY'] else "Rynek słabszy od gotówki (RISK-OFF)"}

2. **Wybór Aktywa:**
   {'Ponieważ jesteśmy w trybie RISK-ON, wybieramy silniejszy rynek akcji:' if mode == 'RISK-ON' else 'Ponieważ jesteśmy w trybie RISK-OFF, uciekamy w bezpieczne obligacje:'}
   - US Momentum: {fmt_pct(mom['US'])}
   - EXUS Momentum: {fmt_pct(mom['EXUS'])}
   - **Wybrano:** {selected} (Najwyższy wynik)

---

## 3. Tabela Wyników (12 Miesięcy)

| Klasa | Ticker | Zwrot 12M | Decyzja |
|-------|--------|-----------|---------|
| US Equities | {tickers_map['US']} | {fmt_pct(mom['US'])} | {us_signal if mode == 'RISK-ON' else '-'} |
| Int'l Equities | {tickers_map['EXUS']} | {fmt_pct(mom['EXUS'])} | {exus_signal if mode == 'RISK-ON' else '-'} |
| Bonds | {tickers_map['BONDS']} | {fmt_pct(mom['BONDS'])} | {bonds_signal if mode == 'RISK-OFF' else '-'} |
| Cash Proxy | {tickers_map['CASH_PROXY']} | {fmt_pct(mom['CASH_PROXY'])} | (Benchmark) |

---
*Wygenerowano automatycznie przez GEM ETF Decision App.*
"""
        return report

    def save_report(self, content: str, date_str: str) -> str:
        """
        Saves the report to disk.
        """
        filename = f"{date_str}.md"
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path
