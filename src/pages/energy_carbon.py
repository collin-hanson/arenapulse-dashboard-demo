import html as _html

import plotly.graph_objects as go
import streamlit as st

from src.components.arena_components import action_card
from src.services.demo_data import (
    get_current_minute, get_energy_history, get_energy_snapshot,
    get_energy_timeseries, get_event_context, get_operational_summary,
)
from src.services.status import get_all_statuses
from src.utils.page_config import plotly_layout


def render_energy_carbon() -> None:
    energy   = get_energy_snapshot()
    ops      = get_operational_summary()
    statuses = get_all_statuses()
    s        = statuses["energy"]
    ctx      = get_event_context()

    epf_row        = ops.loc[ops["metric"] == "energy_per_fan"].iloc[0]
    energy_per_fan = float(epf_row["value"])
    total_kwh      = energy_per_fan * ctx.attendance

    lighting_row   = energy.loc[energy["system"] == "Lighting"].iloc[0]
    lighting_share = float(lighting_row["share"])

    history   = get_energy_history(total_kwh)
    avg_kwh   = history["total_kwh"].mean()
    delta_kwh = total_kwh - avg_kwh

    banner_cls = {"High": "red", "Medium": "yellow", "Stable": ""}.get(s.status, "")

    st.markdown('<div class="ap-kicker">Energy</div>', unsafe_allow_html=True)
    st.title("Energy")

    st.markdown(
        f'<div class="ap-monitor-banner {banner_cls}">'
        f'<strong>{_html.escape(s.status).upper()}:</strong>&nbsp;{_html.escape(s.headline)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── KPI row ───────────────────────────────────────────────────────────────
    def _kpi(label, value, delta, cls):
        return (
            f'<div class="ap-kpi"><div class="kpi-label">{_html.escape(label)}</div>'
            f'<div class="kpi-value">{_html.escape(value)}</div>'
            f'<div class="kpi-delta {cls}">{_html.escape(delta)}</div></div>'
        )

    k1, k2 = st.columns(2)
    with k1:
        st.markdown(
            _kpi("Total energy", f"{total_kwh:,.0f} kWh",
                 f"{energy_per_fan:.1f} kWh per fan — live estimate", "neu"),
            unsafe_allow_html=True,
        )
    with k2:
        direction = "▲" if delta_kwh > 0 else "▼"
        delta_cls = "neg" if delta_kwh > 0 else "pos"
        st.markdown(
            _kpi("vs. 10-event avg",
                 f"{direction} {abs(delta_kwh):,.0f} kWh",
                 f"Avg: {avg_kwh:,.0f} kWh · {'above' if delta_kwh > 0 else 'below'} average tonight",
                 delta_cls),
            unsafe_allow_html=True,
        )


    # ── Priority action card (full width) ────────────────────────────────────
    st.markdown(
        '<div class="ap-section-header">🎯 Priority actions</div>',
        unsafe_allow_html=True,
    )

    if s.status == "High":
        action_card(
            title="Lighting vs occupancy divergence",
            kpi_value=f"{lighting_share:.0%} lighting load",
            gap_text="Occupancy below 75% — lighting still at full load",
            insight=(
                "This is the trigger: occupancy has dropped in confirmed sections while "
                "lighting remains high. Not just load percentage alone."
            ),
            actions=[
                "Apply adaptive lighting in confirmed low-occupancy sections",
                "Check HVAC zoning — unoccupied sections may be over-conditioned",
            ],
            impact=(
                f"Lighting is {lighting_share:.0%} of tracked load. "
                "Adaptive dimming in empty zones is the highest-leverage energy action."
            ),
            priority="red",
            card_key="energy_lighting_high",
        )
    elif s.status == "Medium":
        action_card(
            title="Lighting load — watch for divergence",
            kpi_value=f"{lighting_share:.0%} lighting load",
            gap_text="Monitor for occupancy drop in any section",
            insight=(
                "Lighting is high but occupancy hasn't diverged yet. "
                "Watch section-by-section — act when a zone empties out."
            ),
            actions=[
                "Monitor lower bowl sections for occupancy drop",
                "Pre-identify which zones can be dimmed if needed",
            ],
            impact=(
                "Adaptive lighting is only triggered by actual divergence — "
                "this prepares the response, not a preventive dim."
            ),
            priority="yellow",
            card_key="energy_lighting_medium",
        )
    else:
        st.markdown(
            '<div class="ap-monitor-banner">'
            '✅ Energy is stable — no occupancy/lighting divergence detected. '
            'No action required right now.'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Energy pace — tonight vs avg ──────────────────────────────────────────
    current_minute = get_current_minute(ctx)

    st.markdown(
        '<div class="ap-section-header">📈 Energy pace — tonight vs average</div>'
        f'<div class="ap-section-sub">Cumulative kWh through the game · '
        f'{ctx.event_phase} · {ctx.minutes_to_next_phase} min to {ctx.next_phase}</div>',
        unsafe_allow_html=True,
    )

    ts = get_energy_timeseries(total_kwh, current_minute)
    live_now = ts.dropna(subset=["live_kwh"]).iloc[-1]

    fig_ts = go.Figure()

    # Gray avg line — same style as live line
    fig_ts.add_trace(go.Scatter(
        x=ts["minute"], y=ts["avg_kwh"],
        mode="lines+markers",
        line={"color": "#6b7a8d", "width": 2},
        marker={"size": 5, "color": "#6b7a8d"},
        name="10-event avg",
        hovertemplate="%{customdata}: %{y:,.0f} kWh avg<extra></extra>",
        customdata=ts["label"],
    ))
    # Cyan live line
    fig_ts.add_trace(go.Scatter(
        x=ts["minute"], y=ts["live_kwh"],
        mode="lines+markers",
        line={"color": "#16d9e8", "width": 2.5},
        marker={"size": 5, "color": "#16d9e8"},
        name="Tonight",
        connectgaps=False,
        hovertemplate="%{customdata}: %{y:,.0f} kWh tonight<extra></extra>",
        customdata=ts["label"],
    ))
    # Pulse dot at current position
    fig_ts.add_trace(go.Scatter(
        x=[live_now["minute"]], y=[live_now["live_kwh"]],
        mode="markers",
        marker={"size": 11, "color": "#16d9e8",
                "line": {"color": "#101722", "width": 2}},
        showlegend=False,
        hoverinfo="skip",
    ))

    fig_ts.update_layout(
        yaxis=dict(title="Cumulative kWh", tickformat=","),
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
    st.plotly_chart(plotly_layout(fig_ts, 300), use_container_width=True,
                    config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # ── System detail — donut + recommendation rows ───────────────────────────
    st.markdown(
        '<div class="ap-section-header">⚡ System detail</div>'
        '<div class="ap-section-sub">Live load by system — tracked from building management</div>',
        unsafe_allow_html=True,
    )

    color_map = {"High": "#ff5b65", "Monitor": "#e8b84d", "Stable": "#12b981"}
    systems      = [row.system      for row in energy.itertuples(index=False)]
    shares       = [row.share       for row in energy.itertuples(index=False)]
    statuses_sys = [row.status      for row in energy.itertuples(index=False)]
    colors       = [color_map.get(s, "#16d9e8") for s in statuses_sys]

    fig_donut = go.Figure(go.Pie(
        labels=systems,
        values=shares,
        hole=0.62,
        marker={"colors": colors, "line": {"color": "#0b1017", "width": 2}},
        textinfo="label+percent",
        textfont={"color": "#f4f7fb", "size": 12},
        hovertemplate="%{label}: %{percent}<extra></extra>",
        direction="clockwise",
        sort=False,
    ))
    fig_donut.update_layout(
        showlegend=False,
        margin={"t": 40, "b": 20, "l": 20, "r": 20},
    )

    # ── kWh/fan — last 10 events bar chart ───────────────────────────────────
    hist = get_energy_history(total_kwh)
    bar_colors = ["#16d9e8" if i == len(hist) - 1 else "#2b3645"
                  for i in range(len(hist))]
    epf_vals = [round(row.total_kwh / ctx.attendance, 2)
                for row in hist.itertuples(index=False)]
    fig_bar = go.Figure(go.Bar(
        x=hist["event"].tolist(),
        y=epf_vals,
        marker={"color": bar_colors, "line": {"width": 0}},
        hovertemplate="%{x}: %{y:.2f} kWh/fan<extra></extra>",
    ))
    fig_bar.add_hline(
        y=sum(epf_vals) / len(epf_vals),
        line={"color": "#6b7a8d", "dash": "dot", "width": 1.5},
        annotation_text="10-event avg",
        annotation_font_color="#6b7a8d",
        annotation_position="top left",
    )
    fig_bar.update_layout(
        yaxis=dict(title="kWh / fan", gridcolor="#1e2d3d"),
        xaxis=dict(title="", tickfont={"color": "#9aa8ba", "size": 10}),
        margin={"t": 40, "b": 20, "l": 40, "r": 20},
    )

    donut_col, bar_col = st.columns(2)
    with donut_col:
        st.plotly_chart(plotly_layout(fig_donut, 300), use_container_width=True,
                        config={"displayModeBar": False})
    with bar_col:
        st.plotly_chart(plotly_layout(fig_bar, 300), use_container_width=True,
                        config={"displayModeBar": False})

    # ── AI assistant ──────────────────────────────────────────────────────────
    from src.components.arena_components import ai_chat
    from src.services.ai_assistant import get_energy_response
    ai_chat(get_energy_response,
            placeholder="e.g. Why is lighting load high? What should I watch for at halftime?",
            input_key="energy_ai_input")
