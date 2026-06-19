"""
ArenaPulse SQLite data layer.

All dashboard data reads come through here. The database is created and
seeded by scripts/seed_db.py. In production, the ingestion pipeline writes
to the same schema through the POS sanitization layer.

Connection is cached per session — one connection per Streamlit rerun.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parents[2] / "arenapulse.db"


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ── Generic helpers ────────────────────────────────────────────────────────────

def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    with _conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def scalar(sql: str, params: tuple = ()) -> object:
    with _conn() as conn:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None


# ── Events ─────────────────────────────────────────────────────────────────────

def get_event(event_id: int) -> dict:
    df = query("SELECT * FROM events WHERE event_id = ?", (event_id,))
    if df.empty:
        raise ValueError(f"Event {event_id} not found")
    return df.iloc[0].to_dict()


def get_live_event(sport: str) -> dict:
    """Return the single live/demo event for the given sport."""
    df = query(
        "SELECT * FROM events WHERE sport = ? AND is_live = 1 LIMIT 1",
        (sport,),
    )
    if df.empty:
        raise ValueError(f"No live event found for sport={sport!r}")
    return df.iloc[0].to_dict()


def get_past_events(sport: str, n: int = 10) -> pd.DataFrame:
    return query(
        "SELECT * FROM events WHERE sport = ? AND is_live = 0 ORDER BY event_date DESC LIMIT ?",
        (sport, n),
    )


# ── Energy ─────────────────────────────────────────────────────────────────────

def get_energy_systems(event_id: int) -> pd.DataFrame:
    """Load breakdown by system — maps to Energy_Context sheet."""
    return query(
        "SELECT system, share_pct AS share, status, recommendation "
        "FROM energy_systems WHERE event_id = ?",
        (event_id,),
    )


def get_energy_timeseries(event_id: int) -> pd.DataFrame:
    """Cumulative kWh by game minute for a single event."""
    return query(
        "SELECT minute, cumulative_kwh FROM energy_timeseries "
        "WHERE event_id = ? ORDER BY minute",
        (event_id,),
    )


def get_energy_timeseries_avg(sport: str) -> pd.DataFrame:
    """Average cumulative kWh curve across all past events for sport."""
    return query(
        """
        SELECT et.minute, AVG(et.cumulative_kwh) AS avg_kwh
        FROM energy_timeseries et
        JOIN events e ON e.event_id = et.event_id
        WHERE e.sport = ? AND e.is_live = 0
        GROUP BY et.minute
        ORDER BY et.minute
        """,
        (sport,),
    )


# ── Waste ──────────────────────────────────────────────────────────────────────

def get_waste_streams(event_id: int) -> pd.DataFrame:
    return query(
        "SELECT stream, expected_lbs, max_recoverable_lbs, landfill_risk_lbs "
        "FROM waste_streams WHERE event_id = ?",
        (event_id,),
    )


def get_waste_diversion_history(sport: str, n: int = 10) -> pd.DataFrame:
    return query(
        """
        SELECT event_date AS date, max_possible_diversion_pct AS max_possible_pct
        FROM events
        WHERE sport = ? AND is_live = 0
        ORDER BY event_date DESC LIMIT ?
        """,
        (sport, n),
    )


def get_zone_status(event_id: int) -> pd.DataFrame:
    return query(
        "SELECT zone, density FROM zone_status WHERE event_id = ?",
        (event_id,),
    )


def get_section_sales(event_id: int) -> pd.DataFrame:
    """POS-derived packaging breakdown per section (approved fields only)."""
    return query(
        """
        SELECT section, zone,
               recyclable_pct, compostable_pct, landfill_pct,
               top_item_1, top_item_2, top_item_3
        FROM section_sales WHERE event_id = ?
        """,
        (event_id,),
    )


# ── Water ──────────────────────────────────────────────────────────────────────

def get_water_systems(event_id: int) -> pd.DataFrame:
    return query(
        "SELECT system, share_pct AS share, status, note "
        "FROM water_systems WHERE event_id = ?",
        (event_id,),
    )


def get_water_timeseries(event_id: int) -> pd.DataFrame:
    return query(
        "SELECT minute, cumulative_litres FROM water_timeseries "
        "WHERE event_id = ? ORDER BY minute",
        (event_id,),
    )


def get_water_timeseries_avg(sport: str) -> pd.DataFrame:
    return query(
        """
        SELECT wt.minute, AVG(wt.cumulative_litres) AS avg_litres
        FROM water_timeseries wt
        JOIN events e ON e.event_id = wt.event_id
        WHERE e.sport = ? AND e.is_live = 0
        GROUP BY wt.minute
        ORDER BY wt.minute
        """,
        (sport,),
    )


# ── Environmental ──────────────────────────────────────────────────────────────

def get_env_conditions(event_id: int) -> pd.DataFrame:
    """Current snapshot — maps to Environmental_Conditions sheet."""
    return query(
        "SELECT metric, value, unit, note FROM env_conditions WHERE event_id = ?",
        (event_id,),
    )


def get_env_risk(event_id: int) -> pd.DataFrame:
    """Risk factor cards — maps to Environmental_Risk sheet."""
    return query(
        "SELECT factor, status, headline, watch, notify_if "
        "FROM env_risk WHERE event_id = ?",
        (event_id,),
    )


def get_env_timeseries(event_id: int) -> pd.DataFrame:
    return query(
        "SELECT minute, temp_f, aqi FROM env_timeseries "
        "WHERE event_id = ? ORDER BY minute",
        (event_id,),
    )
