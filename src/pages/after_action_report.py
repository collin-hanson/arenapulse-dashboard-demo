import html as _html

import streamlit as st

from src.services.demo_data import get_post_event_summary
from src.services.ai_assistant import get_aar_response
from src.components.arena_components import ai_chat


# ── Helpers ────────────────────────────────────────────────────────────────────

def _status_pill(met: bool) -> str:
    if met:
        return '<span style="background:rgba(18,185,129,.18);color:#12b981;border-radius:999px;padding:3px 10px;font-size:11px;font-weight:700;">✓ Target met</span>'
    return '<span style="background:rgba(232,184,77,.18);color:#e8b84d;border-radius:999px;padding:3px 10px;font-size:11px;font-weight:700;">↓ Below target</span>'


def _system_card(icon: str, system: str, actual: str, target: str, met: bool, insight: str) -> str:
    border = "#12b981" if met else "#e8b84d"
    bg     = "rgba(18,185,129,.06)" if met else "rgba(232,184,77,.06)"
    return (
        f'<div style="background:#151c25;border:1px solid {border};border-radius:12px;padding:18px 20px;">'
        f'<div style="font-size:12px;font-weight:700;color:#9aa8ba;text-transform:uppercase;'
        f'letter-spacing:.06em;margin-bottom:10px;">{icon} {_html.escape(system)}</div>'
        f'<div style="font-size:28px;font-weight:800;color:#f4f7fb;margin-bottom:4px;">{_html.escape(actual)}</div>'
        f'<div style="font-size:12px;color:#9aa8ba;margin-bottom:10px;">Target: {_html.escape(target)}</div>'
        f'{_status_pill(met)}'
        f'<div style="font-size:12px;color:#9aa8ba;margin-top:10px;line-height:1.5;">{_html.escape(insight)}</div>'
        f'</div>'
    )


def _incident_row(text: str, kind: str = "incident") -> str:
    color = "#e8b84d" if kind == "incident" else "#12b981"
    icon  = "⚠" if kind == "incident" else "✓"
    return (
        f'<div style="display:flex;gap:10px;align-items:flex-start;padding:8px 0;'
        f'border-bottom:1px solid #1e2d3d;">'
        f'<span style="color:{color};font-size:14px;margin-top:1px;">{icon}</span>'
        f'<span style="font-size:13px;color:#f4f7fb;">{_html.escape(text)}</span>'
        f'</div>'
    )


# ── Main render ────────────────────────────────────────────────────────────────

def render_after_action_report() -> None:
    d = get_post_event_summary()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown('<div class="ap-kicker">Post-Event</div>', unsafe_allow_html=True)
    st.title("After Action Report")

    st.markdown(
        f'<div class="ap-monitor-banner">'
        f'<strong>{_html.escape(d["event_name"])}</strong>'
        f'&nbsp;·&nbsp;{_html.escape(d["date"])}'
        f'&nbsp;·&nbsp;{d["attendance"]:,} fans'
        f'&nbsp;·&nbsp;{d["occupancy_rate"]:.0%} occupancy'
        f'&nbsp;·&nbsp;{d["duration_min"]} min'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Overall score ─────────────────────────────────────────────────────────
    waste_met  = d["final_diversion_pct"] >= d["diversion_target_pct"]
    energy_met = d["final_kwh_per_fan"]   <= d["energy_benchmark_kwh"]
    water_met  = d["final_lpf"]           <= d["water_guide_lpf"]
    env_met    = d["env_incidents"]       == 0
    targets_hit = sum([waste_met, energy_met, water_met, env_met])

    score_color = "#12b981" if targets_hit >= 3 else "#e8b84d" if targets_hit == 2 else "#ff5b65"
    st.markdown(
        f'<div style="background:#151c25;border:1px solid {score_color};border-radius:12px;'
        f'padding:18px 24px;margin-bottom:20px;display:flex;align-items:center;gap:20px;">'
        f'<div style="font-size:42px;font-weight:800;color:{score_color};">{targets_hit}/4</div>'
        f'<div>'
        f'<div style="font-size:15px;font-weight:700;color:#f4f7fb;">Sustainability targets met</div>'
        f'<div style="font-size:12px;color:#9aa8ba;margin-top:3px;">'
        f'Waste · Energy · Water · Environmental Health</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── System performance cards ───────────────────────────────────────────────
    st.markdown(
        '<div class="ap-section-header">📊 System performance</div>'
        '<div class="ap-section-sub">Final event totals vs. targets</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(_system_card(
            "♻️", "Waste",
            actual=f"{d['final_diversion_pct']}% diversion",
            target=f"{d['diversion_target_pct']}% diversion",
            met=waste_met,
            insight=(
                "Food-heavy packaging mix in Lower Concourse East was the primary constraint. "
                "Procurement switch to compostable serveware is the highest-leverage long-term action."
            ),
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(_system_card(
            "⚡", "Energy",
            actual=f"{d['final_kwh_per_fan']:.1f} kWh/fan",
            target=f"{d['energy_benchmark_kwh']:.1f} kWh/fan benchmark",
            met=energy_met,
            insight=(
                "Lighting load stayed elevated through second half. Adaptive dimming was not "
                "triggered — occupancy divergence threshold was not reached in any section."
            ),
        ), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown(_system_card(
            "💧", "Water",
            actual=f"{d['final_lpf']:.1f} L/fan",
            target=f"{d['water_guide_lpf']:.0f} L/fan guide",
            met=water_met,
            insight=(
                "Usage above guide driven by restroom demand at high occupancy. "
                "No fixture faults detected. Submeters showed no anomalies post-event."
            ),
        ), unsafe_allow_html=True)
    with c4:
        st.markdown(_system_card(
            "🌿", "Environmental Health",
            actual=f"{d['peak_density_pct']}% peak density",
            target="No heat/AQI incidents",
            met=env_met,
            insight=(
                f"Peak conditions: {d['peak_temp_f']}°F, AQI {d['peak_aqi']}, "
                f"{d['peak_humidity_pct']}% humidity. No medical incidents reported. "
                "Water station restocks were completed before halftime."
            ),
        ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Notable moments ────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown(
            '<div class="ap-section-header">⚠️ Incidents & alerts</div>',
            unsafe_allow_html=True,
        )
        rows = "".join(_incident_row(i, "incident") for i in d["incidents"])
        st.markdown(
            f'<div style="background:#151c25;border:1px solid #2b3645;border-radius:10px;'
            f'padding:12px 16px;">{rows}</div>',
            unsafe_allow_html=True,
        )

    with col_r:
        st.markdown(
            '<div class="ap-section-header">✅ Actions taken</div>',
            unsafe_allow_html=True,
        )
        rows = "".join(_incident_row(a, "action") for a in d["actions_taken"])
        st.markdown(
            f'<div style="background:#151c25;border:1px solid #2b3645;border-radius:10px;'
            f'padding:12px 16px;">{rows}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AI recommendations ────────────────────────────────────────────────────
    st.markdown(
        '<div class="ap-section-header">🤖 AI — Recommendations for next event</div>'
        '<div class="ap-section-sub">Ask the AI what to adjust, prepare, or flag before the next match</div>',
        unsafe_allow_html=True,
    )
    ai_chat(
        get_aar_response,
        placeholder="e.g. What should we do differently next event? What were the biggest gaps tonight?",
        input_key="aar_ai_input",
    )
