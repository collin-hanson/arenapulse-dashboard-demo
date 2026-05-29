import html as _html

import streamlit as st

from src.services.demo_data import get_environmental_conditions, get_environmental_risk
from src.services.status import get_all_statuses


def _cond_tile(label: str, value: str, note: str, status: str) -> str:
    dot_color = {"Stable": "#12b981", "Monitor": "#e8b84d", "High": "#ff5b65"}.get(status, "#9aa8ba")
    return (
        '<div class="ap-cond-tile">'
        f'<div class="cond-label">{_html.escape(label)}</div>'
        f'<div class="cond-value" style="color:{dot_color}">{_html.escape(value)}</div>'
        f'<div class="cond-note">{_html.escape(note)}</div>'
        '</div>'
    )


def _risk_card(factor: str, status: str, headline: str, detail: str,
               watch_for: str, notify_if: str) -> str:
    cls = status.lower()
    return (
        f'<div class="ap-env-card {cls}">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.4rem">'
        f'<span class="env-factor">{_html.escape(factor)}</span>'
        f'<span class="ap-pill {cls}">{_html.escape(status)}</span>'
        f'</div>'
        f'<div class="env-headline">{_html.escape(headline)}</div>'
        f'<div class="env-detail">{_html.escape(detail)}</div>'
        f'<div class="env-watch">👁 Watch: {_html.escape(watch_for)}</div>'
        f'<div class="env-notify"><strong>Notify if:</strong> {_html.escape(notify_if)}</div>'
        '</div>'
    )


def render_environmental_health() -> None:
    conditions = get_environmental_conditions()
    risks      = get_environmental_risk()
    statuses   = get_all_statuses()
    env_status = statuses["environment"]

    cond_lookup = {row.metric: row for row in conditions.itertuples(index=False)}

    temp     = float(cond_lookup["outdoor_temp"].value)
    aqi      = float(cond_lookup["aqi"].value)
    humidity = float(cond_lookup["humidity"].value)
    density  = float(cond_lookup["crowd_density_avg"].value)

    banner_cls = {"High": "red", "Medium": "yellow", "Stable": ""}.get(env_status.status, "")

    st.markdown('<div class="ap-kicker">Environmental health</div>', unsafe_allow_html=True)
    st.title("Environmental Health")

    # ── Composite risk banner ─────────────────────────────────────────────────
    st.markdown(
        f'<div class="ap-monitor-banner {banner_cls}">'
        f'<strong>{_html.escape(env_status.status).upper()}:</strong>&nbsp;'
        f'{_html.escape(env_status.headline)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Conditions strip ──────────────────────────────────────────────────────
    st.markdown(
        '<div class="ap-conditions">'
        + _cond_tile("Outdoor temp",  f"{temp:.0f}°F",
                     cond_lookup["outdoor_temp"].note,  cond_lookup["outdoor_temp"].status)
        + _cond_tile("Indoor temp",   f"{float(cond_lookup['indoor_temp'].value):.0f}°F",
                     cond_lookup["indoor_temp"].note,   cond_lookup["indoor_temp"].status)
        + _cond_tile("AQI",           f"{aqi:.0f}",
                     cond_lookup["aqi"].note,           cond_lookup["aqi"].status)
        + _cond_tile("Humidity",      f"{humidity:.0f}%",
                     cond_lookup["humidity"].note,      cond_lookup["humidity"].status)
        + _cond_tile("Wind",          f"{float(cond_lookup['wind_speed'].value):.0f} mph",
                     cond_lookup["wind_speed"].note,    cond_lookup["wind_speed"].status)
        + _cond_tile("Avg density",   f"{density:.0%}",
                     cond_lookup["crowd_density_avg"].note, cond_lookup["crowd_density_avg"].status)
        + '</div>',
        unsafe_allow_html=True,
    )

    # ── Risk cards — always 2×2 grid ─────────────────────────────────────────
    st.markdown(
        '<div class="ap-section-header">📋 Live risk factors</div>'
        '<div class="ap-section-sub">Each factor assessed independently from live conditions</div>',
        unsafe_allow_html=True,
    )

    risk_rows = list(risks.itertuples(index=False))
    # Render in pairs: 2 columns per row
    for i in range(0, len(risk_rows), 2):
        pair = risk_rows[i:i + 2]
        cols = st.columns(len(pair))
        for col, risk in zip(cols, pair):
            with col:
                st.markdown(
                    _risk_card(
                        factor=str(risk.factor),
                        status=str(risk.status),
                        headline=str(risk.headline),
                        detail=str(risk.detail),
                        watch_for=str(risk.watch_for),
                        notify_if=str(risk.notify_if),
                    ),
                    unsafe_allow_html=True,
                )
        st.markdown("<br>", unsafe_allow_html=True)

    # ── AI assistant ──────────────────────────────────────────────────────────
    from src.components.arena_components import ai_chat
    from src.services.ai_assistant import get_env_response
    ai_chat(get_env_response,
            placeholder="e.g. Why is heat stress elevated? What should I watch for at halftime?",
            input_key="env_ai_input")
