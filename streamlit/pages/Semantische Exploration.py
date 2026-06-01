import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import re

from core.data import _data
from core.filters import _active_filters, _filter_data
from core.metric import _metric

st.set_page_config(page_title="Einblicke", layout="wide", page_icon="🔎")

# ── DATEN ─────────────────────────────────────────────────────────────────────
df, T_TO_MRD, FILTER_COLS, num_cols, cat_cols, SOLL, IST = _data(file_path="data/transformed/digitalhaushalt_semantic_features.csv")

st.sidebar.header("⚙️ Einstellungen")

# ── SIDEBAR: Kennzahl ─────────────────────────────────────────────────────────
metric = _metric(df)
st.sidebar.markdown("---")

# ── FILTER ────────────────────────────────────────────────────────────────────
st.sidebar.subheader("🔍 Filter")
active_filters = _active_filters(df, FILTER_COLS)

# ── DATEN FILTERN ─────────────────────────────────────────────────────────────
df_sel, group_primary, group_color = _filter_data(df, active_filters, cat_cols, group_color_toggle=True)

# ── SEITE ─────────────────────────────────────────────────────────────────────
st.title("Semantische Exploration")

st.markdown("""
### Worum geht es hier?
Diese Seite ermöglich es, die **sprachliche Struktur und Komplexität** der Haushaltstitel (Titel aus maschinenlesbaren Daten + Beschreibungen aus PDFs) zu analysieren. Ziel ist es, Einblicke in die **semantische Gestaltung** der Titel zu gewinnen und zu verstehen, wie sich diese über Zeit und Ressorts hinweg unterscheiden.

### Was bedeuten die Filter-Toggles?
Titel im Haushalt enthalten oft lange Anhänge wie Haushaltsvermerke oder sogar gesamte Tabellen aus den PDF-Beschreibungen. Mit den Toggles lässt sich steuern, wie tief die Texte vor der Analyse bereinigt werden:
* **Bereinigte Titel:** Entfernt Haushaltsvermerke und Tabellen.
* **Erläuterungen entfernen:** Kürzt den Titel zusätzlich, indem erklärende Erläuterungen ebenfalls abgeschnitten werden.

**Weiterer Hinweis zur Bedienung:** Die globalen Filter und die primäre Gruppierungsauswahl in der Sidebar funktionieren hier genauso wie auf den anderen Seiten des Dashboards und steuern alle darunterliegenden Auswertungen.

### Die semantischen Kennzahlen
* **Durchschnittliche Wortanzahl:** Ein direkter Indikator für die Textkomplexität (Je mehr Wörter, desto komplexer).
* **Nominalstil-Quote:** Misst den Anteil an Substantiven. Höhere Werte können ein Hinweis auf stark komprimierte, administrative Sprache sein.
* **Handlungsdichte:** Zeigt den Anteil an operativen Aktionsverben (z. B. *entwickeln, beschaffen, modernisieren*). Je höher, desto aktiver und umsetzungsorientierter ist der Titel womöglich formuliert.
* **Akronym-Dichte:** Versucht den Anteil an genutzten Abkürzungen darzustelen. Hohe Werte könnten auf eine starke Nutzung von Fachjargon oder internen Kürzeln hinweisen.
* **Kardinalität (Text-Einzigartigkeit):** Gibt an, wie viel Prozent der Titel absolute Unikate sind. Eine niedrige Kardinalität zeigt eine hohe Standardisierung (Arbeiten mit wiederkehrenden Text-Baukästen), während eine hohe Kardinalität bedeutet, dass jeder Titel einzigartig formuliert ist.
""")
st.markdown("---")

if active_filters:
    pills = "  ·  ".join(
        f"**{k}** = {', '.join(v) if len(v) <= 3 else ', '.join(v[:3]) + f' +{len(v)-3}'}"
        for k, v in active_filters.items()
    )
    st.caption(f"Aktive Filter: {pills}")
else:
    st.caption("Kein Filter aktiv — alle Daten")

st.markdown("---")

digital_only = st.toggle("Nur digitale Titel anzeigen", value=True)
cleaned_titles = st.toggle("Bereinigte Titel nutzen (ohne Haushaltsvermerke und Tabellen)")
fully_cleaned_titles = st.toggle("Erläuterungen ebenfalls entfernen")

if fully_cleaned_titles:
    prefix = "fully_clean_"
    title_col = "text_fully_clean" if "text_fully_clean" in df_sel.columns else "text_clean"
elif cleaned_titles:
    prefix = "clean_"
    title_col = "text_clean" if "text_clean" in df_sel.columns else "titel_text"
else:
    prefix = "raw_"
    title_col = "text_raw" if "text_raw" in df_sel.columns else "titel_text"

col_tokens = f"{prefix}token_count" if f"{prefix}token_count" in df_sel.columns else "token_count"
col_noun   = f"{prefix}noun_ratio" if f"{prefix}noun_ratio" in df_sel.columns else "noun_ratio"
col_action = f"{prefix}action_density" if f"{prefix}action_density" in df_sel.columns else "action_density"
col_abk    = f"{prefix}abk_density"

if col_abk not in df_sel.columns and title_col in df_sel.columns:
    def _live_abk(text):
        words = str(text).split()
        if not words: return 0.0
        return len([w for w in words if re.match(r"^[A-ZÄÖÜß]{2,}[.,-]?$", w)]) / len(words)
    df_sel[col_abk] = df_sel[title_col].apply(_live_abk)
elif col_abk not in df_sel.columns:
    df_sel[col_abk] = 0.0

if digital_only and "is_digital" in df_sel.columns:
    df_sel = df_sel[df_sel["is_digital"] == True]


# ── 0. BEISPIEL-TITEL ─────────────────────────────────────────────────────────
st.subheader("Beispiele für Titelstrukturen")

st.markdown("**Per Klick auf eine Zeile können die Titeltexte vollständig eingesehen werden.**")

df_sel["Länge des Titels"] = df_sel[title_col].astype(str).str.len()

longest10 = (
    df_sel[[title_col, "Länge des Titels"]]
    .drop_duplicates(subset=[title_col])
    .sort_values(by="Länge des Titels", ascending=False)
    .head(10)
    .reset_index(drop=True)
)

shortest10 = (
    df_sel[[title_col, "Länge des Titels"]]
    .drop_duplicates(subset=[title_col])
    .sort_values(by="Länge des Titels", ascending=True)
    .head(10)
    .reset_index(drop=True)
)

st.caption("Die 10 längsten Titel (Komplexe Formulierungen)")
st.dataframe(
    longest10,
    column_config={
        title_col: st.column_config.TextColumn("Titeltext", width=800),
        "Länge des Titels": st.column_config.NumberColumn("Zeichen", format="%d", width=20)
    },
    hide_index=True,
)

st.markdown("---")

st.caption("Die 10 kürzesten Titel (Prägnante Posten)")
st.dataframe(
    shortest10,
    column_config={
        title_col: st.column_config.TextColumn("Titeltext", width=800),
        "Länge des Titels": st.column_config.NumberColumn("Zeichen", format="%d", width=20)
    },
    hide_index=True,
)

st.markdown("---")


# ── 1. SEMANTISCHE KENNZAHLEN (KPIs) ─────────────────────────────────────────
st.subheader("Semantische Struktur-Kennzahlen")

if len(df_sel) > 0:
    total_budget = df_sel[metric].sum()
    
    if total_budget > 0:
        avg_noun_ratio = (df_sel[col_noun] * df_sel[metric]).sum() / total_budget
        avg_action_density = (df_sel[col_action] * df_sel[metric]).sum() / total_budget
        avg_abk_density = (df_sel[col_abk] * df_sel[metric]).sum() / total_budget
    else:
        avg_noun_ratio = df_sel[col_noun].mean()
        avg_action_density = df_sel[col_action].mean()
        avg_abk_density = df_sel[col_abk].mean()
        
    avg_token_count = df_sel[col_tokens].mean()
else:
    avg_token_count, avg_noun_ratio, avg_action_density, avg_abk_density = 0, 0, 0, 0

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    label="Durchschnittliche Wortanzahl", 
    value=f"{avg_token_count:.1f} Wörter",
    help="Durchschnittliche Anzahl an Tokens (Wörtern) pro Titel."
)
c2.metric(
    label="Nominalstil-Quote", 
    value=f"{avg_noun_ratio * 100:.1f} %",
    help="Anteil der Substantive am Text (Indikator für administrative Komprimierung)."
)
c3.metric(
    label="Handlungsdichte", 
    value=f"{avg_action_density * 100:.1f} %",
    help="Anteil operativer Aktionsbegriffe im Titeltext."
)
c4.metric(
    label="Akronym-Dichte",
    value=f"{avg_abk_density * 100:.1f} %",
    help="Anteil von reinen Abkürzungen und Kürzeln am Titeltext."
)

st.markdown("---")


# ── INTERAKTIVES DICTIONARY FÜR CHARTS ────────────────────────────────────────
AVAILABLE_METRICS = {
    "Wortanzahl": col_tokens,
    "Nominalstil-Quote": col_noun,
    "Handlungsdichte": col_action,
    "Akronym-Dichte": col_abk
}


# ── 2. STRUKTUR-ANALYSE NACH GRUPPE ──────────────────────────────────────────
st.subheader(f"Struktureller Vergleich nach {group_primary}")

chart_metric_label = st.selectbox(
    "Metrik für Balkenchart wählen:",
    list(AVAILABLE_METRICS.keys()),
    key="sb_bar_metric"
)
active_bar_col = AVAILABLE_METRICS[chart_metric_label]

overall_mean = df_sel[active_bar_col].mean()

ling_df = df_sel.groupby(group_primary).agg(
    Vergleichswert=(active_bar_col, "mean"),
    Gesamt_Titel=(title_col, "count"),
    Einzigartige_Titel=(title_col, "nunique")
).reset_index()

ling_df["Kardinalität"] = (ling_df["Einzigartige_Titel"] / ling_df["Gesamt_Titel"]) * 100
ling_df = ling_df.sort_values("Vergleichswert", ascending=False)

is_percentage = "quote" in chart_metric_label.lower() or "dichte" in chart_metric_label.lower()
display_format = ".1f" if not is_percentage else ".2f"

fig_bar = px.bar(
    ling_df,
    x="Vergleichswert",
    y=group_primary,
    orientation="h",
    title=f"Durchschnittliche {chart_metric_label} nach {group_primary}",
    labels={"Vergleichswert": chart_metric_label, group_primary: ""},
    template="plotly_white",
    color="Kardinalität",
    color_continuous_scale="Blues",
    hover_data=["Gesamt_Titel", "Kardinalität"]
)

fig_bar.add_vline(
    x=overall_mean,
    line_dash="dash",
    line_color="#ffd640",
    line_width=2,
    annotation_text=f"Ø {overall_mean:.1f}%" if is_percentage else f"Ø {overall_mean:.1f}",
    annotation_position="top right"
)

fig_bar.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", 
    yaxis={'categoryorder':'total ascending'},
    xaxis=dict(ticksuffix=" %" if is_percentage else "")
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")


# ── 3. ZEITREIHE ──────────────────────────────────────────────────────────────
if "Jahr" in df_sel.columns and df_sel["Jahr"].nunique() > 1:
    st.subheader("Zeitlicher Verlauf der semantischen Merkmale")

    ts_metric_label = st.selectbox(
        "Metrik für Zeitreihe wählen:",
        list(AVAILABLE_METRICS.keys()),
        key="sb_ts_metric"
    )
    active_ts_col = AVAILABLE_METRICS[ts_metric_label]
    is_ts_percentage = "quote" in ts_metric_label.lower() or "dichte" in ts_metric_label.lower()

    ts = (
        df_sel
        .groupby(["Jahr"])[active_ts_col]
        .mean()
        .reset_index()
    )
    ts["Jahr"] = ts["Jahr"].astype(int)
    ts = ts.sort_values("Jahr")

    fig_ts = px.line(
        ts,
        x="Jahr",
        y=active_ts_col,
        markers=True,
        title=f"Verlauf der {ts_metric_label} über die Jahre",
        template="plotly_white",
        labels={"Jahr": "Jahr", active_ts_col: ts_metric_label},
        height=500
    )
    fig_ts.update_traces(line=dict(width=2), marker=dict(size=6))
    fig_ts.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickmode="linear"),
        yaxis=dict(showgrid=True, gridcolor="#eee", tickformat='.1%' if is_ts_percentage else None),
        hovermode="x unified"
    )
    st.plotly_chart(fig_ts, use_container_width=True)
    st.markdown("---")

# ── 4. LINGUISTIK VS. BUDGET (SCATTER) ────────────────────────────────────────
st.subheader("Linguistische Komplexität im Verhältnis zum Budget")

scatter_metric_label = st.selectbox(
    "Metrik für das Streudiagramm wählen:",
    list(AVAILABLE_METRICS.keys()),
    key="sb_scatter_metric" 
)
active_scatter_col = AVAILABLE_METRICS[scatter_metric_label]

st.markdown(f"""
Dieses Diagramm setzt die sprachlichen Merkmale direkt in Beziehung zur Budgethöhe der einzelnen Titel. 
Ausreißer **oben rechts** zeigen teure Posten mit gleichzeitig hoher Komplexität im Bereich **{scatter_metric_label}**.
""")

scatter_df = df_sel[df_sel[metric] > 0].copy()

if len(scatter_df) > 0:
    is_scatter_percentage = "quote" in scatter_metric_label.lower() or "dichte" in scatter_metric_label.lower()
    
    fig_scatter = px.scatter(
        scatter_df,
        x=active_scatter_col,  # Nutzt jetzt die eigene Auswahl
        y=metric,
        title=f"Verhältnis: {scatter_metric_label} vs. Budgethöhe",
        labels={active_scatter_col: scatter_metric_label, metric: "Budget (Euro)"},
        template="plotly_white",
        color=active_scatter_col,
        color_continuous_scale="Viridis",
        hover_data={
            title_col: True, 
            metric: ":,.2f €", 
            active_scatter_col: ":.2f%" if is_scatter_percentage else ":.1f"
        },
        opacity=0.6
    )

    fig_scatter.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            ticksuffix=" %" if is_scatter_percentage else "", 
            showgrid=True, 
            gridcolor="#eee"
        ),
        yaxis=dict(showgrid=True, gridcolor="#eee"),
        height=600
    )
    
    fig_scatter.update_traces(marker=dict(size=8))
    
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("Keine Titel mit einem Budget größer als 0 € für die Streudiagramm-Analyse vorhanden.")

st.markdown("---")

# ── STYLE ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="metric-container"] {
    background: #f0f4ff;
    border-radius: 8px;
    padding: 10px 16px;
}
</style>
""", unsafe_allow_html=True)