import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("monitoring.db")

st.set_page_config(page_title="Monitoring IA", layout="wide")
st.title("Monitoring des inférences")


def load_data(limit: int = 100) -> pd.DataFrame:
    # Lit les derniers événements pour le tableau de bord
    query = """
        SELECT
            id,
            ts_utc,
            request_id,
            selected_hour,
            predicted_class,
            predicted_label,
            latency_ms,
            status
        FROM inference_events
        ORDER BY id DESC
        LIMIT ?
    """

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn, params=[limit])

    if not df.empty:
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], errors="coerce", utc=True)

    return df


if not DB_PATH.exists():
    # La base est créée par l'app Flask au démarrage
    st.error("Le fichier monitoring.db est introuvable. Lance d'abord l'application Flask.")
    st.stop()

try:
    data = load_data(limit=100)
except Exception as exc:
    st.error(f"Erreur de lecture SQLite: {exc}")
    st.stop()

if data.empty:
    st.warning("Aucune donnée disponible pour le filtre sélectionné.")
    st.stop()

metric_1, metric_2, metric_3 = st.columns(3)
# Indicateurs rapides pour diagnostiquer l'état des inférences
metric_1.metric("Total lignes affichées", len(data))
metric_2.metric("Latence moyenne (ms)", round(data["latency_ms"].dropna().mean(), 2) if data["latency_ms"].notna().any() else "-")
metric_3.metric("Erreurs dans l'extrait", int((data["status"] == "error").sum()))

st.subheader("Événements récents")
st.dataframe(data, use_container_width=True)

chart_col_1, chart_col_2 = st.columns(2)

with chart_col_1:
    st.subheader("Latence dans le temps")
    latency_df = data.dropna(subset=["latency_ms", "ts_utc"]).sort_values("ts_utc")
    if latency_df.empty:
        st.info("Pas assez de données pour tracer la latence.")
    else:
        st.line_chart(latency_df.set_index("ts_utc")["latency_ms"], use_container_width=True)

with chart_col_2:
    st.subheader("Répartition des prédictions")
    repartition = data["predicted_label"].fillna("inconnu").value_counts().rename_axis("label").reset_index(name="count")
    st.bar_chart(repartition.set_index("label"), use_container_width=True)
