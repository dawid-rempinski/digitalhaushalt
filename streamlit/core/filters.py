import streamlit as st

def _active_filters(df, FILTER_COLS):
    active_filters = {}

    for col in FILTER_COLS:

        df_opts = df.copy()

        for other_col in FILTER_COLS:
            if other_col == col:
                continue

            vals = st.session_state.get(f"f_{other_col}", [])
            if vals:
                df_opts = df_opts[df_opts[other_col].astype(str).isin(vals)]

        opts = sorted(df_opts[col].dropna().astype(str).unique())

        current = st.session_state.get(f"f_{col}", [])
        current_valid = [v for v in current if v in opts]

        st.session_state[f"f_{col}"] = current_valid

        st.sidebar.multiselect(
            label=f"{col} ({len(opts)})",
            options=opts,
            key=f"f_{col}",
            placeholder="Filterwert auswählen..."
        )

    for col in FILTER_COLS:
        val = st.session_state.get(f"f_{col}", [])
        if val:
            active_filters[col] = val

    if st.sidebar.button("✖ Alle Filter zurücksetzen"):
        for col in FILTER_COLS:
            st.session_state.pop(f"f_{col}", None)
        st.rerun()

    return active_filters


def _filter_data(df, active_filters, cat_cols, group_color_toggle=False):
    df_sel = df.copy()

    for col, vals in active_filters.items():
        df_sel = df_sel[df_sel[col].astype(str).isin(vals)]

    if df_sel.empty:
        st.warning("⚠️ Keine Daten mit den gewählten Filtern.")
        st.stop()

    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Gruppierung")

    group_primary = st.sidebar.selectbox(
        "Hauptgruppe (Y-Achse)",
        options=cat_cols,
        index=0,
        key="group_primary"
    )

    group_color = None
    if group_color_toggle == True:
        group_color = st.sidebar.selectbox(
            "Aufschlüsseln nach (Farbe)",
            options=["— keine —"] + [c for c in cat_cols if c != group_primary],
            index=0,
            key="group_color"
        )

        group_color = None if group_color == "— keine —" else group_color

    return df_sel, group_primary, group_color

if __name__ == "__main__":
    _active_filters()
    _filter_data()