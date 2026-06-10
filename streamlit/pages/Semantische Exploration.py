import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import re
from pathlib import Path
import numpy as np

from core.data import _data
from core.filters import _active_filters, _filter_data
from core.metric import _metric

st.set_page_config(page_title="Einblicke", layout="wide", page_icon="🔎")

# ── DATEN ─────────────────────────────────────────────────────────────────────
df, T_TO_MRD, FILTER_COLS, num_cols, cat_cols, SOLL, IST = _data(
    file_path="data/transformed/digitalhaushalt_semantic_features.csv"
)

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

# ── TOP 15 KEYWORDS ───────────────────────────────────────────────
st.subheader("Top 15 Keywords nach Vorkommen im Datensatz")

kw_col = "keywords"

def parse_keywords(x):
    if pd.isna(x):
        return []
    x = str(x)
    return [p.strip() for p in x.split("|") if p.strip()]

kw_series = df_sel[kw_col].apply(parse_keywords).explode()

kw_series = kw_series.dropna()
kw_series = kw_series[kw_series != ""]

top15 = kw_series.value_counts().head(15)

st.dataframe(
    top15.reset_index(name="Anzahl").rename(columns={"index": "Schlagwort"}),
    column_config={
        "Schlagwort": st.column_config.TextColumn("Schlagwort", width=800),
        "Anzahl": st.column_config.NumberColumn("Anzahl", format="%d", width=120)
    },
    use_container_width=True,
    hide_index=True,
    height=560
)

# ── KEYWORD HEATMAP ────────────────────────
st.subheader(f"Keyword-Struktur nach {group_primary} (Top 15 nach Vorkommen im Datensatz)")

kw_col = "keywords"

if kw_col not in df_sel.columns:
    st.error("Spalte 'keywords' fehlt im aktuellen DataFrame")
    st.stop()

df_kw = df_sel[[group_primary, kw_col]].copy()

def parse_keywords(x):
    if pd.isna(x):
        return []
    x = str(x).strip()
    if not x:
        return []
    return [p.strip() for p in x.split("|") if p.strip()]

df_kw["_kw"] = df_kw[kw_col].apply(parse_keywords)

exploded = df_kw.explode("_kw").rename(columns={"_kw": "keyword"})
exploded = exploded.dropna()

exploded["keyword"] = exploded["keyword"].astype(str).str.strip()
exploded = exploded[exploded["keyword"] != ""]

top15 = exploded["keyword"].value_counts().head(15).index
exploded = exploded[exploded["keyword"].isin(top15)]

heat = (
    exploded
    .groupby([group_primary, "keyword"])
    .size()
    .reset_index(name="count")
)

pivot = heat.pivot_table(
    index=group_primary,
    columns="keyword",
    values="count",
    fill_value=0,
    aggfunc="sum"
)

pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

fig = px.imshow(
    pivot,
    aspect="auto",
    color_continuous_scale="Blues",
    title=f"Top 15 Keywords nach {group_primary}",
    height=1000
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── KEYWORD AUSSCHÖPFUNG ───────────────────────────────────────────────────────
st.subheader("Ausschöpfungsquote nach Keyword")

df_kw_aus = df_sel[[kw_col, SOLL, IST]].copy()
df_kw_aus[SOLL] = pd.to_numeric(df_kw_aus[SOLL], errors='coerce')
df_kw_aus[IST]  = pd.to_numeric(df_kw_aus[IST],  errors='coerce')
df_kw_aus = df_kw_aus[df_kw_aus[SOLL] > 0].copy()
df_kw_aus['ausschoepfung'] = df_kw_aus[IST] / df_kw_aus[SOLL]
df_kw_aus['_kw'] = df_kw_aus[kw_col].apply(parse_keywords)

df_kw_aus_exp = (
    df_kw_aus.explode('_kw')
    .rename(columns={'_kw': 'keyword'})
    .dropna(subset=['keyword', 'ausschoepfung'])
)
df_kw_aus_exp['keyword'] = df_kw_aus_exp['keyword'].str.strip()
df_kw_aus_exp = df_kw_aus_exp[df_kw_aus_exp['keyword'] != '']

c1, c2, c3 = st.columns(3)
with c1:
    min_titel = st.slider("Mindestanzahl Titel pro Keyword", min_value=1, max_value=20, value=5, key="sl_min_titel")
with c2:
    sort_metric = st.radio("Sortieren nach", ["Gewichteter Durchschnitt", "Einfacher Durchschnitt"], horizontal=True, key="rb_aus")
    st.caption(
        "**Gewichteter Durchschnitt:** Titel mit hohem Budget haben mehr Einfluss auf den Wert. "
        "Beispiel: Ein Titel mit 50 Mio. € zählt stärker als zehn Titel mit je 100.000 €. "
        "→ Zeigt, wie gut das Geld insgesamt ausgeschöpft wurde.\n\n"
        "**Einfacher Durchschnitt:** Jeder Titel zählt gleich, egal wie groß. "
        "→ Zeigt, ob ein Keyword strukturell oft mit schlechter oder guter Ausschöpfung vorkommt."
    )
with c3:
    show_bottom = st.toggle("Bottom 20 anzeigen", value=False, key="tg_bottom")

sort_col = 'gewichteter_avg' if sort_metric == "Gewichteter Durchschnitt" else 'avg_ausschoepfung'

kw_stats = df_kw_aus_exp.groupby('keyword').apply(
    lambda g: pd.Series({
        'n_titel': len(g),
        'avg_ausschoepfung': g['ausschoepfung'].mean(),
        'gewichteter_avg': np.nansum(g['ausschoepfung'] * g[SOLL]) / np.nansum(g[SOLL]) if np.nansum(g[SOLL]) > 0 else np.nan,
    })
).reset_index()

kw_filtered = (
    kw_stats[kw_stats['n_titel'] >= min_titel]
    .dropna(subset=[sort_col])
)

kw_stats_top = kw_filtered.sort_values(sort_col, ascending=False).head(20)
kw_stats_bottom = kw_filtered.sort_values(sort_col, ascending=True).head(20)

kw_display = kw_stats_bottom if show_bottom else kw_stats_top
chart_title = (
    f"Bottom 20 Keywords nach Ausschöpfungsquote ({sort_metric}, mind. {min_titel} Titel)"
    if show_bottom else
    f"Top 20 Keywords nach Ausschöpfungsquote ({sort_metric}, mind. {min_titel} Titel)"
)

fig_aus = px.bar(
    kw_display,
    x=sort_col,
    y='keyword',
    orientation='h',
    title=chart_title,
    labels={sort_col: "Ausschöpfungsquote", 'keyword': ''},
    template="plotly_white",
    color=sort_col,
    color_continuous_scale="Blues" if not show_bottom else "Reds_r",
    hover_data=['n_titel', 'avg_ausschoepfung', 'gewichteter_avg']
)
fig_aus.add_vline(
    x=1.0, line_dash="dash", line_color="#ffd640", line_width=2,
    annotation_text="100%", annotation_position="top right"
)
fig_aus.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis={'categoryorder': 'total ascending' if not show_bottom else 'total descending'},
    xaxis=dict(tickformat='.0%'),
    height=800
)
st.plotly_chart(fig_aus, use_container_width=True)

st.markdown("---")

# ── KEYWORD AUSSCHÖPFUNG ZEITREIHE ────────────────────────────────────────────
st.subheader("Keyword Ausschöpfung über Zeit — Schwankungsanalyse")

if "Jahr" not in df_sel.columns or df_sel["Jahr"].nunique() < 2:
    st.info("Zeitreihenanalyse benötigt mindestens 2 Jahre im gefilterten Datensatz.")
else:
    df_kw_ts = df_sel[[kw_col, SOLL, IST, "Jahr"]].copy()
    df_kw_ts[SOLL] = pd.to_numeric(df_kw_ts[SOLL], errors='coerce')
    df_kw_ts[IST]  = pd.to_numeric(df_kw_ts[IST],  errors='coerce')
    df_kw_ts = df_kw_ts[df_kw_ts[SOLL] > 0].copy()
    df_kw_ts['ausschoepfung'] = df_kw_ts[IST] / df_kw_ts[SOLL]
    df_kw_ts['_kw'] = df_kw_ts[kw_col].apply(parse_keywords)

    df_kw_ts_exp = (
        df_kw_ts.explode('_kw')
        .rename(columns={'_kw': 'keyword'})
        .dropna(subset=['keyword', 'ausschoepfung', 'Jahr'])
    )
    df_kw_ts_exp['keyword'] = df_kw_ts_exp['keyword'].str.strip()
    df_kw_ts_exp = df_kw_ts_exp[df_kw_ts_exp['keyword'] != '']

    ts_stats = (
        df_kw_ts_exp.groupby(['keyword', 'Jahr'])
        .agg(avg_aus=('ausschoepfung', 'mean'), n=('ausschoepfung', 'count'))
        .reset_index()
    )

    kw_year_counts = ts_stats[ts_stats['n'] >= min_titel].groupby('keyword')['Jahr'].nunique()
    valid_kws = kw_year_counts[kw_year_counts >= 2].index
    ts_stats = ts_stats[ts_stats['keyword'].isin(valid_kws)]

    from scipy.stats import linregress

    def trend_slope(g):
        g = g.sort_values('Jahr')
        if len(g) < 2:
            return np.nan
        return linregress(g['Jahr'].astype(int), g['avg_aus']).slope

    trend = (
        ts_stats.groupby('keyword')
        .apply(trend_slope)
        .reset_index()
        .rename(columns={0: 'slope'})
        .dropna()
        .sort_values('slope')
    )

    top_n_trend = st.slider("Top N Keywords pro Richtung", min_value=3, max_value=10, value=5, key="sl_trend")

    top_rising  = trend.tail(top_n_trend).sort_values('slope', ascending=True)['keyword'].tolist()
    top_falling = trend.head(top_n_trend).sort_values('slope', ascending=False)['keyword'].tolist()

    for keywords, label, palette in [
        (top_rising,  "📈 Stärkster Anstieg der Ausschöpfung über Zeit",  px.colors.sequential.Greens),
        (top_falling, "📉 Stärkster Rückgang der Ausschöpfung über Zeit", px.colors.sequential.Reds),
    ]:
        ts_p = ts_stats[ts_stats['keyword'].isin(keywords)].copy()
        ts_p['Jahr'] = ts_p['Jahr'].astype(int)
        ts_p['avg_aus_pct'] = ts_p['avg_aus'] * 100

        first_last = (
            ts_p.groupby('keyword')
            .apply(lambda g: g.sort_values('Jahr').iloc[-1]['avg_aus_pct'] - g.sort_values('Jahr').iloc[0]['avg_aus_pct'])
            .reset_index()
            .rename(columns={0: 'diff'})
        )
        diff_map = dict(zip(first_last['keyword'], first_last['diff']))
        slope_map = dict(zip(trend['keyword'], trend['slope']))
        ts_p['keyword_label'] = ts_p['keyword'].map(
            lambda k: f"{k} ({diff_map.get(k, 0):+.0f}%)"
        )

        ascending = (label == "📉 Stärkster Rückgang der Ausschöpfung über Zeit")
        label_order = (
            ts_p[['keyword', 'keyword_label']]
            .drop_duplicates()
            .assign(slope=lambda x: x['keyword'].map(slope_map))
            .sort_values('slope', ascending=ascending)
            ['keyword_label']
            .tolist()
        )

        fig = px.line(
            ts_p, x='Jahr', y='avg_aus_pct', color='keyword_label', markers=True,
            title=label,
            labels={'avg_aus_pct': 'Ø Ausschöpfung (%)', 'Jahr': 'Jahr', 'keyword_label': 'Keyword'},
            template="plotly_white", height=450,
            color_discrete_sequence=px.colors.qualitative.D3,
            category_orders={'keyword_label': label_order}
        )
        fig.add_hline(y=100, line_dash="dash", line_color="#ffd640", line_width=2,
                    annotation_text="100%", annotation_position="right")
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickmode="linear"),
            yaxis=dict(showgrid=True, gridcolor="#eee", ticksuffix=" %"),
            hovermode="x unified",
            height=650
        )
        st.plotly_chart(fig, use_container_width=True)

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