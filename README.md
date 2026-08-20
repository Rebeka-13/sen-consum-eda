# ⚡ EDA – Consum Sistem Energetic Național (SEN)

Aplicație interactivă (Streamlit) pentru analiza exploratorie a consumului
și producției de energie electrică din România.

## 📁 Fișiere din proiect

| Fișier                 | Rol                               |
| ---------------------- | --------------------------------- |
| `sen_eda_dashboard.py` | Codul aplicației (Streamlit)      |
| `requirements.txt`     | Lista de librării Python necesare |
| `README.md`            | Acest fișier                      |

Aplicația **nu are nevoie de alt fișier de date inclus în proiect** — datele
se încarcă manual din interfață, la fiecare rulare, printr-un fișier Excel.

## ▶️ Cum se pornește aplicația

1. Instalează librăriile necesare (o singură dată, sau ori de câte ori se
   schimbă `requirements.txt`):

   ```bash
   pip install -r requirements.txt
   ```

2. Pornește aplicația:

   ```bash
   streamlit run sen_consum_eda.py
   ```

3. Se deschide automat în browser (de obicei la `http://localhost:8501`).

## 📊 Cum se folosește

1. În bara laterală (sidebar), la secțiunea **📂 Date**, încarcă fișierul
   Excel cu observațiile (`.xlsx` sau `.xls`).
2. Aplicația detectează automat coloanele relevante după numele lor
   (nu contează ordinea coloanelor sau ordinea cronologică a rândurilor —
   datele sunt sortate automat după dată/oră după încărcare).
3. Coloane minim necesare:
   - o coloană de tip dată/oră (`Data`, `DataOra`, `Timestamp`, etc.)
   - o coloană de consum (`Consum[MW]`, `Consum`, etc.)
4. Coloane opționale, folosite dacă există:
   - `Medie Orară Consum` — pentru secțiunea 5 (zgomot intraorar)
   - `Temperatură` — pentru secțiunea 6 (sensibilitate la temperatură)
   - restul coloanelor de producție (Cărbune, Hidrocarburi, Ape, Nuclear,
     Eolian, Foto, Biomasă, Sold) nu sunt obligatorii pentru EDA de consum.
5. (Opțional) În sidebar, la **🎉 Sărbători**, poți dezactiva sărbătorile
   legale fixe (precompletate automat) sau adăuga manual sărbători cu
   dată variabilă (Paște, Rusalii) ori alte zile speciale.
6. Aplicația generează automat:
   1. Curba de sarcină tipică pe 24h + analiza unei zile alese din calendar
   2. Raportul vârf/gol zilnic și variația lui în timp
   3. Profilul de consum: zi lucrătoare vs. weekend vs. sărbătoare
   4. Ora vârfului de seară și cum se deplasează pe sezoane
   5. Diferența dintre consumul instantaneu și media orară (zgomot)
   6. Corelația consum–temperatură
