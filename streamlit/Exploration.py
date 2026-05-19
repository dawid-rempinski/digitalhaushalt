import pandas as pd
import plotly.express as px
import streamlit as st

from core.data import _data
from core.filters import _active_filters, _filter_data
from core.metric import _metric

st.set_page_config(page_title="Digitalhaushalt Exploration", layout="wide", page_icon="📊")

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
df_sel, group_primary, group_color = _filter_data(df, active_filters, cat_cols, group_color_toggle=True)

# ── HEADER & KPIs ─────────────────────────────────────────────────────────────
st.title("📊 Digitalhaushalt Exploration")

if active_filters:
    pills = "  ·  ".join(
        f"**{k}** = {', '.join(v) if len(v) <= 3 else ', '.join(v[:3]) + f' +{len(v)-3}'}"
        for k, v in active_filters.items()
    )
    st.caption(f"Aktive Filter: {pills}")
else:
    st.caption("Kein Filter aktiv — alle Daten")

st.markdown("---")

c1, c2, c3, c4 = st.columns(4)
soll_val = df_sel["Digitalhaushalt Soll (eng)"].sum() / T_TO_MRD if "Digitalhaushalt Soll (eng)" in df_sel.columns else None
ist_val  = df_sel["Digitalhaushalt Ist (eng)"].sum()  / T_TO_MRD if "Digitalhaushalt Ist (eng)"  in df_sel.columns else None

c1.metric("Haushaltstitel", f"{len(df_sel):,}")
if soll_val is not None:
    c2.metric("Geplante Digitalausgaben (Soll)", f"{soll_val:,.2f} Mrd. €")
if ist_val is not None:
    c3.metric("Getätigte Digitalausgaben (Ist)", f"{ist_val:,.2f} Mrd. €")
if soll_val and ist_val and soll_val != 0:
    c4.metric("Ausschöpfung (Ist/Soll)", f"{ist_val / soll_val * 100:.1f} %")

st.markdown("---")

# ── CHART ─────────────────────────────────────────────────────────────────────
group_cols = [group_primary] + ([group_color] if group_color else [])

grouped = (
    df_sel
    .groupby(group_cols, dropna=False)[metric]
    .sum()
    .reset_index()
)
grouped["_val"] = grouped[metric] / T_TO_MRD

order = (
    grouped.groupby(group_primary)["_val"]
    .sum()
    .sort_values(ascending=False)
    .index.tolist()
)

chart_title = f"{metric} nach {group_primary}"
if group_color:
    chart_title += f" · aufgeschlüsselt nach {group_color}"

fig = px.bar(
    grouped,
    x="_val",
    y=group_primary,
    color=group_color,
    orientation="h",
    barmode="stack",
    title=chart_title,
    text="_val",
    template="plotly_white",
    category_orders={group_primary: order},
    labels={"_val": f"{metric} (Mrd. €)", group_primary: "", group_color: group_color or ""},
    height=max(420, 28 * grouped[group_primary].nunique() + 150),
)
fig.update_traces(texttemplate="%{x:.2f}", textposition="outside", cliponaxis=False)
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=True, gridcolor="#eee", title=f"{metric} (Mrd. €)"),
    yaxis_title="",
    legend_title=group_color or "",
    bargap=0.2,
    margin=dict(l=10, r=90, t=60, b=40),
)

st.plotly_chart(fig, use_container_width=True)

# ── ZEITREIHE ─────────────────────────────────────────────────────────────────
if "Jahr" in df_sel.columns and df_sel["Jahr"].nunique() > 1:
    st.markdown("---")
    st.subheader("📅 Zeitreihe")

    # Gruppierung: immer nach Jahr + group_primary als Linien
    # So bleibt der Kontext der gewählten Hauptgruppe erhalten
    ts_group = ["Jahr", group_primary]
    ts = (
        df_sel
        .groupby(ts_group, dropna=False)[metric]
        .sum()
        .reset_index()
    )
    ts["_val"] = ts[metric] / T_TO_MRD
    ts["Jahr_int"] = ts["Jahr"].astype(int)
    ts = ts.sort_values("Jahr_int")

    # Zu viele Linien machen das Chart unlesbar → Warnung + Cap
    n_lines = ts[group_primary].nunique()
    MAX_LINES = 15

    if n_lines > MAX_LINES:
        # Nur Top-N nach Gesamtwert zeigen
        top_groups = (
            ts.groupby(group_primary)["_val"]
            .sum()
            .nlargest(MAX_LINES)
            .index
        )
        ts_plot = ts[ts[group_primary].isin(top_groups)]
        st.caption(
            f"ℹ️ {n_lines} Gruppen — Zeitreihe zeigt die Top {MAX_LINES} nach Gesamtwert. "
            "Für alle: Filter einschränken."
        )
    else:
        ts_plot = ts

    fig_ts = px.line(
        ts_plot,
        x="Jahr",
        y="_val",
        color=group_primary,
        markers=True,
        title=f"{metric} · Jahresverlauf nach {group_primary}",
        template="plotly_white",
        labels={"_val": f"{metric} (Mrd. €)", "Jahr": "Jahr", group_primary: group_primary},
        height=600,
    )
    fig_ts.update_traces(line=dict(width=2), marker=dict(size=7))
    fig_ts.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, tickmode="linear"),
        yaxis=dict(showgrid=True, gridcolor="#eee", title=f"{metric} (Mrd. €)"),
        legend_title=group_primary,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=60, b=40),
    )
    st.plotly_chart(fig_ts, use_container_width=True)

# ── TABELLEN ──────────────────────────────────────────────────────────────────
with st.expander("📋 Aggregierte Tabelle"):
    disp = grouped.drop(columns=["_val"]).copy()
    disp[metric] = (disp[metric] / T_TO_MRD).round(4)
    disp = disp.rename(columns={metric: f"{metric} (Mrd. €)"})
    st.dataframe(
        disp.sort_values(f"{metric} (Mrd. €)", ascending=False).reset_index(drop=True),
        use_container_width=True, height=280,
    )

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