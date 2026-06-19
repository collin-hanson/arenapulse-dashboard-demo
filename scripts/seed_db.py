"""
ArenaPulse SQLite seed script.

Creates arenapulse.db in the project root and populates every table with
demo data that exactly matches what the dashboard currently displays.

Run from the project root:
    python scripts/seed_db.py

Safe to re-run — drops and recreates all tables each time.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "arenapulse.db"

# ── Schema ─────────────────────────────────────────────────────────────────────

SCHEMA = """
-- One row per event (live or historical)
CREATE TABLE IF NOT EXISTS events (
    event_id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    sport                       TEXT NOT NULL,          -- 'soccer' | 'nfl'
    is_live                     INTEGER NOT NULL DEFAULT 0,
    event_name                  TEXT NOT NULL,
    venue                       TEXT NOT NULL,
    event_date                  TEXT NOT NULL,          -- ISO date string
    attendance                  INTEGER NOT NULL,
    occupancy_rate              REAL NOT NULL,
    duration_min                INTEGER NOT NULL,
    leed_status                 TEXT,
    event_phase                 TEXT,                   -- live events only
    minutes_to_next_phase       INTEGER,
    next_phase                  TEXT,
    -- Waste
    max_possible_diversion_pct  REAL,
    max_div_target_pct          REAL,
    current_diversion_rate      REAL,
    next_year_target            REAL,
    platinum_target             REAL,
    total_waste_lb              REAL,
    -- Energy
    energy_per_fan_kwh          REAL,
    energy_benchmark_kwh        REAL,
    total_kwh                   REAL,
    -- Water
    water_per_fan_litres        REAL,
    water_guide_lpf             REAL,
    total_litres                REAL,
    restroom_check_done         INTEGER DEFAULT 0,
    fixture_faults              INTEGER DEFAULT 0,
    -- Environmental
    peak_temp_f                 REAL,
    peak_aqi                    REAL,
    peak_humidity_pct           REAL,
    peak_density_pct            REAL,
    env_incidents               INTEGER DEFAULT 0
);

-- Energy breakdown by system for each event
CREATE TABLE IF NOT EXISTS energy_systems (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES events(event_id),
    system          TEXT NOT NULL,
    share_pct       REAL NOT NULL,
    status          TEXT NOT NULL,
    recommendation  TEXT NOT NULL
);

-- Cumulative kWh at each game minute
CREATE TABLE IF NOT EXISTS energy_timeseries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES events(event_id),
    minute          INTEGER NOT NULL,
    cumulative_kwh  REAL NOT NULL
);

-- Waste streams for each event
CREATE TABLE IF NOT EXISTS waste_streams (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id            INTEGER NOT NULL REFERENCES events(event_id),
    stream              TEXT NOT NULL,
    expected_lbs        REAL NOT NULL,
    current_captured_lbs REAL NOT NULL,
    max_recoverable_lbs REAL NOT NULL,
    landfill_risk_lbs   REAL NOT NULL
);

-- Zone crowd density for each event
CREATE TABLE IF NOT EXISTS zone_status (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL REFERENCES events(event_id),
    zone        TEXT NOT NULL,
    density     REAL NOT NULL
);

-- POS-derived section packaging breakdown (approved fields only)
-- Sensitive fields (price, customer data, staff IDs) are never stored here
CREATE TABLE IF NOT EXISTS section_sales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL REFERENCES events(event_id),
    section         TEXT NOT NULL,
    zone            TEXT NOT NULL,
    recyclable_pct  REAL NOT NULL,
    compostable_pct REAL NOT NULL,
    landfill_pct    REAL NOT NULL,
    top_item_1      TEXT,
    top_item_2      TEXT,
    top_item_3      TEXT
);

-- Water breakdown by venue system
CREATE TABLE IF NOT EXISTS water_systems (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL REFERENCES events(event_id),
    system      TEXT NOT NULL,
    share_pct   REAL NOT NULL,
    status      TEXT NOT NULL,
    note        TEXT NOT NULL
);

-- Cumulative litres at each game minute
CREATE TABLE IF NOT EXISTS water_timeseries (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id            INTEGER NOT NULL REFERENCES events(event_id),
    minute              INTEGER NOT NULL,
    cumulative_litres   REAL NOT NULL
);

-- Environmental conditions snapshot
CREATE TABLE IF NOT EXISTS env_conditions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL REFERENCES events(event_id),
    metric      TEXT NOT NULL,
    value       REAL NOT NULL,
    unit        TEXT NOT NULL,
    note        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'Stable'
);

-- Environmental risk factor cards
CREATE TABLE IF NOT EXISTS env_risk (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL REFERENCES events(event_id),
    factor      TEXT NOT NULL,
    status      TEXT NOT NULL,
    headline    TEXT NOT NULL,
    watch       TEXT NOT NULL,
    notify_if   TEXT NOT NULL
);

-- Temp and AQI readings at each game minute
CREATE TABLE IF NOT EXISTS env_timeseries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL REFERENCES events(event_id),
    minute      INTEGER NOT NULL,
    temp_f      REAL NOT NULL,
    aqi         REAL NOT NULL
);
"""

# ── Helpers ────────────────────────────────────────────────────────────────────

def _energy_curve(total_kwh: float, time_points: np.ndarray) -> np.ndarray:
    base_fractions = np.array([
        0.00, 0.04, 0.10, 0.17, 0.26, 0.35, 0.43, 0.48,
        0.53, 0.61, 0.70, 0.79, 0.88, 0.93, 0.97, 1.00,
    ])
    # Pad or trim fractions to match time_points length
    f = np.interp(np.linspace(0, 1, len(time_points)),
                  np.linspace(0, 1, len(base_fractions)), base_fractions)
    return (f * total_kwh).round(0)


def _water_curve(total_litres: float, time_points: np.ndarray) -> np.ndarray:
    base_fractions = np.array([
        0.00, 0.03, 0.07, 0.13, 0.21, 0.30, 0.38, 0.44,
        0.55, 0.63, 0.71, 0.79, 0.87, 0.92, 0.97, 1.00,
    ])
    f = np.interp(np.linspace(0, 1, len(time_points)),
                  np.linspace(0, 1, len(base_fractions)), base_fractions)
    return (f * total_litres).round(0)


SOCCER_MINUTES = np.array([-30, -20, -10, 0, 10, 20, 30, 40, 45, 55, 65, 75, 85, 90, 100, 110])
NFL_MINUTES    = np.array([-30, -15, 0, 15, 30, 45, 60, 75, 90, 105, 120])

# ── Seed data ──────────────────────────────────────────────────────────────────

def seed(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # ── Drop all tables and recreate ──────────────────────────────────────────
    tables = [
        "env_timeseries", "env_risk", "env_conditions",
        "water_timeseries", "water_systems",
        "section_sales", "zone_status", "waste_streams",
        "energy_timeseries", "energy_systems", "events",
    ]
    for t in tables:
        cur.execute(f"DROP TABLE IF EXISTS {t}")
    conn.executescript(SCHEMA)

    # ══════════════════════════════════════════════════════════════════════════
    # SOCCER — live event
    # ══════════════════════════════════════════════════════════════════════════
    cur.execute("""
        INSERT INTO events (
            sport, is_live, event_name, venue, event_date,
            attendance, occupancy_rate, duration_min, leed_status,
            event_phase, minutes_to_next_phase, next_phase,
            max_possible_diversion_pct, max_div_target_pct,
            current_diversion_rate, next_year_target, platinum_target,
            total_waste_lb,
            energy_per_fan_kwh, energy_benchmark_kwh, total_kwh,
            water_per_fan_litres, water_guide_lpf, total_litres,
            restroom_check_done, fixture_faults,
            peak_temp_f, peak_aqi, peak_humidity_pct, peak_density_pct, env_incidents
        ) VALUES (
            'soccer', 1, 'Soccer — Pilot FC vs. Riverside United',
            'Pilot Stadium', '2026-06-06',
            64200, 0.91, 135, 'LEED Silver',
            '1ST HALF', 18, 'Halftime',
            54, 50, 0.28, 0.35, 0.75, 6890,
            1.9, 1.5, 121980,
            24.5, 20.0, 1572900,
            1, 0,
            78, 52, 65, 84, 0
        )
    """)
    soccer_live_id = cur.lastrowid

    # Energy systems
    cur.executemany(
        "INSERT INTO energy_systems (event_id, system, share_pct, status, recommendation) VALUES (?,?,?,?,?)",
        [
            (soccer_live_id, "Lighting",          0.75, "High",    "Apply adaptive dimming in low-occupancy sections"),
            (soccer_live_id, "HVAC",               0.14, "Stable",  "Zoned correctly — no action needed"),
            (soccer_live_id, "Scoreboards & AV",   0.06, "Stable",  "Within normal range"),
            (soccer_live_id, "Concessions",         0.05, "Stable",  "Within normal range"),
        ]
    )

    # Energy timeseries — soccer live
    kwh_curve = _energy_curve(121980, SOCCER_MINUTES)
    cur.executemany(
        "INSERT INTO energy_timeseries (event_id, minute, cumulative_kwh) VALUES (?,?,?)",
        [(soccer_live_id, int(m), float(v)) for m, v in zip(SOCCER_MINUTES, kwh_curve)]
    )

    # Waste streams — current_captured_lbs reflects diversion at current_diversion_rate (28%)
    cur.executemany(
        "INSERT INTO waste_streams (event_id, stream, expected_lbs, current_captured_lbs, max_recoverable_lbs, landfill_risk_lbs) VALUES (?,?,?,?,?,?)",
        [
            (soccer_live_id, "Compostable",  2100,  420, 1890, 210),
            (soccer_live_id, "Recyclable",   2800,  980, 2520, 280),
            (soccer_live_id, "Landfill",     1990,    0,    0, 1990),
        ]
    )

    # Zone status
    cur.executemany(
        "INSERT INTO zone_status (event_id, zone, density) VALUES (?,?,?)",
        [
            (soccer_live_id, "Lower Concourse East",  0.91),
            (soccer_live_id, "Gate Plaza",             0.88),
            (soccer_live_id, "Upper Concourse West",   0.78),
            (soccer_live_id, "Premium Level",          0.73),
        ]
    )

    # Section sales (approved POS fields only)
    cur.executemany(
        """INSERT INTO section_sales
           (event_id, section, zone, recyclable_pct, compostable_pct, landfill_pct,
            top_item_1, top_item_2, top_item_3)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [
            (soccer_live_id, "Lower Concourse East",  "C", 0.34, 0.14, 0.52, "Hot Dog",  "Nachos",       "Beer Can"),
            (soccer_live_id, "Gate Plaza",             "B", 0.58, 0.08, 0.34, "Beer Can", "Water Bottle", "Soda"),
            (soccer_live_id, "Premium Level",          "D", 0.44, 0.19, 0.37, "Wine Cup", "Beer Can",     "Pretzel"),
            (soccer_live_id, "Upper Concourse West",   "A", 0.41, 0.23, 0.36, "Beer Can", "Popcorn",      "Hot Dog"),
        ]
    )

    # Water systems
    cur.executemany(
        "INSERT INTO water_systems (event_id, system, share_pct, status, note) VALUES (?,?,?,?,?)",
        [
            (soccer_live_id, "Restrooms",             0.67, "Monitor", "Dominant consumer — peaks sharply at halftime. Submeter spike = immediate check."),
            (soccer_live_id, "Concessions & food prep",0.19, "Stable",  "Steady throughout event. Elevated on high-attendance nights."),
            (soccer_live_id, "HVAC & cooling",         0.09, "Stable",  "Higher in warm weather. Cooling towers account for most of this share."),
            (soccer_live_id, "Field irrigation",        0.05, "Stable",  "Confirmed off during event window. Pre- and post-event only."),
        ]
    )

    # Water timeseries
    water_curve = _water_curve(1572900, SOCCER_MINUTES)
    cur.executemany(
        "INSERT INTO water_timeseries (event_id, minute, cumulative_litres) VALUES (?,?,?)",
        [(soccer_live_id, int(m), float(v)) for m, v in zip(SOCCER_MINUTES, water_curve)]
    )

    # Environmental conditions
    cur.executemany(
        "INSERT INTO env_conditions (event_id, metric, value, unit, note, status) VALUES (?,?,?,?,?,?)",
        [
            (soccer_live_id, "outdoor_temp",      78,   "°F",  "Warm afternoon — heat risk in outdoor sections", "Monitor"),
            (soccer_live_id, "indoor_temp",       71,   "°F",  "HVAC maintaining target range",                  "Stable"),
            (soccer_live_id, "aqi",               52,   "AQI", "Moderate — acceptable but elevated",             "Monitor"),
            (soccer_live_id, "humidity",          65,   "%",   "Elevated — compounds heat stress risk",          "Monitor"),
            (soccer_live_id, "wind_speed",         8,   "mph", "Light breeze — minimal cooling effect outdoors", "Stable"),
            (soccer_live_id, "crowd_density_avg", 84,   "%",   "84% average density amplifies all thermal risks","Monitor"),
        ]
    )

    # Environmental risk cards
    cur.executemany(
        "INSERT INTO env_risk (event_id, factor, status, headline, watch, notify_if) VALUES (?,?,?,?,?,?)",
        [
            (soccer_live_id, "Heat Stress",    "Monitor",
             "78°F outdoors + 65% humidity + 84% crowd density",
             "Fans showing distress in Lower Concourse East. Medical staff response times. Water station queue lengths before halftime.",
             "Any section exceeds 92% density AND outdoor temp climbs above 85°F"),
            (soccer_live_id, "Air Quality",    "Stable",
             "AQI 52 outdoors — ventilation running at capacity",
             "AQI trend mid-event. Ventilation fault alerts. Any unusual odor reports from concourses.",
             "Outdoor AQI exceeds 100 OR any HVAC fault reported during event"),
            (soccer_live_id, "Crowd Comfort",  "Monitor",
             "High density + elevated humidity creates discomfort conditions",
             "Complaint clusters in Upper Concourse West. Restroom queue lengths. Fan movement patterns ahead of halftime.",
             "Any enclosed section density exceeds 92% during halftime surge"),
            (soccer_live_id, "Egress Safety",  "Stable",
             "Normal flow at all exits — Gate Plaza at 92% requires monitoring",
             "Gate Plaza density before and during halftime. Any exit obstruction reports. Emergency egress path clearance.",
             "Exit blockage reported OR Gate Plaza density exceeds 95%"),
        ]
    )

    # Environmental timeseries
    rng = np.random.default_rng(seed=77)
    soccer_ts_minutes = np.array([-30, -15, 0, 15, 30, 45, 60, 75, 90])
    base_temp = np.array([74, 75, 76, 77, 78, 78, 79, 78, 77], dtype=float)
    base_aqi  = np.array([42, 44, 47, 50, 52, 53, 55, 54, 52], dtype=float)
    temp_vals = (base_temp + rng.normal(0, 0.3, len(soccer_ts_minutes))).round(1)
    aqi_vals  = (base_aqi  + rng.normal(0, 1.0, len(soccer_ts_minutes))).round(1)
    cur.executemany(
        "INSERT INTO env_timeseries (event_id, minute, temp_f, aqi) VALUES (?,?,?,?)",
        [(soccer_live_id, int(m), float(t), float(a))
         for m, t, a in zip(soccer_ts_minutes, temp_vals, aqi_vals)]
    )

    # ══════════════════════════════════════════════════════════════════════════
    # SOCCER — 10 historical events
    # ══════════════════════════════════════════════════════════════════════════
    rng_h = np.random.default_rng(seed=42)
    soccer_dates = pd.date_range(end="2026-04-25", periods=10, freq="2D")
    soccer_base_kwh  = np.linspace(108_000, 118_000, 10) + rng_h.normal(0, 4_000, 10)
    soccer_base_kwh  = np.clip(soccer_base_kwh, 90_000, 140_000)
    soccer_base_div  = np.linspace(0.46, 0.52, 10)        + rng_h.normal(0, 0.025, 10)
    soccer_base_div  = np.clip(soccer_base_div, 0.40, 0.65)
    soccer_base_litr = np.linspace(1_400_000, 1_600_000, 10) + rng_h.normal(0, 60_000, 10)
    soccer_base_litr = np.clip(soccer_base_litr, 1_100_000, 2_000_000)

    for i in range(10):
        att  = int(rng_h.integers(58_000, 66_000))
        kwh  = float(soccer_base_kwh[i].round(0))
        litr = float(soccer_base_litr[i].round(0))
        cur.execute("""
            INSERT INTO events (
                sport, is_live, event_name, venue, event_date,
                attendance, occupancy_rate, duration_min,
                max_possible_diversion_pct, max_div_target_pct,
                total_kwh, energy_per_fan_kwh, energy_benchmark_kwh,
                total_litres, water_per_fan_litres, water_guide_lpf,
                peak_temp_f, peak_aqi, peak_humidity_pct, peak_density_pct
            ) VALUES (
                'soccer', 0, ?, 'Pilot Stadium', ?,
                ?, ?, 135,
                ?, 50,
                ?, ?, 1.5,
                ?, ?, 20.0,
                ?, ?, ?, ?
            )
        """, (
            f"Soccer — Event {i+1}",
            soccer_dates[i].strftime("%Y-%m-%d"),
            att, round(att / 70_500, 2),
            round(soccer_base_div[i] * 100, 1),
            kwh, round(kwh / att, 2),
            litr, round(litr / att, 1),
            float(rng_h.uniform(72, 82)), float(rng_h.uniform(40, 60)),
            float(rng_h.uniform(55, 70)), float(rng_h.uniform(75, 92)),
        ))
        eid = cur.lastrowid

        # Energy timeseries for this past event
        curve = _energy_curve(kwh, SOCCER_MINUTES)
        cur.executemany(
            "INSERT INTO energy_timeseries (event_id, minute, cumulative_kwh) VALUES (?,?,?)",
            [(eid, int(m), float(v)) for m, v in zip(SOCCER_MINUTES, curve)]
        )

        # Water timeseries for this past event
        wcurve = _water_curve(litr, SOCCER_MINUTES)
        cur.executemany(
            "INSERT INTO water_timeseries (event_id, minute, cumulative_litres) VALUES (?,?,?)",
            [(eid, int(m), float(v)) for m, v in zip(SOCCER_MINUTES, wcurve)]
        )

    # ══════════════════════════════════════════════════════════════════════════
    # NFL — live event
    # ══════════════════════════════════════════════════════════════════════════
    cur.execute("""
        INSERT INTO events (
            sport, is_live, event_name, venue, event_date,
            attendance, occupancy_rate, duration_min, leed_status,
            event_phase, minutes_to_next_phase, next_phase,
            max_possible_diversion_pct, max_div_target_pct,
            current_diversion_rate, next_year_target, platinum_target,
            total_waste_lb,
            energy_per_fan_kwh, energy_benchmark_kwh, total_kwh,
            water_per_fan_litres, water_guide_lpf, total_litres,
            restroom_check_done, fixture_faults,
            peak_temp_f, peak_aqi, peak_humidity_pct, peak_density_pct, env_incidents
        ) VALUES (
            'nfl', 1, 'NFL — Raiders vs. Chiefs',
            'Pilot Stadium', '2026-06-06',
            68500, 0.94, 210, 'LEED Gold',
            'Q2', 12, 'Halftime',
            28, 35, 0.21, 0.30, 0.75, 8240,
            2.4, 2.4, 164400,
            27.5, 20.0, 1883750,
            1, 1,
            79, 58, 62, 94, 0
        )
    """)
    nfl_live_id = cur.lastrowid

    # Energy systems — NFL
    cur.executemany(
        "INSERT INTO energy_systems (event_id, system, share_pct, status, recommendation) VALUES (?,?,?,?,?)",
        [
            (nfl_live_id, "Lighting",         0.75, "High",    "Apply adaptive dimming in low-occupancy sections"),
            (nfl_live_id, "HVAC",              0.14, "Stable",  "Zoned correctly — no action needed"),
            (nfl_live_id, "Scoreboards & AV",  0.07, "Stable",  "Within normal range"),
            (nfl_live_id, "Concessions",        0.04, "Stable",  "Within normal range"),
        ]
    )

    kwh_curve_nfl = _energy_curve(164400, NFL_MINUTES)
    cur.executemany(
        "INSERT INTO energy_timeseries (event_id, minute, cumulative_kwh) VALUES (?,?,?)",
        [(nfl_live_id, int(m), float(v)) for m, v in zip(NFL_MINUTES, kwh_curve_nfl)]
    )

    # Waste streams — NFL (current_captured_lbs reflects 21% diversion rate)
    cur.executemany(
        "INSERT INTO waste_streams (event_id, stream, expected_lbs, current_captured_lbs, max_recoverable_lbs, landfill_risk_lbs) VALUES (?,?,?,?,?,?)",
        [
            (nfl_live_id, "Compostable",  2200,  264,  616, 1584),
            (nfl_live_id, "Recyclable",   3800, 1134, 2660,  760),
            (nfl_live_id, "Landfill",     2240,    0,    0, 2240),
        ]
    )

    # Zone status — NFL
    cur.executemany(
        "INSERT INTO zone_status (event_id, zone, density) VALUES (?,?,?)",
        [
            (nfl_live_id, "Lower Concourse East",  0.93),
            (nfl_live_id, "Gate Plaza",             0.91),
            (nfl_live_id, "Upper Concourse West",   0.85),
            (nfl_live_id, "Premium Level",          0.79),
        ]
    )

    # Section sales — NFL
    cur.executemany(
        """INSERT INTO section_sales
           (event_id, section, zone, recyclable_pct, compostable_pct, landfill_pct,
            top_item_1, top_item_2, top_item_3)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [
            (nfl_live_id, "Lower Concourse East",  "C", 0.28, 0.10, 0.62, "Hot Wings", "Nachos",  "Beer Can"),
            (nfl_live_id, "Gate Plaza",             "B", 0.51, 0.07, 0.42, "Beer Can",  "Soda",    "Pretzel"),
            (nfl_live_id, "Premium Level",          "D", 0.38, 0.15, 0.47, "Whiskey Cup","Burger", "Beer Can"),
            (nfl_live_id, "Upper Concourse West",   "A", 0.35, 0.18, 0.47, "Popcorn",   "Hot Dog", "Beer Can"),
        ]
    )

    # Water systems — NFL
    cur.executemany(
        "INSERT INTO water_systems (event_id, system, share_pct, status, note) VALUES (?,?,?,?,?)",
        [
            (nfl_live_id, "Restrooms",              0.67, "Monitor", "Dominant consumer — peaks sharply at halftime. Submeter spike = immediate check."),
            (nfl_live_id, "Concessions & food prep", 0.19, "Stable",  "Steady throughout event. Elevated on high-attendance nights."),
            (nfl_live_id, "HVAC & cooling",          0.09, "Stable",  "Higher in warm weather. Cooling towers account for most of this share."),
            (nfl_live_id, "Field irrigation",         0.05, "Stable",  "Confirmed off during event window. Pre- and post-event only."),
        ]
    )

    water_curve_nfl = _water_curve(1883750, NFL_MINUTES)
    cur.executemany(
        "INSERT INTO water_timeseries (event_id, minute, cumulative_litres) VALUES (?,?,?)",
        [(nfl_live_id, int(m), float(v)) for m, v in zip(NFL_MINUTES, water_curve_nfl)]
    )

    # Environmental conditions — NFL
    cur.executemany(
        "INSERT INTO env_conditions (event_id, metric, value, unit, note, status) VALUES (?,?,?,?,?,?)",
        [
            (nfl_live_id, "outdoor_temp",      79,   "°F",  "Warm conditions — heat risk elevated for outdoor sections", "Monitor"),
            (nfl_live_id, "indoor_temp",       72,   "°F",  "HVAC maintaining target range",                            "Stable"),
            (nfl_live_id, "aqi",               58,   "AQI", "Moderate — acceptable but monitor trend",                  "Monitor"),
            (nfl_live_id, "humidity",          62,   "%",   "Moderate — compounds heat stress at high density",         "Monitor"),
            (nfl_live_id, "wind_speed",         6,   "mph", "Light breeze — limited cooling effect",                    "Stable"),
            (nfl_live_id, "crowd_density_avg", 94,   "%",   "Very high density — amplifies all thermal risks",          "High"),
        ]
    )

    # Environmental risk — NFL
    cur.executemany(
        "INSERT INTO env_risk (event_id, factor, status, headline, watch, notify_if) VALUES (?,?,?,?,?,?)",
        [
            (nfl_live_id, "Heat Stress",   "High",
             "79°F outdoors + 62% humidity + 94% crowd density",
             "Fans showing distress in any outdoor section. Medical response times. Water station queues.",
             "Any section exceeds 95% density OR outdoor temp climbs above 85°F"),
            (nfl_live_id, "Air Quality",   "Monitor",
             "AQI 58 outdoors — generator exhaust risk in parking areas",
             "AQI trend through Q3/Q4. Any tailgate generator proximity reports.",
             "Outdoor AQI exceeds 100 OR any indoor AQI reading above 75"),
            (nfl_live_id, "Crowd Comfort", "High",
             "Extreme density + humidity creates significant discomfort risk",
             "Complaint clusters. Restroom queues. Fan movement at end of Q2.",
             "Any enclosed section density exceeds 95% during Q2/Q3 transition"),
            (nfl_live_id, "Egress Safety", "Monitor",
             "Gate Plaza at 91% — halftime egress will be stressed",
             "Gate Plaza throughput at halftime. Any bottleneck reports. Emergency path clearance.",
             "Exit blockage reported OR Gate Plaza density exceeds 96%"),
        ]
    )

    # Environmental timeseries — NFL
    nfl_ts_minutes = np.array([-30, -15, 0, 15, 30, 45, 60, 75, 90, 105, 120])
    base_temp_nfl = np.array([74, 75, 76, 77, 78, 79, 79, 78, 77, 76, 75], dtype=float)
    base_aqi_nfl  = np.array([44, 46, 48, 50, 52, 55, 57, 56, 55, 54, 53], dtype=float)
    rng2 = np.random.default_rng(seed=77)
    temp_nfl = (base_temp_nfl + rng2.normal(0, 0.3, len(nfl_ts_minutes))).round(1)
    aqi_nfl  = (base_aqi_nfl  + rng2.normal(0, 1.0, len(nfl_ts_minutes))).round(1)
    cur.executemany(
        "INSERT INTO env_timeseries (event_id, minute, temp_f, aqi) VALUES (?,?,?,?)",
        [(nfl_live_id, int(m), float(t), float(a))
         for m, t, a in zip(nfl_ts_minutes, temp_nfl, aqi_nfl)]
    )

    # ══════════════════════════════════════════════════════════════════════════
    # NFL — 10 historical events
    # ══════════════════════════════════════════════════════════════════════════
    rng_n = np.random.default_rng(seed=43)
    nfl_dates    = pd.date_range(end="2026-04-25", periods=10, freq="2D")
    nfl_base_kwh = np.linspace(155_000, 175_000, 10) + rng_n.normal(0, 5_000, 10)
    nfl_base_kwh = np.clip(nfl_base_kwh, 130_000, 200_000)
    nfl_base_div = np.linspace(0.18, 0.25, 10) + rng_n.normal(0, 0.02, 10)
    nfl_base_div = np.clip(nfl_base_div, 0.12, 0.35)
    nfl_base_lit = np.linspace(1_800_000, 2_100_000, 10) + rng_n.normal(0, 80_000, 10)
    nfl_base_lit = np.clip(nfl_base_lit, 1_500_000, 2_500_000)

    for i in range(10):
        att  = int(rng_n.integers(63_000, 72_000))
        kwh  = float(nfl_base_kwh[i].round(0))
        litr = float(nfl_base_lit[i].round(0))
        cur.execute("""
            INSERT INTO events (
                sport, is_live, event_name, venue, event_date,
                attendance, occupancy_rate, duration_min,
                max_possible_diversion_pct, max_div_target_pct,
                total_kwh, energy_per_fan_kwh, energy_benchmark_kwh,
                total_litres, water_per_fan_litres, water_guide_lpf,
                peak_temp_f, peak_aqi, peak_humidity_pct, peak_density_pct
            ) VALUES (
                'nfl', 0, ?, 'Pilot Stadium', ?,
                ?, ?, 210,
                ?, 35,
                ?, ?, 2.4,
                ?, ?, 20.0,
                ?, ?, ?, ?
            )
        """, (
            f"NFL — Event {i+1}",
            nfl_dates[i].strftime("%Y-%m-%d"),
            att, round(att / 72_500, 2),
            round(nfl_base_div[i] * 100, 1),
            kwh, round(kwh / att, 2),
            litr, round(litr / att, 1),
            float(rng_n.uniform(68, 84)), float(rng_n.uniform(42, 65)),
            float(rng_n.uniform(50, 70)), float(rng_n.uniform(80, 95)),
        ))
        eid = cur.lastrowid

        curve = _energy_curve(kwh, NFL_MINUTES)
        cur.executemany(
            "INSERT INTO energy_timeseries (event_id, minute, cumulative_kwh) VALUES (?,?,?)",
            [(eid, int(m), float(v)) for m, v in zip(NFL_MINUTES, curve)]
        )

        wcurve = _water_curve(litr, NFL_MINUTES)
        cur.executemany(
            "INSERT INTO water_timeseries (event_id, minute, cumulative_litres) VALUES (?,?,?)",
            [(eid, int(m), float(v)) for m, v in zip(NFL_MINUTES, wcurve)]
        )

    conn.commit()
    print(f"[OK] Database seeded at {DB_PATH}")
    print(f"  Soccer live event ID : {soccer_live_id}")
    print(f"  NFL live event ID    : {nfl_live_id}")
    print(f"  Historical events    : 10 soccer + 10 NFL")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    try:
        seed(conn)
    finally:
        conn.close()
