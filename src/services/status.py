"""
Central status computation module.
All four system statuses are derived here from live data.
The sidebar, priority cards, and page banners all read from this module.
Nothing is hardcoded — status comes from the data.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.services.demo_data import (
    get_energy_snapshot,
    get_environmental_conditions,
    get_event_context,
    get_operational_summary,
    get_waste_streams,
    get_water_context,
)


@dataclass
class SystemStatus:
    system: str
    status: str          # "High" | "Medium" | "Stable"
    headline: str        # one-line summary shown in priority card
    actions: list[str] = field(default_factory=list)   # bullet points
    impact: str = ""     # impact line at bottom of priority card


def status_emoji(status: str) -> str:
    return {"High": "🔴", "Medium": "🟡", "Stable": "🟢"}.get(status, "⚪")


def _waste_status() -> SystemStatus:
    streams = get_waste_streams()
    ctx = get_event_context()
    total_expected = streams["expected_lbs"].sum()
    current_div = streams["current_captured_lbs"].sum() / total_expected if total_expected else 0
    max_div = streams["max_recoverable_lbs"].sum() / total_expected if total_expected else 0
    gap = max_div - current_div
    gap_pts = round(gap * 100)
    landfill_lbs = int(total_expected - streams["current_captured_lbs"].sum())

    if gap > 0.20:
        status = "High"
    elif gap > 0.08:
        status = "Medium"
    else:
        status = "Stable"

    return SystemStatus(
        system="Waste",
        status=status,
        headline=f"Diversion gap — {gap_pts} pts below max possible ({max_div:.0%})",
        actions=[
            f"Redirect green team ambassador to Lower Concourse East before {ctx.next_phase}",
            "Pre-position compost signage at hot food vendor stands",
            "Stage overflow bins at Gate Plaza ahead of halftime surge",
        ],
        impact=f"Closing the gap recovers ~{landfill_lbs:,} lb from landfill this event",
    )


def _energy_status() -> SystemStatus:
    energy = get_energy_snapshot()
    ctx = get_event_context()
    ops = get_operational_summary()

    lighting_row = energy.loc[energy["system"] == "Lighting"].iloc[0]
    lighting_share = float(lighting_row["share"])
    carbon_row = ops.loc[ops["metric"] == "carbon_intensity"].iloc[0]
    carbon_status = str(carbon_row["status"])

    # Only urgent if lighting is high AND occupancy is dropping (divergence signal)
    # For demo: occupancy is 91% — no divergence yet → Monitor
    if carbon_status == "High" and lighting_share > 0.70 and ctx.occupancy_rate < 0.75:
        status = "High"
        headline = f"Lighting at {lighting_share:.0%} with occupancy below 75% — act now"
        actions = [
            "Apply adaptive lighting mode to confirmed low-occupancy sections",
            "Notify facilities — dimming authorization required",
            "Re-check occupancy scan in 15 minutes",
        ]
        impact = "Adaptive lighting in low-occupancy zones can reduce load by 15–20%"
    elif lighting_share > 0.70:
        status = "Medium"
        headline = f"Lighting at {lighting_share:.0%} of tracked load — watching for occupancy divergence"
        actions = [
            "Monitor section occupancy scans — act if density drops below 75% while lighting stays high",
            "Prepare adaptive lighting mode but do not trigger yet",
        ]
        impact = "No action until occupancy and lighting load diverge"
    else:
        status = "Stable"
        headline = f"Energy load is within expected range — no action needed"
        actions = ["Continue monitoring — review carbon trend post-event"]
        impact = "Energy is background context this event"

    return SystemStatus(system="Energy", status=status, headline=headline,
                        actions=actions, impact=impact)


def _water_status() -> SystemStatus:
    water = get_water_context()
    ctx = get_event_context()
    lookup = {row.metric: row for row in water.itertuples(index=False)}
    wpf = float(lookup["water_per_attendee"].value)

    if wpf > 30:
        status = "High"
        headline = f"{wpf:.1f} L/fan — significantly above 20 L guide, check for active leak"
        actions = [
            "Dispatch maintenance to check for active leaks or fixture faults",
            "Audit restroom fixture status in high-traffic areas",
        ]
        impact = "Active fault resolution could reduce usage by 10–15% immediately"
    elif wpf > 20:
        status = "Medium"
        headline = f"{wpf:.1f} L/fan — above 20 L guide, monitor restroom demand"
        actions = [
            f"Monitor restroom queues before {ctx.next_phase} — surge expected",
            "Flag any fixture fault to maintenance — do not wait for post-event report",
        ]
        impact = "No immediate live action unless a fault is reported"
    else:
        status = "Stable"
        headline = f"{wpf:.1f} L/fan — within guide, no action needed"
        actions = ["Continue monitoring — no action required"]
        impact = "Water is within acceptable range this event"

    return SystemStatus(system="Water", status=status, headline=headline,
                        actions=actions, impact=impact)


def _environment_status() -> SystemStatus:
    env = get_environmental_conditions()
    lookup = {row.metric: row for row in env.itertuples(index=False)}

    temp = float(lookup["outdoor_temp"].value)
    aqi = float(lookup["aqi"].value)
    humidity = float(lookup["humidity"].value)
    density = float(lookup["crowd_density_avg"].value)

    # Composite risk logic
    heat_risk = temp > 85 or (temp > 75 and humidity > 65 and density > 0.82)
    air_risk = aqi > 100
    comfort_risk = humidity > 70 and density > 0.85

    if heat_risk or air_risk:
        status = "High"
        headline = f"{temp:.0f}°F / AQI {aqi:.0f} / {humidity:.0f}% humidity — heat stress risk active"
        actions = [
            "Pre-position medical staff in Lower Concourse East and Gate Plaza",
            "Activate additional water distribution stations at high-density zones",
            "Brief security on heat exhaustion recognition protocol",
        ]
        impact = "Proactive positioning reduces medical response time by 3–5 min in dense zones"
    elif comfort_risk or (temp > 75 and humidity > 60) or aqi > 50:
        status = "Medium"
        headline = f"{temp:.0f}°F outdoor, {humidity:.0f}% humidity, {density:.0%} avg density — monitor comfort"
        actions = [
            "Watch for discomfort clustering in enclosed Upper Concourse sections",
            "Confirm water stations are stocked ahead of halftime",
            "Monitor ventilation status in enclosed concourses",
        ]
        impact = "No action unless conditions worsen or complaints cluster in one zone"
    else:
        status = "Stable"
        headline = f"Environmental conditions within normal range — no action needed"
        actions = ["Continue monitoring — conditions stable"]
        impact = "Environmental health is not a live concern this event"

    return SystemStatus(system="Environment", status=status, headline=headline,
                        actions=actions, impact=impact)


def get_all_statuses() -> dict[str, SystemStatus]:
    """Compute live status for all four operational systems from data."""
    return {
        "waste":       _waste_status(),
        "energy":      _energy_status(),
        "water":       _water_status(),
        "environment": _environment_status(),
    }
