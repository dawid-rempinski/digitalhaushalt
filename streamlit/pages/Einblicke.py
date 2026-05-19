import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.data import _data
from core.filters import _active_filters, _filter_data
from core.metric import _metric

st.set_page_config(page_title="Einblicke", layout="wide", page_icon="🔎")

# ── DATEN ─────────────────────────────────────────────────────────────────────
df, T_TO_MRD, FILTER_COLS, num_cols, cat_cols, SOLL, IST = _data()

st.sidebar.header("⚙️ Einstellungen")

# ── SIDEBAR: Kennzahl ─────────────────────────────────────────────────────────
metric = _metric(df)
st.sidebar.markdown("---")

# ── FILTER ────────────────────────────────────────────────────────────────────
st.sidebar.subheader("🔍 Filter")
active_filters = _active_filters(df, FILTER_COLS)

# ── DATEN FILTERN ─────────────────────────────────────────────────────────────
df_sel, dim, group_color = _filter_data(df, active_filters, cat_cols)

# ── SEITE ─────────────────────────────────────────────────────────────────────
st.title("🔎 Einblicke")

if active_filters:
    pills = "  ·  ".join(
        f"**{k}** = {', '.join(v) if len(v) <= 3 else ', '.join(v[:3]) + f' +{len(v)-3}'}"
        for k, v in active_filters.items()
    )
    st.caption(f"Aktive Filter: {pills}")
else:
    st.caption("Kein Filter aktiv — alle Daten")

st.markdown("---")

has_soll = SOLL in df_sel.columns
has_ist  = IST  in df_sel.columns

# ── 1. SOLL vs. IST pro Jahr ──────────────────────────────────────────────────
if has_soll and has_ist and "Jahr" in df_sel.columns:
    st.subheader("Soll vs. Ist — Jahresvergleich")

    yearly = (
        df_sel.groupby("Jahr")[[SOLL, IST]]
        .sum()
        .reset_index()
        .sort_values("Jahr")
    )
    yearly["_soll"] = yearly[SOLL] / T_TO_MRD
    yearly["_ist"]  = yearly[IST]  / T_TO_MRD
    yearly["_luecke"] = yearly["_soll"] - yearly["_ist"]

    fig1 = go.Figure()
    fig1.add_bar(x=yearly["Jahr"], y=yearly["_soll"], name="Soll", marker_color="#a8c5e8")
    fig1.add_bar(x=yearly["Jahr"], y=yearly["_ist"],  name="Ist",  marker_color="#1f6fad")
    fig1.update_layout(
        barmode="group",
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickmode="linear"),
        yaxis=dict(title="Mrd. €", showgrid=True, gridcolor="#eee"),
        legend=dict(orientation="h", y=1.08),
        margin=dict(l=10, r=10, t=40, b=30),
        height=360,
    )
    st.plotly_chart(fig1, use_container_width=True)

    total_luecke = yearly["_luecke"].sum()
    avg_ausschoepfung = yearly["_ist"].sum() / yearly["_soll"].sum() * 100 if yearly["_soll"].sum() else 0
    k1, k2, k3 = st.columns(3)
    k1.metric("Kumulierte Budgetlücke", f"{total_luecke:,.2f} Mrd. €")
    k2.metric("Ø Ausschöpfung", f"{avg_ausschoepfung:.1f} %")
    k3.metric("Jahre im Datensatz", str(df_sel["Jahr"].nunique()))

    st.markdown("---")

# ── 2. TOP 10 UNGENUTZTE BUDGETS ──────────────────────────────────────────────
if has_soll and has_ist:
    st.subheader(f"Top 10 · schlechteste Ausschöpfung nach {dim}")
    st.caption("Sortiert nach niedrigster Ausschöpfungsquote (Effizienz).")

    gap_df = (
        df_sel.groupby(dim)[[SOLL, IST]]
        .sum()
        .reset_index()
    )

    gap_df = gap_df[gap_df[SOLL] > 0].copy()
    gap_df["Quote (%)"] = gap_df[IST] / gap_df[SOLL] * 100

    top10 = gap_df.nsmallest(10, "Quote (%)").copy()
    top10 = top10.sort_values("Quote (%)", ascending=False)

    fig2 = px.bar(
        top10,
        x="Quote (%)",
        y=dim,
        orientation="h",
        text=top10["Quote (%)"].round(1).astype(str) + "%",
        color="Quote (%)",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        template="plotly_white",
        labels={"Quote (%)": "Ausschöpfung (%)", dim: ""},
        height=max(360, 46 * len(top10) + 100),
    )

    fig2.add_vline(x=100, line_dash="dash", line_color="#aaa")
    fig2.update_traces(textposition="outside", cliponaxis=False)

    fig2.update_layout(
        xaxis=dict(range=[0, 120], showgrid=True, gridcolor="#eee"),
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=30, b=30),
    )

    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("---")

# ── 3. AUSSCHÖPFUNGSQUOTE ─────────────────────────────────────────────────────
if has_soll and has_ist:
    st.subheader(f"Top 10 · größte Budgetlücken nach {dim}")
    st.caption("Absolute Differenz zwischen Soll und Ist (nicht Effizienz).")

    gap_abs = (
        df_sel.groupby(dim)[[SOLL, IST]]
        .sum()
        .reset_index()
    )

    gap_abs = gap_abs[gap_abs[SOLL] > 0].copy()
    gap_abs["Lücke (Mrd. €)"] = (gap_abs[SOLL] - gap_abs[IST]) / T_TO_MRD

    top_gap = gap_abs.nlargest(10, "Lücke (Mrd. €)").copy()
    top_gap = top_gap.sort_values("Lücke (Mrd. €)", ascending=True)

    fig_gap = px.bar(
        top_gap,
        x="Lücke (Mrd. €)",
        y=dim,
        orientation="h",
        text=top_gap["Lücke (Mrd. €)"].round(2).astype(str) + " Mrd.",
        color="Lücke (Mrd. €)",
        color_continuous_scale="Blues",
        template="plotly_white",
        labels={"Lücke (Mrd. €)": "Budgetlücke (Mrd. €)", dim: ""},
        height=max(360, 46 * len(top_gap) + 100),
    )

    fig_gap.update_traces(textposition="outside", cliponaxis=False)
    fig_gap.update_layout(
        xaxis=dict(showgrid=True, gridcolor="#eee"),
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=30, b=30),
    )

    st.plotly_chart(fig_gap, use_container_width=True)
    st.markdown("---")

# ── 4. ANTEIL AM GESAMTHAUSHALT ───────────────────────────────────────────────
if has_soll and "Gesamthaushalt Soll" in df_sel.columns:
    st.subheader(f"Digitalanteil am Gesamthaushalt nach {dim}")
    st.caption("Wie digital ist jeder Bereich — relativ zu seinem Gesamtbudget?")

    share_df = (
        df_sel.groupby(dim)[[SOLL, "Gesamthaushalt Soll"]]
        .sum()
        .reset_index()
    )
    share_df = share_df[share_df["Gesamthaushalt Soll"] > 0].copy()
    share_df["Digitalanteil (%)"] = (share_df[SOLL] / share_df["Gesamthaushalt Soll"] * 100).round(2)
    share_df["Digi-Budget (Mrd. €)"] = share_df[SOLL] / T_TO_MRD
    share_df = share_df.sort_values("Digitalanteil (%)", ascending=True)

    fig4 = px.bar(
        share_df,
        x="Digitalanteil (%)",
        y=dim,
        orientation="h",
        text="Digitalanteil (%)",
        color="Digi-Budget (Mrd. €)",
        color_continuous_scale="Blues",
        template="plotly_white",
        labels={"Digitalanteil (%)": "Digitalanteil am Gesamtbudget (%)", dim: ""},
        height=max(360, 28 * len(share_df) + 100),
    )
    fig4.update_traces(texttemplate="%{x:.1f}%", textposition="outside", cliponaxis=False)
    fig4.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#eee"),
        coloraxis_colorbar=dict(title="Digi-Budget (Mrd. €)"),
        margin=dict(l=10, r=100, t=30, b=30),
    )
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown("---")

# ── 5. ZEITVERGLEICH (YoY) ───────────────────────────────────────────────────
if has_soll and "Jahr" in df.columns:
    st.subheader(f"Zeitvergleich Soll nach {dim}")

    df_sel_grouped = (
        df_sel.groupby(["Jahr", dim])[[SOLL]]
        .sum()
        .reset_index()
    )

    df_grouped = (
        df.groupby(["Jahr", dim])[[SOLL]]
        .sum()
        .reset_index()
    )

    df_sel_grouped = df_sel_grouped[df_sel_grouped[SOLL] > 0].copy()
    df_grouped = df_grouped[df_grouped[SOLL] > 0].copy()

    df_sel_grouped["Jahr"] = df_sel_grouped["Jahr"].astype(int)
    df_grouped["Jahr"] = df_grouped["Jahr"].astype(int)

    all_years = sorted(df["Jahr"].astype(int).unique())
    selected_years = sorted(df_sel["Jahr"].astype(int).unique())

    if len(selected_years) > 1:
        start_year = min(selected_years)
        end_year = max(selected_years)

        start_data = df_grouped[df_grouped["Jahr"] == start_year]
        end_data = df_grouped[df_grouped["Jahr"] == end_year]

    else:
        end_year = selected_years[0]

        idx = all_years.index(end_year)
        if idx == 0:
            st.info("Kein Vorjahr vorhanden")
            st.stop()

        start_year = all_years[idx - 1]

        start_data = df_grouped[df_grouped["Jahr"] == start_year]
        end_data = df_grouped[df_grouped["Jahr"] == end_year]

    start = start_data.set_index(dim)[SOLL]
    end = end_data.set_index(dim)[SOLL]

    comparison = pd.concat([start, end], axis=1, keys=["start", "end"]).fillna(0)
    comparison = comparison[comparison["start"] > 0].copy()

    comparison["Δ %"] = ((comparison["end"] / comparison["start"]) - 1) * 100
    comparison["Δ %"] = pd.to_numeric(comparison["Δ %"], errors="coerce")

    comparison["Δ abs"] = (comparison["end"] - comparison["start"]) / T_TO_MRD

    comparison = comparison.dropna(subset=["Δ %"]).reset_index()

    top = pd.concat([
        comparison.nlargest(5, "Δ %"),
        comparison.nsmallest(5, "Δ %")
    ]).sort_values("Δ %")

    fig5 = px.bar(
        top,
        x="Δ %",
        y=dim,
        orientation="h",
        color="Δ %",
        color_continuous_scale="RdBu",
        template="plotly_white",
        labels={"Δ %": f"Soll-Veränderung ({start_year} → {end_year})", dim: ""},
        height=max(400, 45 * len(top) + 100),
    )

    fig5.add_vline(x=0, line_dash="dash", line_color="#666")

    fig5.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#eee"),
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=50, b=30),
    )

    fig5.update_layout(title=f"{start_year} → {end_year}")

    st.plotly_chart(fig5, use_container_width=True)
    st.markdown("---")

# ── 6. EINZELPLAN BUDGETS VERTEILUNG AUF HAUPTFUNKTIONEN ───────────────
if has_soll and "Einzelplan (~Ministerium)" in df.columns and "Hauptfunktion" in df.columns:

    st.subheader("Budgetverteilung je Einzelplan nach Hauptfunktion")

    df_sel_grouped = (
        df_sel.groupby(["Einzelplan (~Ministerium)", "Hauptfunktion"])[[SOLL]]
        .sum()
        .reset_index()
        .dropna()
    )

    df_sel_grouped = df_sel_grouped[df_sel_grouped[SOLL] > 0]

    df_sel_grouped = df_sel_grouped.sort_values(by=SOLL, ascending=False)

    # Labels
    einzelplaene = df_sel_grouped["Einzelplan (~Ministerium)"].unique().tolist()
    hauptfunktionen = df_sel_grouped["Hauptfunktion"].unique().tolist()
    labels = einzelplaene + hauptfunktionen
    label_to_id = {l: i for i, l in enumerate(labels)}

    palette = px.colors.qualitative.Set3
    color_map = {e: palette[i % len(palette)] for i, e in enumerate(einzelplaene)}

    node_colors = [
        color_map.get(l, "rgba(200,200,200,0.4)") for l in labels
    ]

    source = df_sel_grouped["Einzelplan (~Ministerium)"].map(label_to_id)
    target = df_sel_grouped["Hauptfunktion"].map(label_to_id)
    value = df_sel_grouped[SOLL]

    link_colors = df_sel_grouped["Einzelplan (~Ministerium)"].map(
        lambda x: color_map.get(x, "rgba(150,150,150,0.25)")
    )

    fig6 = go.Figure(data=[go.Sankey(
        arrangement="freeform",
        node=dict(
            pad=20,
            thickness=18,
            label=labels,
            color=node_colors,
            line=dict(color="rgba(0,0,0,0.2)", width=0.5)
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors
        ),
        textfont=dict(
            size=11,           # Font size
            color="white"      # Font color for labels
        )
    )])

    fig6.update_layout(
        template="plotly_white",
        height=850,
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(size=11)
    )

    st.plotly_chart(fig6, use_container_width=True)
    st.markdown("---")

# ── 7. EINZELPLAN BUDGETS VERTEILUNG AUF KATEGORIEN ───────────────
if has_soll and "Einzelplan (~Ministerium)" in df.columns and "Kategorie" in df.columns:

    st.subheader("Budgetverteilung je Einzelplan nach Kategorie")

    df_sel_grouped = (
        df_sel.groupby(["Einzelplan (~Ministerium)", "Kategorie"])[[SOLL]]
        .sum()
        .reset_index()
        .dropna()
    )

    df_sel_grouped = df_sel_grouped[df_sel_grouped[SOLL] > 0]

    df_sel_grouped = df_sel_grouped.sort_values(by=SOLL, ascending=False)

    # Labels
    einzelplaene = df_sel_grouped["Einzelplan (~Ministerium)"].unique().tolist()
    kategorien = df_sel_grouped["Kategorie"].unique().tolist()
    labels = einzelplaene + kategorien
    label_to_id = {l: i for i, l in enumerate(labels)}

    palette = px.colors.qualitative.Set3
    color_map = {e: palette[i % len(palette)] for i, e in enumerate(einzelplaene)}

    node_colors = [
        color_map.get(l, "rgba(200,200,200,0.4)") for l in labels
    ]

    source = df_sel_grouped["Einzelplan (~Ministerium)"].map(label_to_id)
    target = df_sel_grouped["Kategorie"].map(label_to_id)
    value = df_sel_grouped[SOLL]

    link_colors = df_sel_grouped["Einzelplan (~Ministerium)"].map(
        lambda x: color_map.get(x, "rgba(150,150,150,0.25)")
    )

    fig7 = go.Figure(data=[go.Sankey(
        arrangement="freeform",
        node=dict(
            pad=20,
            thickness=18,
            label=labels,
            color=node_colors,
            line=dict(color="rgba(0,0,0,0.2)", width=0.5)
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors
        ),
        textfont=dict(
            size=11,           # Font size
            color="white"      # Font color for labels
        )
    )])

    fig7.update_layout(
        template="plotly_white",
        height=850,
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(size=11)
    )

    st.plotly_chart(fig7, use_container_width=True)

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