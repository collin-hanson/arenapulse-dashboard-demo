import html

import streamlit as st

from src.components.arena_components import action_card, risk_alert_banner, stadium_zone_map
from src.services.demo_data import (
    get_event_context, get_operational_summary, get_waste_streams,
    get_water_context, get_zone_status,
)
from src.services.status import get_all_statuses
from src.utils.page_config import plotly_layout


# ── Helpers ────────────────────────────────────────────────────────────────────

def _phase_banner(ctx) -> str:
    return (
        '<div class="ap-phase-banner">'
        f'<span class="phase-tag">{html.escape(ctx.event_phase.upper())}</span>'
        f'<span class="phase-countdown">'
        f'{html.escape(ctx.next_phase)} in <strong>{ctx.minutes_to_next_phase} min</strong>'
        f'</span>'
        f'<span class="phase-meta">'
        f'{html.escape(ctx.venue)} &nbsp;·&nbsp; {ctx.attendance:,} fans'
        f' &nbsp;·&nbsp; {ctx.occupancy_rate:.0%} occupancy'
        f'</span>'
        '</div>'
    )


def _kpi(label: str, value: str, delta: str, delta_class: str) -> str:
    return (
        '<div class="ap-kpi">'
        f'<div class="kpi-label">{html.escape(label)}</div>'
        f'<div class="kpi-value">{html.escape(value)}</div>'
        f'<div class="kpi-delta {delta_class}">{html.escape(delta)}</div>'
        '</div>'
    )


def _zones_to_abcd(zones_df) -> tuple[dict, dict]:
    mapping = {
        "Lower Concourse East":  "C",
        "Gate Plaza":            "B",
        "Upper Concourse West":  "A",
        "Premium Level":         "D",
    }
    zone_data  = {}
    zone_names = {}
    for row in zones_df.itertuples(index=False):
        letter = mapping.get(str(row.zone))
        if letter:
            zone_data[letter]  = int(float(row.density) * 100)
            zone_names[letter] = str(row.zone)
    for letter in ["A", "B", "C", "D"]:
        zone_data.setdefault(letter, 50)
        zone_names.setdefault(letter, letter)
    return zone_data, zone_names


def _collect_live_actions(statuses, zones, ctx) -> list[dict]:
    actions = []

    ws = statuses["waste"]
    if ws.status in ("High", "Medium"):
        top_zone    = zones.sort_values("density", ascending=False).iloc[0]
        density_pct = int(float(top_zone.density) * 100)
        actions.append({
            "priority": "red",
            "title":    "Waste response",
            "kpi":      f"{density_pct}% density",
            "gap":      f"{top_zone.zone} — highest diversion leverage",
            "key":      "ov_waste_response",
            "insight":  f"Food-heavy waste + high density = best chance to lift diversion before {ctx.next_phase}.",
            "actions": [
                f"Redirect green team ambassador to {top_zone.zone}",
                "Place compost signage at hot food vendor stands",
            ],
            "impact": "Bin labelling at the highest-volume section directly lifts the diversion rate.",
        })

        gate = zones.loc[zones["zone"].str.contains("Gate", case=False)]
        if not gate.empty and float(gate.iloc[0]["density"]) >= 0.85:
            actions.append({
                "priority": "red",
                "title":    "Overflow bin risk",
                "kpi":      f"Bins at capacity by halftime",
                "gap":      f"Gate Plaza — bins will overflow during halftime surge",
                "key":      "ov_overflow",
                "insight":  f"Existing bins will hit capacity during the halftime surge in {ctx.minutes_to_next_phase} min.",
                "actions":  ["Move overflow bins to Gate Plaza now"],
                "impact":   "Prevents bin overflow and fan complaints at peak halftime volume.",
            })

    wtr = statuses["water"]
    if wtr.status in ("High", "Medium"):
        actions.append({
            "priority": "yellow",
            "title":    "Halftime restroom prep",
            "kpi":      f"{ctx.minutes_to_next_phase} min to {ctx.next_phase}",
            "gap":      "Lower Concourse East — restroom surge approaching",
            "key":      "ov_restroom",
            "insight":  "High density drives restroom demand spikes. Catch blockages before the surge.",
            "actions": [
                f"Walk restroom banks at Lower Concourse East before {ctx.next_phase}",
                "Flag any fixture fault to maintenance immediately",
            ],
            "impact": "Preventing a halftime blockage avoids a fan-facing incident at peak demand.",
        })

    env = statuses["environment"]
    if env.status in ("High", "Medium"):
        actions.append({
            "priority": "red" if env.status == "High" else "yellow",
            "title":    "Hydration demand",
            "kpi":      "78°F · 65% humidity",
            "gap":      "Gate Plaza + Lower Concourse East — water stations",
            "key":      "ov_hydration",
            "insight":  "Heat + humidity + 84% avg density = sharp hydration demand spike at halftime.",
            "actions":  ["Restock water stations at Gate Plaza and Lower Concourse East"],
            "impact":   "Reduces heat exhaustion risk and prevents empty-station complaints.",
        })

    nrg = statuses["energy"]
    if nrg.status == "High":
        actions.append({
            "priority": "yellow",
            "title":    "Lighting vs occupancy",
            "kpi":      "High load · Low occupancy",
            "gap":      "Low-occupancy sections still fully lit",
            "key":      "ov_lighting",
            "insight":  "Occupancy has dropped below 75% while lighting load stays high — act now.",
            "actions":  ["Apply adaptive lighting in confirmed low-occupancy sections"],
            "impact":   "Direct energy reduction — occupancy/lighting divergence is the trigger.",
        })

    return actions


# ── Main render ────────────────────────────────────────────────────────────────

def render_executive_scorecard() -> None:
    ctx      = get_event_context()
    waste    = get_waste_streams()
    zones    = get_zone_status()
    statuses = get_all_statuses()

    total_expected = waste["expected_lbs"].sum()
    max_div = waste["max_recoverable_lbs"].sum() / total_expected if total_expected else 0

    ops       = get_operational_summary()
    epf       = float(ops.loc[ops["metric"] == "energy_per_fan", "value"].iloc[0])
    total_kwh = epf * ctx.attendance

    water_ctx = get_water_context()
    wpf = float(water_ctx.loc[water_ctx["metric"] == "water_per_attendee", "value"].iloc[0])

    live_actions = _collect_live_actions(statuses, zones, ctx)
    zone_data, zone_names = _zones_to_abcd(zones)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown('<div class="ap-kicker">Overview</div>', unsafe_allow_html=True)
    st.title("Decision board")
    st.markdown(_phase_banner(ctx), unsafe_allow_html=True)

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(_kpi(
            "Max possible diversion", f"{max_div:.0%}",
            "Best achievable if all recoverable material is sorted", "neu"
        ), unsafe_allow_html=True)
    with k2:
        st.markdown(_kpi(
            "Total energy", f"{total_kwh:,.0f} kWh",
            f"{epf:.1f} kWh per fan — live estimate", "neu"
        ), unsafe_allow_html=True)
    with k3:
        total_litres = wpf * ctx.attendance
        delta_wpf = wpf - 20
        st.markdown(_kpi(
            "Total water", f"{total_litres:,.0f} L",
            f"{wpf:.1f} L per fan — {'▲ above' if delta_wpf > 0 else 'within'} 20 L guide",
            "neg" if delta_wpf > 0 else "neu"
        ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stadium map (full-width-ish) + zone alerts beside it ─────────────────
    st.markdown(
        '<div class="ap-section-header">🏟️ Live venue status</div>'
        '<div class="ap-section-sub">Zone density from live ticket-scan data</div>',
        unsafe_allow_html=True,
    )

    map_col, alert_col = st.columns([1.5, 1])

    with map_col:
        fig = stadium_zone_map(zone_data, title="")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption(
            "Zone density is pulled from turnstile scans and ticketing system APIs in production. "
            "In this demo, values are simulated to reflect a real high-attendance event."
        )

    with alert_col:
        from src.components.arena_components import ai_chat
        from src.services.ai_assistant import get_overview_response
        ai_chat(get_overview_response,
                placeholder="e.g. What's the highest priority right now? What should I do before halftime?",
                input_key="overview_ai_input")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Operational priorities — 2 × 2 grid ──────────────────────────────────
    st.markdown(
        '<div class="ap-section-header">🎯 Operational priorities</div>'
        '<div class="ap-section-sub">What to act on before the next phase — driven by live system status</div>',
        unsafe_allow_html=True,
    )

    if not live_actions:
        st.markdown(
            '<div class="ap-monitor-banner">'
            '✅ All systems stable — no immediate action required.'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        total = len(live_actions)
        # #1 priority — full width, most prominent
        a = live_actions[0]
        action_card(
            title=a["title"], kpi_value=a["kpi"], gap_text=a["gap"],
            insight=a["insight"], actions=a["actions"], impact=a["impact"],
            priority=a["priority"], compact=True, priority_num=1,
            card_key=a.get("key"),
        )
        # Remaining actions — up to 3 per row
        rest = live_actions[1:]
        if rest:
            cols = st.columns(len(rest))
            for i, (col, a) in enumerate(zip(cols, rest)):
                with col:
                    action_card(
                        title=a["title"], kpi_value=a["kpi"], gap_text=a["gap"],
                        insight=a["insight"], actions=a["actions"], impact=a["impact"],
                        priority=a["priority"], compact=True, priority_num=i + 2,
                        card_key=a.get("key"),
                    )
