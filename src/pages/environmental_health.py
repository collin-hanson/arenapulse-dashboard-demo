import html as _html

import plotly.graph_objects as go
import streamlit as st

from src.components.arena_components import action_card, ai_chat
from src.services.ai_assistant import get_env_response
from src.services.demo_data import (
    get_current_minute,
    get_env_timeseries,
    get_environmental_conditions,
    get_environmental_risk,
    get_event_context,
)
from src.services.status import get_all_statuses
from src.utils.page_config import plotly_layout


# ── Helpers ────────────────────────────────────────────────────────────────────

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


# ── Main render ────────────────────────────────────────────────────────────────

def render_environmental_health() -> None:
    conditions = get_environmental_conditions()
    risks      = get_environmental_risk()
    statuses   = get_all_statuses()
    env_status = statuses["environment"]
    ctx        = get_event_context()

    cond_lookup = {row.metric: row for row in conditions.itertuples(index=False)}

    temp     = float(cond_lookup["outdoor_temp"].value)
    aqi      = float(cond_lookup["aqi"].value)
    humidity = float(cond_lookup["humidity"].value)
    density  = float(cond_lookup["crowd_density_avg"].value)

    banner_cls = {"High": "red", "Medium": "yellow", "Stable": ""}.get(env_status.status, "")

    st.markdown('<div class="ap-kicker">Environmental health</div>', unsafe_allow_html=True)
    st.title("Environmental Health")

    # ── Status banner ─────────────────────────────────────────────────────────
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

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Priority action card ──────────────────────────────────────────────────
    st.markdown(
        '<div class="ap-section-header">🎯 Priority actions</div>',
        unsafe_allow_html=True,
    )

    if env_status.status == "High":
        action_card(
            title="Heat stress + crowd density — act now",
            kpi_value=f"{temp:.0f}°F · {humidity:.0f}% humidity · {density:.0%} avg density",
            gap_text="Gate Plaza + Lower Concourse East — high density + heat",
            insight=(
                f"The combination of {temp:.0f}°F heat, {humidity:.0f}% humidity, and "
                f"{density:.0%} crowd density creates real heat stress risk. "
                f"Hydration demand will spike at {ctx.next_phase} in {ctx.minutes_to_next_phase} min."
            ),
            actions=[
                f"Restock water stations at Gate Plaza and Lower Concourse East now",
                "Position medical staff at high-density zones before next phase",
                "Open additional concourse ventilation if available",
            ],
            impact=(
                "Proactive water restocking and medical positioning prevents heat incidents "
                "before the crowd surge at phase change."
            ),
            priority="red",
            card_key="env_heat_stress",
        )
    elif env_status.status == "Medium":
        action_card(
            title="Heat conditions — monitor hydration demand",
            kpi_value=f"{temp:.0f}°F · {humidity:.0f}% humidity",
            gap_text=f"Watch for density spike at {ctx.next_phase}",
            insight=(
                f"Conditions are elevated but not yet critical. "
                f"With {density:.0%} average density and {ctx.minutes_to_next_phase} min "
                f"to {ctx.next_phase}, check water station stock levels now."
            ),
            actions=[
                "Confirm water station stock levels before phase change",
                "Flag any zone where density exceeds 90% to supervisor",
            ],
            impact=(
                "Catching a low water station before halftime surge is the difference "
                "between a fan complaint and a heat incident."
            ),
            priority="yellow",
            card_key="env_heat_monitor",
        )
    else:
        st.markdown(
            '<div class="ap-monitor-banner">'
            '✅ Environmental conditions stable — no immediate action required.'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Temp & AQI trend chart ────────────────────────────────────────────────
    current_minute = get_current_minute(ctx)
    ts = get_env_timeseries(current_minute)

    st.markdown(
        '<div class="ap-section-header">📈 Conditions trend — temperature & AQI</div>'
        f'<div class="ap-section-sub">Live readings through the event · '
        f'{ctx.event_phase} · {ctx.minutes_to_next_phase} min to {ctx.next_phase}</div>',
        unsafe_allow_html=True,
    )

    fig = go.Figure()

    # Faint full forecast line for temp
    fig.add_trace(go.Scatter(
        x=ts["minute"], y=ts["temp_f"],
        mode="lines",
        line={"color": "#ff5b65", "width": 1, "dash": "dot"},
        opacity=0.3,
        name="Temp forecast",
        hoverinfo="skip",
        showlegend=False,
    ))
    # Live temp line
    fig.add_trace(go.Scatter(
        x=ts["minute"], y=ts["live_temp"],
        mode="lines+markers",
        line={"color": "#ff5b65", "width": 2.5},
        marker={"size": 5, "color": "#ff5b65"},
        name="Temp (°F)",
        yaxis="y1",
        hovertemplate="%{customdata}: %{y:.1f}°F<extra></extra>",
        customdata=ts["label"],
    ))

    # Pulse dot — live temp
    live_temp_now = ts.dropna(subset=["live_temp"]).iloc[-1]
    fig.add_trace(go.Scatter(
        x=[live_temp_now["minute"]], y=[live_temp_now["live_temp"]],
        mode="markers",
        marker={"size": 11, "color": "#ff5b65", "line": {"color": "#101722", "width": 2}},
        yaxis="y1",
        showlegend=False,
        hoverinfo="skip",
    ))

    # Faint full forecast for AQI
    fig.add_trace(go.Scatter(
        x=ts["minute"], y=ts["aqi"],
        mode="lines",
        line={"color": "#e8b84d", "width": 1, "dash": "dot"},
        opacity=0.3,
        name="AQI forecast",
        yaxis="y2",
        hoverinfo="skip",
        showlegend=False,
    ))
    # Live AQI line
    fig.add_trace(go.Scatter(
        x=ts["minute"], y=ts["live_aqi"],
        mode="lines+markers",
        line={"color": "#e8b84d", "width": 2.5},
        marker={"size": 5, "color": "#e8b84d"},
        name="AQI",
        yaxis="y2",
        hovertemplate="%{customdata}: AQI %{y:.0f}<extra></extra>",
        customdata=ts["label"],
    ))

    # Pulse dot — live AQI
    live_aqi_now = ts.dropna(subset=["live_aqi"]).iloc[-1]
    fig.add_trace(go.Scatter(
        x=[live_aqi_now["minute"]], y=[live_aqi_now["live_aqi"]],
        mode="markers",
        marker={"size": 11, "color": "#e8b84d", "line": {"color": "#101722", "width": 2}},
        yaxis="y2",
        showlegend=False,
        hoverinfo="skip",
    ))

    fig.update_layout(
        yaxis=dict(
            title="Temperature (°F)",
            titlefont={"color": "#ff5b65"},
            tickfont={"color": "#ff5b65"},
            tickformat=".0f",
            range=[60, 100],
        ),
        yaxis2=dict(
            title="AQI",
            titlefont={"color": "#e8b84d"},
            tickfont={"color": "#e8b84d"},
            overlaying="y",
            side="right",
            range=[0, 150],
        ),
        xaxis=dict(
            tickvals=ts["minute"].tolist(),
            ticktext=ts["label"].tolist(),
            title="",
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="#9aa8ba", size=12),
        ),
    )

    st.plotly_chart(plotly_layout(fig, 300), use_container_width=True,
                    config={"displayModeBar": False})

    st.caption(
        "Temperature and AQI readings from stadium weather station. "
        "AQI thresholds: 0–50 Good · 51–100 Moderate · 101+ Unhealthy for sensitive groups."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Risk factor cards ─────────────────────────────────────────────────────
    st.markdown(
        '<div class="ap-section-header">📋 Live risk factors</div>'
        '<div class="ap-section-sub">Each factor assessed independently from live conditions</div>',
        unsafe_allow_html=True,
    )

    risk_rows = list(risks.itertuples(index=False))
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
    ai_chat(get_env_response,
            placeholder="e.g. Why is heat stress elevated? What should I watch for at halftime?",
            input_key="env_ai_input")
