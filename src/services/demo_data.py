from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

from src.services import db
from src.services.data_loader import load_excel_workbook


DEMO_WORKBOOK = "ArenaPulse_Demo_Data.xlsx"


# ── Sport helpers ──────────────────────────────────────────────────────────────

def _get_sport() -> str:
    return st.session_state.get("sport", "soccer")


def _live_event() -> dict:
    return db.get_live_event(_get_sport())


def _make_time_labels(time_points, sport: str) -> list[str]:
    labels = []
    for m in time_points:
        if sport == "nfl":
            if m < 0:      labels.append("Pre-game")
            elif m == 0:   labels.append("KO")
            elif m <= 15:  labels.append("Q1")
            elif m <= 40:  labels.append("Q2")
            elif m == 45:  labels.append("HT")
            elif m <= 65:  labels.append("Q3")
            elif m <= 85:  labels.append("Q4")
            elif m == 90:  labels.append("Final")
            elif m <= 100: labels.append("OT")
            else:           labels.append("Post")
        else:
            if m == -30:   labels.append("Pre-game")
            elif m < 0:    labels.append(f"{m}'")
            elif m == 0:   labels.append("KO")
            elif m == 45:  labels.append("HT")
            elif m == 90:  labels.append("FT")
            elif m > 90:   labels.append(f"+{m - 90}'")
            else:           labels.append(f"{m}'")
    return labels


def get_current_minute(ctx: "EventContext") -> int:
    phase_map = {
        "1ST HALF": 45,
        "2ND HALF": 90,
        "Q1": 15,
        "Q2": 45,
        "Q3": 65,
        "Q4": 85,
    }
    end = phase_map.get(ctx.event_phase.upper(), 0)
    return max(0, end - ctx.minutes_to_next_phase)


@dataclass(frozen=True)
class EventContext:
    venue: str
    event_name: str
    attendance: int
    occupancy_rate: float
    leed_status: str
    current_diversion_rate: float
    next_year_target: float
    platinum_target: float
    event_phase: str
    minutes_to_next_phase: int
    next_phase: str


def get_event_context() -> EventContext:
    e = _live_event()
    return EventContext(
        venue=str(e["venue"]),
        event_name=str(e["event_name"]),
        attendance=int(e["attendance"]),
        occupancy_rate=float(e["occupancy_rate"]),
        leed_status=str(e["leed_status"] or ""),
        current_diversion_rate=float(e["current_diversion_rate"]),
        next_year_target=float(e["next_year_target"]),
        platinum_target=float(e["platinum_target"]),
        event_phase=str(e["event_phase"]),
        minutes_to_next_phase=int(e["minutes_to_next_phase"]),
        next_phase=str(e["next_phase"]),
    )


# ── Waste ──────────────────────────────────────────────────────────────────────

def load_waste_trend() -> pd.DataFrame:
    trend = load_excel_workbook(DEMO_WORKBOOK)["Waste_Trend"].copy()
    trend["date"] = pd.to_datetime(trend["date"])
    trend["verified_diversion_rate"] = trend["verified_diversion_rate"] * 100
    trend["target_diversion_rate"] = trend["target_diversion_rate"] * 100
    return trend


def get_waste_streams() -> pd.DataFrame:
    e = _live_event()
    return db.get_waste_streams(e["event_id"])


def get_product_risk() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Product_Risk"].copy()


def get_section_hotspots() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Section_Hotspots"].copy()


def get_waste_diversion_history(current_max_possible: float, n: int = 10) -> pd.DataFrame:
    df = db.get_waste_diversion_history(_get_sport(), n)
    df = df.copy()
    df["event"] = [f"Event {i+1}" for i in range(len(df))]
    df["is_current"] = False
    df["date"] = pd.to_datetime(df["date"])
    return df[["event", "date", "max_possible_pct", "is_current"]]


def get_section_sales_breakdown() -> list[dict]:
    e = _live_event()
    rows = db.get_section_sales(e["event_id"])
    result = []
    for row in rows.itertuples(index=False):
        result.append({
            "section":         row.section,
            "zone":            row.zone,
            "recyclable_pct":  row.recyclable_pct,
            "compostable_pct": row.compostable_pct,
            "landfill_pct":    row.landfill_pct,
            "top_items":       [x for x in [row.top_item_1, row.top_item_2, row.top_item_3] if x],
        })
    return result


def get_waste_diversion_timeseries(current_div: float, current_minute: int) -> pd.DataFrame:
    time_points = np.array([-30, -20, -10, 0, 10, 20, 30, 40, 45, 55, 65, 75, 85, 90, 100, 110])
    base_fractions = np.array([
        0.00, 0.02, 0.06, 0.12, 0.20, 0.30, 0.38, 0.45,
        0.52, 0.62, 0.70, 0.78, 0.86, 0.92, 0.97, 1.00,
    ])
    rng = np.random.default_rng(seed=46)
    past_finals = np.clip(
        np.linspace(0.44, 0.50, 10) + rng.normal(0, 0.015, 10), 0.35, 0.60
    )
    avg_curves = []
    for final in past_finals:
        noise = rng.normal(0, 0.005, len(base_fractions))
        fracs = np.maximum.accumulate(np.clip(base_fractions + noise, 0, 1))
        fracs /= fracs[-1]
        avg_curves.append(fracs * final * 100)
    avg_curve = np.mean(avg_curves, axis=0)

    current_fraction = float(np.interp(current_minute, time_points, base_fractions))
    scale = current_div / current_fraction if current_fraction > 0 else current_div
    live_curve = np.where(time_points <= current_minute, base_fractions * scale * 100, np.nan)

    labels = []
    for m in time_points:
        if m == -30:  labels.append("Pre-game")
        elif m < 0:   labels.append(f"{m}'")
        elif m == 0:  labels.append("KO")
        elif m == 45: labels.append("HT")
        elif m == 90: labels.append("FT")
        elif m > 90:  labels.append(f"+{m - 90}'")
        else:         labels.append(f"{m}'")

    return pd.DataFrame({
        "minute":   time_points,
        "label":    labels,
        "avg_pct":  avg_curve,
        "live_pct": live_curve,
    })


def get_max_div_by_gametime(current_minute: int) -> pd.DataFrame:
    time_points = np.array([-30, -20, -10, 0, 10, 20, 30, 40, 45, 55, 65, 75, 85, 90, 100, 110])
    base_max = np.array([
        57, 56, 54, 52, 50, 48, 47, 46,
        44,
        50, 52, 54, 55, 56,
        57, 58,
    ], dtype=float)
    rng = np.random.default_rng(seed=47)
    avg_curves = []
    for _ in range(10):
        noise = rng.normal(0, 1.5, len(time_points))
        avg_curves.append(np.clip(base_max + noise, 35, 70))
    avg_curve = np.mean(avg_curves, axis=0)
    tonight = np.clip(base_max + rng.normal(0, 2.0, len(time_points)), 35, 70)
    live_curve = np.where(time_points <= current_minute, tonight, np.nan)

    labels = []
    for m in time_points:
        if m == -30:  labels.append("Pre-game")
        elif m < 0:   labels.append(f"{m}'")
        elif m == 0:  labels.append("KO")
        elif m == 45: labels.append("HT")
        elif m == 90: labels.append("FT")
        elif m > 90:  labels.append(f"+{m - 90}'")
        else:         labels.append(f"{m}'")

    return pd.DataFrame({
        "minute":   time_points,
        "label":    labels,
        "avg_pct":  avg_curve,
        "live_pct": live_curve,
    })


# ── Energy ─────────────────────────────────────────────────────────────────────

def get_energy_snapshot() -> pd.DataFrame:
    e = _live_event()
    return db.get_energy_systems(e["event_id"])


def get_governance_feeds() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Governance_Feeds"].copy()


def get_operational_summary() -> pd.DataFrame:
    e = _live_event()
    return pd.DataFrame([
        {"metric": "energy_per_fan",  "value": float(e["energy_per_fan_kwh"]), "status": "Medium"},
        {"metric": "carbon_intensity", "value": 92.1 if _get_sport() == "nfl" else 78.4, "status": "Medium"},
    ])


def get_energy_history(current_kwh: float, n: int = 10) -> pd.DataFrame:
    df = db.get_past_events(_get_sport(), n)
    df = df.copy()
    df["event"] = [f"Event {i+1}" for i in range(len(df))]
    df["is_current"] = False
    df = df.rename(columns={"event_date": "date"})
    df["date"] = pd.to_datetime(df["date"])
    return df[["event", "date", "total_kwh", "is_current"]]


def get_energy_timeseries(current_kwh: float, current_minute: int) -> pd.DataFrame:
    sport = _get_sport()
    e = _live_event()

    live_ts  = db.get_energy_timeseries(e["event_id"])
    avg_ts   = db.get_energy_timeseries_avg(sport)

    minutes  = live_ts["minute"].to_numpy()
    live_kwh = np.where(minutes <= current_minute, live_ts["cumulative_kwh"].to_numpy(), np.nan)

    avg_kwh  = np.interp(minutes, avg_ts["minute"].to_numpy(), avg_ts["avg_kwh"].to_numpy())

    return pd.DataFrame({
        "minute":   minutes,
        "label":    _make_time_labels(minutes, sport),
        "avg_kwh":  avg_kwh,
        "live_kwh": live_kwh,
    })


# ── Water ──────────────────────────────────────────────────────────────────────

def get_water_context() -> pd.DataFrame:
    e = _live_event()
    return pd.DataFrame([
        {"metric": "water_per_attendee", "value": float(e["water_per_fan_litres"])},
    ])


def get_pos_sample() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["POS_Sample"].copy()


def get_zone_status() -> pd.DataFrame:
    e = _live_event()
    return db.get_zone_status(e["event_id"])


def get_water_history(current_litres: float, n: int = 10) -> pd.DataFrame:
    df = db.get_past_events(_get_sport(), n)
    df = df.copy()
    df["event"] = [f"Event {i+1}" for i in range(len(df))]
    df["is_current"] = False
    df = df.rename(columns={"event_date": "date"})
    df["date"] = pd.to_datetime(df["date"])
    return df[["event", "date", "total_litres", "is_current"]]


def get_water_timeseries(current_litres: float, current_minute: int) -> pd.DataFrame:
    sport = _get_sport()
    e = _live_event()

    live_ts   = db.get_water_timeseries(e["event_id"])
    avg_ts    = db.get_water_timeseries_avg(sport)

    minutes   = live_ts["minute"].to_numpy()
    live_litr = np.where(minutes <= current_minute, live_ts["cumulative_litres"].to_numpy(), np.nan)
    avg_litr  = np.interp(minutes, avg_ts["minute"].to_numpy(), avg_ts["avg_litres"].to_numpy())

    return pd.DataFrame({
        "minute":      minutes,
        "label":       _make_time_labels(minutes, sport),
        "avg_litres":  avg_litr,
        "live_litres": live_litr,
    })


def get_water_by_system(total_litres: float) -> list[dict]:
    e = _live_event()
    rows = db.get_water_systems(e["event_id"])
    result = []
    for row in rows.itertuples(index=False):
        result.append({
            "system": row.system,
            "share":  row.share,
            "litres": round(total_litres * row.share),
            "status": row.status,
            "note":   row.note,
        })
    return result


# ── Environmental ──────────────────────────────────────────────────────────────

def get_environmental_conditions() -> pd.DataFrame:
    e = _live_event()
    return db.get_env_conditions(e["event_id"])


def get_environmental_risk() -> pd.DataFrame:
    e = _live_event()
    return db.get_env_risk(e["event_id"])


def get_env_timeseries(current_minute: int) -> pd.DataFrame:
    sport = _get_sport()
    e = _live_event()

    ts      = db.get_env_timeseries(e["event_id"])
    minutes = ts["minute"].to_numpy()
    temp_f  = ts["temp_f"].to_numpy()
    aqi     = ts["aqi"].to_numpy()

    live_temp = np.where(minutes <= current_minute, temp_f, np.nan)
    live_aqi  = np.where(minutes <= current_minute, aqi,    np.nan)

    return pd.DataFrame({
        "minute":    minutes,
        "label":     _make_time_labels(minutes, sport),
        "temp_f":    temp_f,
        "aqi":       aqi,
        "live_temp": live_temp,
        "live_aqi":  live_aqi,
    })


# ── Post-event ─────────────────────────────────────────────────────────────────

def get_post_event_summary() -> dict:
    e = _live_event()
    sport = _get_sport()

    if sport == "nfl":
        incidents = [
            "Gate Plaza bins reached 95% capacity during Q3 surge",
            "Restroom fixture fault flagged in Lower Concourse East — resolved in 8 min",
            "Zone B density peaked at 94% at halftime",
        ]
        actions_taken = [
            "Overflow bins repositioned to Gate Plaza before halftime",
            "Maintenance dispatched to Lower Concourse East restrooms",
            "Green team redirected to Lower Concourse East at Q2",
        ]
    else:
        incidents = [
            "Gate Plaza bins reached overflow capacity at halftime",
            "Zone B density peaked at 92% during halftime surge",
            "Water usage 25% above 20 L guide — restroom demand driven by high occupancy",
        ]
        actions_taken = [
            "Overflow bins repositioned to Gate Plaza 15 min before halftime",
            "Green team ambassador redirected to Lower Concourse East at 30'",
            "Compost signage placed at hot food vendor stands in Zone C",
        ]

    return {
        "event_name":                 e["event_name"],
        "venue":                      e["venue"],
        "date":                       "June 6, 2026",
        "attendance":                 int(e["attendance"]),
        "occupancy_rate":             float(e["occupancy_rate"]),
        "duration_min":               int(e["duration_min"]),
        "peak_temp_f":                float(e["peak_temp_f"]),
        "peak_aqi":                   float(e["peak_aqi"]),
        "peak_humidity_pct":          float(e["peak_humidity_pct"]),
        "max_possible_diversion_pct": float(e["max_possible_diversion_pct"]),
        "max_div_target_pct":         float(e["max_div_target_pct"]),
        "total_waste_lb":             float(e["total_waste_lb"]),
        "final_kwh_per_fan":          float(e["energy_per_fan_kwh"]),
        "energy_benchmark_kwh":       float(e["energy_benchmark_kwh"]),
        "total_kwh":                  float(e["total_kwh"]),
        "final_lpf":                  float(e["water_per_fan_litres"]),
        "water_guide_lpf":            float(e["water_guide_lpf"]),
        "total_litres":               float(e["total_litres"]),
        "restroom_check_done":        bool(e["restroom_check_done"]),
        "fixture_faults":             int(e["fixture_faults"]),
        "peak_density_pct":           float(e["peak_density_pct"]),
        "env_incidents":              int(e["env_incidents"]),
        "incidents":                  incidents,
        "actions_taken":              actions_taken,
    }
