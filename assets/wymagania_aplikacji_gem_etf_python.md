# Wymagania produktu (PRD)

## Nazwa
**GEM ETF Decision App (Python)**

## 1. Cel produktu
Celem aplikacji jest automatyczne, comiesięczne generowanie decyzji inwestycyjnej zgodnie ze strategią **GEM (Global Equity Momentum / Dual Momentum)** dla wybranych ETF-ów oraz wysyłka czytelnego podsumowania e‑mail **w pierwszy poniedziałek miesiąca**.

Aplikacja **nie składa zleceń** – dostarcza wyłącznie rekomendację: *w co wejść / z czego wyjść* wraz z uzasadnieniem.

---

## 2. Zakres MVP

### MVP zawiera
- Harmonogram uruchomienia: **pierwszy poniedziałek miesiąca**.
- Pobranie danych historycznych ETF-ów.
- Obliczenie momentum (domyślnie **12 miesięcy**).
- Decyzję GEM (risk-on / risk-off + rotacja).
- Generację raportu tekstowego.
- **Wysyłkę e‑mail z podsumowaniem przez Resend**.
- Zapis historii decyzji.

### MVP nie zawiera
- Integracji z brokerem.
- Automatycznych transakcji.
- Obsługi podatków, FX i kosztów transakcyjnych.

---

## 3. Użytkownik i potrzeby

**Persona:** inwestor długoterminowy, który chce raz w miesiącu otrzymać jednoznaczną decyzję inwestycyjną.

**Potrzeby:**
- jasna rekomendacja BUY / HOLD / SELL,
- transparentne uzasadnienie (dane + reguła),
- pełna automatyzacja bez ręcznego liczenia.

---

## 4. Strategia inwestycyjna (GEM – opis produktowy)

### Koszyk aktywów (konfigurowalny)
- **US** – ETF na rynek USA (np. S&P 500)
- **EXUS** – ETF na rynki akcji poza USA
- **BONDS** – ETF na obligacje (aggregate)
- **CASH_PROXY** – proxy gotówki (np. T‑Bills / money market)

### Punkt pomiaru
- Dane liczone są na podstawie **ostatniej sesji giełdowej poprzedniego miesiąca**.
- Uruchomienie następuje w pierwszy poniedziałek, ale zawsze bazuje na „month‑end close”.

### Reguły decyzyjne
1. Oblicz 12‑miesięczną stopę zwrotu **US** oraz **CASH_PROXY**.
2. Jeśli `US <= CASH_PROXY` → **RISK‑OFF** → wybierz **BONDS**.
3. Jeśli `US > CASH_PROXY` → **RISK‑ON** → wybierz aktywo o wyższym momentum z (**US**, **EXUS**).

Decyzja obowiązuje przez cały kolejny miesiąc.

---

## 5. Wymagania funkcjonalne (FR)

### FR‑01 Harmonogram
- Aplikacja uruchamia się automatycznie **w pierwszy poniedziałek miesiąca**.
- Godzina uruchomienia konfigurowalna (domyślnie 09:00 CET).

### FR‑02 Konfiguracja
- Konfiguracja przez `config.yaml` + zmienne środowiskowe.
- Parametry:
  - tickery ETF‑ów,
  - długość lookback (domyślnie 12M),
  - źródło danych,
  - konfiguracja e‑mail.

### FR‑03 Kalendarz sesji
- Aplikacja identyfikuje **ostatnią sesję poprzedniego miesiąca**.
- Jeśli brak danych dla danej sesji – cofa się do najbliższej wcześniejszej sesji.

### FR‑04 Pobieranie danych
- Pobranie danych cenowych dla wszystkich ETF‑ów.
- Wykorzystanie **cen skorygowanych (adjusted)** – dywidendy i splity uwzględnione.

### FR‑05 Obliczenia
- Wyliczenie 12‑miesięcznych stóp zwrotu dla:
  - US
  - EXUS
  - CASH_PROXY
- Wyznaczenie trybu: risk‑on / risk‑off.
- Wybór aktywa docelowego.

### FR‑06 Raport
- Generacja raportu tekstowego (Markdown / TXT).
- Raport zawiera:
  - datę uruchomienia,
  - punkt pomiaru,
  - wyniki momentum,
  - decyzję,
  - zmianę względem poprzedniego miesiąca.
- Zapis raportu do katalogu `reports/YYYY‑MM.md`.

### FR‑07 Wysyłka e‑mail (Resend)

#### FR‑07.1 Ogólne
- Po każdym uruchomieniu aplikacja **musi wysłać e‑mail z podsumowaniem decyzji**.
- Dostawca e‑mail: **Resend**.

#### FR‑07.2 Autoryzacja
- Klucz API przekazywany jako zmienna środowiskowa:
  - `RESEND_API_KEY`
- Nadawca (`from`) musi być adresem na **zweryfikowanej domenie**.

#### FR‑07.3 Treść e‑maila
- Temat (przykład):
  - `GEM ETF – decyzja za 2026‑01 (RISK‑ON)`
- Treść zawiera:
  - wybrane aktywo,
  - BUY / HOLD / SELL,
  - stopy zwrotu 12M,
  - krótkie uzasadnienie decyzji,
  - informację, z czego należy wyjść (jeśli dotyczy).

#### FR‑07.4 Obsługa błędów
- W przypadku błędu wysyłki:
  - raport lokalny **musi zostać zapisany**,
  - błąd logowany w systemie.

### FR‑08 Historia decyzji
- Zapis historii do `decisions.csv`:
  - miesiąc
  - wybrane aktywo
  - tryb (risk‑on / risk‑off)
  - momentum
  - timestamp

---

## 6. Wymagania niefunkcjonalne (NFR)

- **NFR‑01 Determinizm** – te same dane wejściowe → ten sam wynik.
- **NFR‑02 Odporność** – aplikacja działa mimo braków danych.
- **NFR‑03 Logowanie** – logi do `logs/app.log`.
- **NFR‑04 Bezpieczeństwo** – brak sekretów w repozytorium.
- **NFR‑05 Przenośność** – uruchomienie lokalne + możliwość dockeryzacji.

---

## 7. Architektura techniczna (propozycja)

```
app/
├── main.py
├── config/
│   └── config.yaml
├── data_provider.py
├── market_calendar.py
├── strategy_gem.py
├── reporter.py
├── email_resend.py
├── storage.py
├── reports/
├── logs/
└── decisions.csv
```

---

## 8. Kryteria akceptacji (AC)

- **AC‑01** Aplikacja uruchamia się w pierwszy poniedziałek miesiąca.
- **AC‑02** Decyzja oparta jest o dane z końca poprzedniego miesiąca.
- **AC‑03** Strategia poprawnie rozróżnia risk‑on / risk‑off.
- **AC‑04** Raport zapisuje się lokalnie.
- **AC‑05** Po każdym uruchomieniu wysyłany jest e‑mail przez Resend.
- **AC‑06** Historia decyzji jest zapisywana i możliwa do odczytu.

---

## 9. Otwarte kwestie (do dalszych iteracji)
- Wagi portfela (100% vs podział).
- Backtest historyczny.
- Dashboard webowy.
- Integracja z brokerem (read‑only / trading).

