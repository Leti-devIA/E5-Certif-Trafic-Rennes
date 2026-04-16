import sqlite3
from datetime import datetime, timezone

DB_PATH = "monitoring.db"


def init_monitoring_db(db_path: str = DB_PATH) -> None:
    # Crée la table qui historise les inférences
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inference_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_utc TEXT NOT NULL,
                request_id TEXT,
                selected_hour INTEGER,
                predicted_class INTEGER,
                predicted_label TEXT,
                latency_ms REAL,
                status TEXT NOT NULL
            )
            """
        )
        connection.commit()


def record_inference_event(
    request_id: str,
    selected_hour: int,
    predicted_class: int,
    predicted_label: str,
    latency_ms: float,
    status: str = "predicted",
    db_path: str = DB_PATH,
) -> None:
    # Enregistre une inférence pour analyse ultérieure
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO inference_events (
                ts_utc,
                request_id,
                selected_hour,
                predicted_class,
                predicted_label,
                latency_ms,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                request_id,
                selected_hour,
                predicted_class,
                predicted_label,
                latency_ms,
                status,
            ),
        )
        connection.commit()


def get_health_snapshot(db_path: str = DB_PATH) -> dict:
    # Retourne un mini résumé des métriques de santé
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM inference_events")
        total_predictions = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT latency_ms
            FROM inference_events
            WHERE latency_ms IS NOT NULL
            ORDER BY id DESC
            LIMIT 20
            """
        )
        recent_latencies = [row[0] for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM inference_events
            WHERE status = 'error'
            """
        )
        total_errors = cursor.fetchone()[0]

    # Moyenne glissante des 20 dernières latences
    avg_latency_ms_last_20 = round(sum(recent_latencies) / len(recent_latencies), 2) if recent_latencies else None

    return {
        "total_predictions": total_predictions,
        "avg_latency_ms_last_20": avg_latency_ms_last_20,
        "total_errors": total_errors,
    }
