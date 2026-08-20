import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re


# ============================================================
# CONFIGURARE
# ============================================================

st.set_page_config(
    page_title="EDA - Consum",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ EDA – Consum")
st.markdown(
    """
    Aplicație interactivă pentru analiza consumului și producției
    de energie electrică.
    """
)


# ============================================================
# FUNCȚII
# ============================================================

def clean_column_name(col):
    """Curăță numele coloanelor."""
    col = str(col).strip()
    col = re.sub(r"\s+", " ", col)
    return col


def find_column(columns, keywords):
    """
    Caută automat o coloană după cuvinte-cheie.
    Nu depinde de numele exact al coloanei.
    """
    columns_lower = {str(c).lower(): c for c in columns}

    # întâi căutare exactă
    for keyword in keywords:
        for lower_col, original_col in columns_lower.items():
            if keyword.lower() == lower_col:
                return original_col

    # apoi căutare parțială
    for keyword in keywords:
        for lower_col, original_col in columns_lower.items():
            if keyword.lower() in lower_col:
                return original_col

    return None


def detect_columns(df):
    """Detectează automat coloanele importante."""

    columns = df.columns

    date_col = find_column(
        columns,
        ["data", "date", "datetime", "timestamp"]
    )

    consum_col = find_column(
        columns,
        ["consum[mw]", "consum", "consumption"]
    )

    hourly_col = find_column(
        columns,
        [
            "medie orara consum",
            "medie consum",
            "medie orară consum",
            "average consumption"
        ]
    )

    temp_col = find_column(
        columns,
        ["temperatura", "temperatură", "temp", "temperature"]
    )

    return date_col, consum_col, hourly_col, temp_col


def season(month):
    """Împarte anul în anotimpuri."""
    if month in [12, 1, 2]:
        return "Iarnă"
    elif month in [3, 4, 5]:
        return "Primăvară"
    elif month in [6, 7, 8]:
        return "Vară"
    else:
        return "Toamnă"


def add_time_features(df):
    """Adaugă caracteristicile temporale necesare analizei."""

    df = df.copy()

    df["DataOra"] = pd.to_datetime(
        df["DataOra"],
        errors="coerce",
        dayfirst=True
    )

    df = df.dropna(subset=["DataOra"])

    df["Data"] = df["DataOra"].dt.date
    df["Ora"] = df["DataOra"].dt.hour
    df["Luna"] = df["DataOra"].dt.month
    df["An"] = df["DataOra"].dt.year
    df["ZiSaptamana"] = df["DataOra"].dt.dayofweek

    df["Zi"] = df["DataOra"].dt.day_name()

    df["TipZi"] = np.where(
        df["ZiSaptamana"] >= 5,
        "Weekend",
        "Lucrătoare"
    )

    df["Sezon"] = df["Luna"].apply(season)

    return df


# ============================================================
# UPLOAD EXCEL
# ============================================================

st.sidebar.header("📂 Date")

uploaded_file = st.sidebar.file_uploader(
    "Încarcă fișierul Excel",
    type=["xlsx", "xls"]
)

if uploaded_file is None:
    st.info(
        "Încarcă fișierul Excel pentru a începe analiza."
    )

    st.markdown(
        """
        **Structura recomandată a Excelului:**

        - `Data`
        - `Consum[MW]`
        - `Medie Consum[...]`
        - `Productie[MW]`
        - `Carbune[MW]`
        - `Hidrocarburi[MW]`
        - `Ape[MW]`
        - `Nuclear[MW]`
        - `Eolian[MW]`
        - `Foto[MW]`
        - `Biomasa[MW]`
        - `Sold[MW]`

        Coloanele de producție sunt opționale pentru această
        secțiune de EDA. Pentru analiza consumului este suficient
        să existe data și consumul.
        """
    )

    st.stop()


# ============================================================
# CITIRE DATE
# ============================================================

try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Nu am putut citi fișierul Excel: {e}")
    st.stop()


df.columns = [clean_column_name(c) for c in df.columns]

date_col, consum_col, hourly_col, temp_col = detect_columns(df)


# ============================================================
# VERIFICARE COLOANE
# ============================================================

if date_col is None:
    st.error(
        "Nu am găsit coloana pentru dată/oră. "
        "Este necesară o coloană de tip «Data»."
    )
    st.stop()

if consum_col is None:
    st.error(
        "Nu am găsit coloana «Consum»."
    )
    st.stop()


# Redenumim intern coloanele.
# Astfel restul codului nu depinde de numele exact din Excel.

df = df.rename(
    columns={
        date_col: "DataOra",
        consum_col: "Consum"
    }
)

if hourly_col is not None:
    df = df.rename(columns={hourly_col: "MedieOraraConsum"})

if temp_col is not None:
    df = df.rename(columns={temp_col: "Temperatura"})


# ============================================================
# CONVERSIE NUMERICĂ
# ============================================================

df["Consum"] = pd.to_numeric(
    df["Consum"],
    errors="coerce"
)

if "MedieOraraConsum" in df.columns:
    df["MedieOraraConsum"] = pd.to_numeric(
        df["MedieOraraConsum"],
        errors="coerce"
    )

if "Temperatura" in df.columns:
    df["Temperatura"] = pd.to_numeric(
        df["Temperatura"],
        errors="coerce"
    )


df = add_time_features(df)

df = df.dropna(subset=["Consum"])

df = df.sort_values("DataOra")

# Elimină înregistrările duplicate (același DataOra apare de mai multe
# ori în unele exporturi, cu valori identice) — altfel se dublează
# ponderea acelor observații în medii/histograme.
df = df.drop_duplicates(subset="DataOra", keep="first")


# ============================================================
# INFORMAȚII DESPRE DATASET
# ============================================================

min_date = df["DataOra"].min()
max_date = df["DataOra"].max()

nr_zile = df["Data"].nunique()
nr_observatii = len(df)


# ============================================================
# SIDEBAR - INFORMAȚII
# ============================================================

st.sidebar.markdown("---")

st.sidebar.write("### 📊 Dataset")

st.sidebar.write(
    f"**De la:** {min_date:%d-%m-%Y %H:%M}"
)

st.sidebar.write(
    f"**Până la:** {max_date:%d-%m-%Y %H:%M}"
)

st.sidebar.write(
    f"**Zile:** {nr_zile:,}"
)

st.sidebar.write(
    f"**Observații:** {nr_observatii:,}"
)


# ============================================================
# SĂRBĂTORI
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("🎉 Sărbători")

# Sărbători legale fixe (lună, zi) — se aplică automat pentru
# fiecare an prezent în dataset, fără să mai fie nevoie să le scrii.
SARBATORI_FIXE = [
    (1, 1, "Anul Nou"),
    (1, 2, "Anul Nou"),
    (1, 24, "Ziua Unirii"),
    (5, 1, "Ziua Muncii"),
    (6, 1, "Ziua Copilului"),
    (8, 15, "Adormirea Maicii Domnului"),
    (11, 30, "Sf. Andrei"),
    (12, 1, "Ziua Națională"),
    (12, 25, "Crăciun"),
    (12, 26, "Crăciun"),
]

ani_din_date = sorted(df["An"].unique())

holiday_dates = set()

for an in ani_din_date:
    for luna, zi, _nume in SARBATORI_FIXE:
        try:
            holiday_dates.add(pd.Timestamp(year=an, month=luna, day=zi).date())
        except ValueError:
            pass

use_fixed_holidays = st.sidebar.checkbox(
    "Include sărbătorile legale fixe (Crăciun, 1 mai, etc.)",
    value=True
)

if not use_fixed_holidays:
    holiday_dates = set()

st.sidebar.caption(
    "Sărbătorile cu dată variabilă (Paște, Rusalii) nu pot fi "
    "calculate automat — adaugă-le mai jos, separate prin virgulă. "
    "Exemplu: 20-04-2025, 21-04-2025"
)

holiday_text = st.sidebar.text_input(
    "Alte sărbători / date speciale",
    value=""
)

if holiday_text.strip():

    for value in holiday_text.split(","):

        try:
            d = pd.to_datetime(
                value.strip(),
                dayfirst=True
            ).date()

            holiday_dates.add(d)

        except Exception:
            pass


df["TipZi"] = np.where(
    df["Data"].isin(holiday_dates),
    "Sărbătoare",
    np.where(
        df["ZiSaptamana"] >= 5,
        "Weekend",
        "Lucrătoare"
    )
)


# ============================================================
# TITLU
# ============================================================

st.subheader("📊 Privire generală")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Consum mediu",
        f"{df['Consum'].mean():,.0f} MW"
    )

with col2:
    st.metric(
        "Consum minim",
        f"{df['Consum'].min():,.0f} MW"
    )

with col3:
    st.metric(
        "Consum maxim",
        f"{df['Consum'].max():,.0f} MW"
    )

with col4:
    st.metric(
        "Zile analizate",
        f"{nr_zile:,}"
    )


# ============================================================
# 1. CURBA DE SARCINĂ
# ============================================================

st.header("1️⃣ Curba de sarcină tipică pe o zi")

st.markdown(
    """
    Curba tipică este calculată ca **media consumului pentru fiecare
    oră a zilei**, folosind toate zilele disponibile.
    """
)


# Profil mediu pe ore
profil_orar = (
    df.groupby("Ora")["Consum"]
    .mean()
    .reset_index()
)

fig = px.line(
    profil_orar,
    x="Ora",
    y="Consum",
    markers=True,
    title="Profilul mediu al consumului pe 24 de ore"
)

fig.update_xaxes(
    dtick=1,
    title="Ora"
)

fig.update_yaxes(
    title="Consum mediu (MW)"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ------------------------------------------------------------
# VÂRFURI
# ------------------------------------------------------------

col1, col2, col3 = st.columns(3)

# Noapte: 00-06 (conform glosarului, golul e tipic ~02-05)
noapte = profil_orar[
    profil_orar["Ora"].between(0, 6)
]

if not noapte.empty:
    min_row = noapte.loc[
        noapte["Consum"].idxmin()
    ]
else:
    min_row = profil_orar.loc[
        profil_orar["Consum"].idxmin()
    ]

max_row = profil_orar.loc[
    profil_orar["Consum"].idxmax()
]

# Dimineața: 05-11
dimineata = profil_orar[
    profil_orar["Ora"].between(5, 11)
]

# Seara: 17-23
seara = profil_orar[
    profil_orar["Ora"].between(17, 23)
]

if not dimineata.empty:
    peak_morning = dimineata.loc[
        dimineata["Consum"].idxmax()
    ]
else:
    peak_morning = None

if not seara.empty:
    peak_evening = seara.loc[
        seara["Consum"].idxmax()
    ]
else:
    peak_evening = None


with col1:
    st.metric(
        "🌙 Gol de noapte",
        f"{min_row['Consum']:,.0f} MW",
        f"ora {int(min_row['Ora']):02d}:00"
    )

with col2:
    if peak_morning is not None:
        st.metric(
            "🌅 Vârf de dimineață",
            f"{peak_morning['Consum']:,.0f} MW",
            f"ora {int(peak_morning['Ora']):02d}:00"
        )

with col3:
    if peak_evening is not None:
        st.metric(
            "🌆 Vârf de seară",
            f"{peak_evening['Consum']:,.0f} MW",
            f"ora {int(peak_evening['Ora']):02d}:00"
        )


# ============================================================
# ZI ALEASĂ
# ============================================================

st.subheader("🔎 Analiza unei zile")

available_dates = sorted(df["Data"].unique())

selected_date = st.date_input(
    "Alege ziua pe care vrei să o analizezi:",
    value=available_dates[-1],
    min_value=available_dates[0],
    max_value=available_dates[-1]
)

if selected_date not in df["Data"].values:
    st.warning(
        "Nu există observații pentru data selectată în dataset."
    )


day_df = df[
    df["Data"] == selected_date
].copy()


if not day_df.empty:

    fig_day = px.line(
        day_df,
        x="DataOra",
        y="Consum",
        markers=True,
        title=f"Consum în data de {selected_date.strftime('%d-%m-%Y')}"
    )

    fig_day.update_xaxes(
        title="Ora"
    )

    fig_day.update_yaxes(
        title="Consum (MW)"
    )

    st.plotly_chart(
        fig_day,
        use_container_width=True
    )


    # MINIM / MAXIM ZILNIC

    min_day = day_df.loc[
        day_df["Consum"].idxmin()
    ]

    max_day = day_df.loc[
        day_df["Consum"].idxmax()
    ]

    ratio = (
        max_day["Consum"] /
        min_day["Consum"]
        if min_day["Consum"] != 0
        else np.nan
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Consum minim",
            f"{min_day['Consum']:,.0f} MW",
            f"{min_day['DataOra']:%H:%M:%S}"
        )

    with c2:
        st.metric(
            "Consum maxim",
            f"{max_day['Consum']:,.0f} MW",
            f"{max_day['DataOra']:%H:%M:%S}"
        )

    with c3:
        st.metric(
            "Raport vârf / gol",
            f"{ratio:.2f}"
        )


# ============================================================
# 2. RAPORT VÂRF / GOL
# ============================================================

st.header("2️⃣ Raportul vârf / gol intrazilnic")

st.markdown(
    """
    Pentru fiecare zi calculăm raportul dintre consumul maxim și
    consumul minim din ziua respectivă.
    """
)


daily_stats = (
    df.groupby("Data")["Consum"]
    .agg(
        ConsumMinim="min",
        ConsumMaxim="max"
    )
    .reset_index()
)

daily_stats["RaportVarfGol"] = (
    daily_stats["ConsumMaxim"] /
    daily_stats["ConsumMinim"]
)


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Raport mediu",
        f"{daily_stats['RaportVarfGol'].mean():.2f}"
    )

with col2:
    st.metric(
        "Raport median",
        f"{daily_stats['RaportVarfGol'].median():.2f}"
    )

with col3:
    st.metric(
        "Raport minim",
        f"{daily_stats['RaportVarfGol'].min():.2f}"
    )

with col4:
    st.metric(
        "Raport maxim",
        f"{daily_stats['RaportVarfGol'].max():.2f}"
    )


fig_ratio = px.line(
    daily_stats,
    x="Data",
    y="RaportVarfGol",
    title="Variația zilnică a raportului vârf / gol"
)

fig_ratio.update_yaxes(
    title="Raport vârf / gol"
)

st.plotly_chart(
    fig_ratio,
    use_container_width=True
)


# ============================================================
# 3. LUCRĂTOARE VS WEEKEND VS SĂRBĂTORI
# ============================================================

st.header("3️⃣ Zile lucrătoare vs weekend vs sărbători")

profile_day_type = (
    df.groupby(["TipZi", "Ora"])["Consum"]
    .mean()
    .reset_index()
)

fig_types = px.line(
    profile_day_type,
    x="Ora",
    y="Consum",
    color="TipZi",
    markers=True,
    title="Profilul mediu al consumului în funcție de tipul zilei"
)

fig_types.update_xaxes(
    dtick=1,
    title="Ora"
)

fig_types.update_yaxes(
    title="Consum mediu (MW)"
)

st.plotly_chart(
    fig_types,
    use_container_width=True
)


# ============================================================
# 4. VÂRFUL DE SEARĂ ȘI SEZONALITATE
# ============================================================

st.header("4️⃣ Vârful de seară și sezonalitatea")

st.markdown(
    """
    Considerăm intervalul 17:00–23:00 drept interval de seară.
    Pentru fiecare zi identificăm ora la care consumul este maxim
    în acest interval.
    """
)


evening_df = df[
    df["Ora"].between(17, 23)
].copy()


if not evening_df.empty:

    evening_peak = (
        evening_df
        .loc[
            evening_df.groupby("Data")["Consum"].idxmax()
        ]
        [["Data", "DataOra", "Ora", "Consum", "Sezon"]]
        .copy()
    )


    # Distribuția orelor de vârf
    # (bar pe valori exacte de oră, nu histogram cu nbins — cu doar
    # 7 valori întregi posibile (17-23), nbins=7 plasează marginile
    # binurilor între ore și amestecă zilele în binul greșit)
    ore_counts = (
        evening_peak["Ora"]
        .value_counts()
        .reindex(range(17, 24), fill_value=0)
        .reset_index()
    )
    ore_counts.columns = ["Ora", "NumarZile"]

    fig_peak = px.bar(
        ore_counts,
        x="Ora",
        y="NumarZile",
        title="Distribuția orei vârfului de seară"
    )

    fig_peak.update_xaxes(
        dtick=1,
        title="Ora vârfului de seară"
    )

    fig_peak.update_yaxes(
        title="Număr de zile"
    )

    st.plotly_chart(
        fig_peak,
        use_container_width=True
    )


    # Sezon
    seasonal_peak = (
        evening_peak
        .groupby("Sezon")["Ora"]
        .agg(
            OraMedie="mean",
            OraMediana="median"
        )
        .reset_index()
    )

    st.subheader("Ora medie a vârfului de seară pe sezon")

    st.dataframe(
        seasonal_peak,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 5. CONSUM VS MEDIE ORARĂ
# ============================================================

st.header("5️⃣ Consum instantaneu vs Medie Orară Consum")


if "MedieOraraConsum" not in df.columns:

    st.warning(
        "Nu am găsit o coloană de tip «Medie Orară Consum» "
        "în fișierul încărcat."
    )

else:

    df["Diferenta"] = (
        df["Consum"] -
        df["MedieOraraConsum"]
    )

    df["DiferentaAbsoluta"] = (
        df["Diferenta"].abs()
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Diferență medie",
            f"{df['Diferenta'].mean():,.1f} MW"
        )

    with col2:
        st.metric(
            "Diferență absolută medie",
            f"{df['DiferentaAbsoluta'].mean():,.1f} MW"
        )

    with col3:
        st.metric(
            "Deviație standard",
            f"{df['Diferenta'].std():,.1f} MW"
        )

    with col4:
        st.metric(
            "Diferență maximă absolută",
            f"{df['DiferentaAbsoluta'].max():,.1f} MW"
        )


    fig_noise = px.histogram(
        df,
        x="Diferenta",
        nbins=60,
        title="Distribuția diferenței Consum - Medie Orară Consum"
    )

    fig_noise.update_xaxes(
        title="Diferență (MW)"
    )

    fig_noise.update_yaxes(
        title="Număr de observații"
    )

    st.plotly_chart(
        fig_noise,
        use_container_width=True
    )


# ============================================================
# 6. TEMPERATURĂ VS CONSUM
# ============================================================

st.header("6️⃣ Sensibilitatea consumului la temperatură")


if "Temperatura" not in df.columns:

    st.info(
        "În fișierul încărcat nu există o coloană de temperatură. "
        "Pentru această analiză trebuie adăugată temperatura "
        "corespunzătoare fiecărei date/ore."
    )

else:

    temp_df = df[
        ["Temperatura", "Consum"]
    ].dropna()


    if len(temp_df) >= 10:

        # Corelație Pearson
        correlation = temp_df[
            "Temperatura"
        ].corr(
            temp_df["Consum"]
        )

        st.metric(
            "Corelație Pearson temperatură - consum",
            f"{correlation:.3f}"
        )


        fig_temp = px.scatter(
            temp_df,
            x="Temperatura",
            y="Consum",
            opacity=0.35,
            trendline="ols",
            title="Relația dintre temperatură și consum"
        )

        fig_temp.update_xaxes(
            title="Temperatură"
        )

        fig_temp.update_yaxes(
            title="Consum (MW)"
        )

        st.plotly_chart(
            fig_temp,
            use_container_width=True
        )


        # Grupare pe intervale de temperatură
        temp_df["IntervalTemperatura"] = pd.cut(
            temp_df["Temperatura"],
            bins=10
        )

        temp_profile = (
            temp_df
            .groupby(
                "IntervalTemperatura",
                observed=True
            )["Consum"]
            .mean()
            .reset_index()
        )

        fig_temp_profile = px.line(
            temp_profile,
            x="IntervalTemperatura",
            y="Consum",
            markers=True,
            title="Consum mediu în funcție de intervalul de temperatură"
        )

        fig_temp_profile.update_xaxes(
            title="Interval temperatură"
        )

        fig_temp_profile.update_yaxes(
            title="Consum mediu (MW)"
        )

        st.plotly_chart(
            fig_temp_profile,
            use_container_width=True
        )

    else:

        st.warning(
            "Nu există suficiente observații valide pentru analiza "
            "temperatură - consum."
        )


# ============================================================
# DATE BRUTE
# ============================================================

with st.expander("🔍 Vezi datele procesate"):

    st.dataframe(
        df,
        use_container_width=True
    )