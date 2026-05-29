from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.services.data_loader import load_excel_workbook


DEMO_WORKBOOK = "ArenaPulse_Demo_Data.xlsx"


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
    data = load_excel_workbook(DEMO_WORKBOOK)["Event_Context"]
    values = dict(zip(data["metric"], data["value"]))
    return EventContext(
        venue=str(values["venue"]),
        event_name=str(values["event_name"]),
        attendance=int(values["attendance"]),
        occupancy_rate=float(values["occupancy_rate"]),
        leed_status=str(values["leed_status"]),
        current_diversion_rate=float(values["current_diversion_rate"]),
        next_year_target=float(values["next_year_target"]),
        platinum_target=float(values["platinum_target"]),
        event_phase=str(values["event_phase"]),
        minutes_to_next_phase=int(values["minutes_to_next_phase"]),
        next_phase=str(values["next_phase"]),
    )


def load_waste_trend() -> pd.DataFrame:
    trend = load_excel_workbook(DEMO_WORKBOOK)["Waste_Trend"].copy()
    trend["date"] = pd.to_datetime(trend["date"])
    trend["verified_diversion_rate"] = trend["verified_diversion_rate"] * 100
    trend["target_diversion_rate"] = trend["target_diversion_rate"] * 100
    return trend


def get_waste_streams() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Waste_Streams"].copy()


def get_product_risk() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Product_Risk"].copy()


def get_section_hotspots() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Section_Hotspots"].copy()


def get_energy_snapshot() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Energy_Context"].copy()


def get_governance_feeds() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Governance_Feeds"].copy()


def get_pos_sample() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["POS_Sample"].copy()


def get_operational_summary() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Operational_Summary"].copy()


def get_water_context() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Water_Context"].copy()


def get_zone_status() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Zone_Status"].copy()


def get_environmental_conditions() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Environmental_Conditions"].copy()


def get_environmental_risk() -> pd.DataFrame:
    return load_excel_workbook(DEMO_WORKBOOK)["Environmental_Risk"].copy()


def get_waste_diversion_history(current_max_possible: float, n: int = 10) -> pd.DataFrame:
    """
    Generate realistic mock max-possible diversion history for past events.
    Max possible is based on packaging mix sold — varies event to event.
    Seeded for reproducibility in demo.
    """
    rng = np.random.default_rng(seed=42)
    dates = pd.date_range(end="2026-04-25", periods=n, freq="2D")
    # Realistic variation: most events land 46-58%, trending slightly upward
    base = np.linspace(0.46, 0.52, n)
    noise = rng.normal(0, 0.025, n)
    max_possible = np.clip(base + noise, 0.40, 0.65)
    return pd.DataFrame({
        "event": [f"Event {i+1}" for i in range(n)],
        "date": dates,
        "max_possible_pct": (max_possible * 100).round(1),
        "is_current": [False] * n,
    })


def get_energy_history(current_kwh: float, n: int = 10) -> pd.DataFrame:
    """Mock total kWh history for past events. Seeded for demo reproducibility."""
    rng = np.random.default_rng(seed=43)
    dates = pd.date_range(end="2026-04-25", periods=n, freq="2D")
    base = np.linspace(108_000, 118_000, n)
    noise = rng.normal(0, 4_000, n)
    totals = np.clip(base + noise, 90_000, 140_000)
    return pd.DataFrame({
        "event": [f"Event {i+1}" for i in range(n)],
        "date": dates,
        "total_kwh": totals.round(0),
        "is_current": [False] * n,
    })


def get_energy_timeseries(current_kwh: float, current_minute: int) -> pd.DataFrame:
    """
    Cumulative kWh through the game — tonight vs historical average.
    current_minute: game minute (0 = kickoff, 45 = halftime, 90 = full time).
    Columns: minute, label, avg_kwh, live_kwh (NaN after current_minute).
    """
    time_points = np.array([-30, -20, -10, 0, 10, 20, 30, 40, 45, 55, 65, 75, 85, 90, 100, 110])

    # Cumulative fraction of total event energy consumed at each game minute
    base_fractions = np.array([
        0.00, 0.04, 0.10, 0.17, 0.26, 0.35, 0.43, 0.48,
        0.53, 0.61, 0.70, 0.79, 0.88, 0.93, 0.97, 1.00,
    ])

    # Historical average across 10 past events
    rng = np.random.default_rng(seed=45)
    past_totals = np.clip(
        np.linspace(108_000, 118_000, 10) + rng.normal(0, 3_000, 10),
        90_000, 140_000,
    )
    avg_curves = []
    for total in past_totals:
        noise = rng.normal(0, 0.006, len(base_fractions))
        fracs = np.maximum.accumulate(np.clip(base_fractions + noise, 0, 1))
        fracs /= fracs[-1]
        avg_curves.append(fracs * total)
    avg_curve = np.mean(avg_curves, axis=0)

    # Live curve — current_kwh is the projected full-game total; show cumulative up to current_minute
    live_curve = np.where(time_points <= current_minute, base_fractions * current_kwh, np.nan)

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
        "avg_kwh":  avg_curve,
        "live_kwh": live_curve,
    })


def get_max_div_by_gametime(current_minute: int) -> pd.DataFrame:
    """
    Max possible diversion rate at each game minute, driven by packaging mix sold.
    Fluctuates as sales patterns shift — higher when drinks dominate, lower during food surges.
    Columns: minute, label, avg_pct, live_pct (NaN after current_minute).
    """
    time_points = np.array([-30, -20, -10, 0, 10, 20, 30, 40, 45, 55, 65, 75, 85, 90, 100, 110])

    # Shape: pre-game drinks (cans) → high; food surge at HT → dips; drinks return 2nd half
    base_max = np.array([
        57, 56, 54, 52, 50, 48, 47, 46,   # pre-game → 40' (food builds)
        44,                                 # HT food surge → dips
        50, 52, 54, 55, 56,                # 55'→FT (drinks dominate again)
        57, 58,                             # post-game
    ], dtype=float)

    rng = np.random.default_rng(seed=47)
    # Historical avg — slight per-event variation
    avg_curves = []
    for _ in range(10):
        noise = rng.normal(0, 1.5, len(time_points))
        avg_curves.append(np.clip(base_max + noise, 35, 70))
    avg_curve = np.mean(avg_curves, axis=0)

    # Tonight — own variation, only shown to current_minute
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


def get_section_sales_breakdown() -> list[dict]:
    """
    Section-level POS packaging breakdown for bin placement intelligence.
    Tries to aggregate from POS sample; falls back to seeded synthetic data.
    """
    try:
        pos = get_pos_sample()
        required = {"section", "item_name", "quantity", "recyclable_flag", "compostable_flag"}
        if not required.issubset(pos.columns):
            raise ValueError("Missing columns")
        result = []
        section_map = {
            "Lower Concourse East": "C",
            "Gate Plaza":           "B",
            "Premium Level":        "D",
            "Upper Concourse West": "A",
        }
        for section, zone in section_map.items():
            grp = pos[pos["section"] == section]
            if grp.empty:
                raise ValueError("No data")
            total      = grp["quantity"].sum()
            recyclable = grp.loc[grp["recyclable_flag"] == 1, "quantity"].sum()
            compostable = grp.loc[grp["compostable_flag"] == 1, "quantity"].sum()
            landfill   = max(0, total - recyclable - compostable)
            top_items  = (grp.groupby("item_name")["quantity"]
                          .sum().sort_values(ascending=False).head(3).index.tolist())
            result.append({
                "section": section, "zone": zone,
                "recyclable_pct":  recyclable  / total if total else 0,
                "compostable_pct": compostable / total if total else 0,
                "landfill_pct":    landfill    / total if total else 0,
                "top_items": top_items,
            })
        return result
    except Exception:
        pass

    # Synthetic fallback — seeded for demo reproducibility
    return [
        {
            "section": "Lower Concourse East", "zone": "C",
            "recyclable_pct": 0.34, "compostable_pct": 0.14, "landfill_pct": 0.52,
            "top_items": ["Hot Dog", "Nachos", "Beer Can"],
        },
        {
            "section": "Gate Plaza", "zone": "B",
            "recyclable_pct": 0.58, "compostable_pct": 0.08, "landfill_pct": 0.34,
            "top_items": ["Beer Can", "Water Bottle", "Soda"],
        },
        {
            "section": "Premium Level", "zone": "D",
            "recyclable_pct": 0.44, "compostable_pct": 0.19, "landfill_pct": 0.37,
            "top_items": ["Wine Cup", "Beer Can", "Pretzel"],
        },
        {
            "section": "Upper Concourse West", "zone": "A",
            "recyclable_pct": 0.41, "compostable_pct": 0.23, "landfill_pct": 0.36,
            "top_items": ["Beer Can", "Popcorn", "Hot Dog"],
        },
    ]


def get_waste_diversion_timeseries(current_div: float, current_minute: int) -> pd.DataFrame:
    """
    Estimated diversion rate % through the game — tonight vs historical average.
    current_div: current diversion rate as decimal (e.g. 0.28).
    Columns: minute, label, avg_pct, live_pct (NaN after current_minute).
    """
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


def get_water_timeseries(current_litres: float, current_minute: int) -> pd.DataFrame:
    """
    Cumulative litres through the game — tonight vs historical average.
    Noticeable halftime spike as restroom demand peaks.
    Columns: minute, label, avg_litres, live_litres (NaN after current_minute).
    """
    time_points = np.array([-30, -20, -10, 0, 10, 20, 30, 40, 45, 55, 65, 75, 85, 90, 100, 110])

    # Cumulative fraction — sharper halftime spike than energy
    base_fractions = np.array([
        0.00, 0.03, 0.07, 0.13, 0.21, 0.30, 0.38, 0.44,
        0.55,                                               # HT restroom surge
        0.63, 0.71, 0.79, 0.87, 0.92, 0.97, 1.00,
    ])

    rng = np.random.default_rng(seed=49)
    past_totals = np.clip(
        np.linspace(1_400_000, 1_600_000, 10) + rng.normal(0, 60_000, 10),
        1_100_000, 2_000_000,
    )
    avg_curves = []
    for total in past_totals:
        noise = rng.normal(0, 0.006, len(base_fractions))
        fracs = np.maximum.accumulate(np.clip(base_fractions + noise, 0, 1))
        fracs /= fracs[-1]
        avg_curves.append(fracs * total)
    avg_curve = np.mean(avg_curves, axis=0)

    live_curve = np.where(time_points <= current_minute, base_fractions * current_litres, np.nan)

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
        "minute":      time_points,
        "label":       labels,
        "avg_litres":  avg_curve,
        "live_litres": live_curve,
    })


def get_water_history(current_litres: float, n: int = 10) -> pd.DataFrame:
    """Mock total litres history for past events. Seeded for demo reproducibility."""
    rng = np.random.default_rng(seed=44)
    dates = pd.date_range(end="2026-04-25", periods=n, freq="2D")
    base = np.linspace(1_400_000, 1_600_000, n)
    noise = rng.normal(0, 60_000, n)
    totals = np.clip(base + noise, 1_100_000, 2_000_000)
    return pd.DataFrame({
        "event": [f"Event {i+1}" for i in range(n)],
        "date": dates,
        "total_litres": totals.round(0),
        "is_current": [False] * n,
    })


def get_water_by_system(total_litres: float) -> list[dict]:
    """
    Water usage breakdown by venue system.
    Shares are realistic for a modern stadium event.
    Returns list of dicts: system, share, litres, status, note.
    """
    systems = [
        {
            "system":  "Restrooms",
            "share":   0.67,
            "status":  "Monitor",
            "note":    "Dominant consumer — peaks sharply at halftime. Submeter spike = immediate check.",
        },
        {
            "system":  "Concessions & food prep",
            "share":   0.19,
            "status":  "Stable",
            "note":    "Steady throughout event. Elevated on high-attendance nights.",
        },
        {
            "system":  "HVAC & cooling",
            "share":   0.09,
            "status":  "Stable",
            "note":    "Higher in warm weather. Cooling towers account for most of this share.",
        },
        {
            "system":  "Field irrigation",
            "share":   0.05,
            "status":  "Stable",
            "note":    "Confirmed off during event window. Pre- and post-event only.",
        },
    ]
    for s in systems:
        s["litres"] = round(total_litres * s["share"])
    return systems
