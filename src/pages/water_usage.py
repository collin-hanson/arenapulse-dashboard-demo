import html as _html

import plotly.graph_objects as go
import streamlit as st

from src.services.demo_data import (
    get_current_minute, get_event_context, get_water_context,
    get_water_history, get_water_timeseries, get_water_by_system,
)
from src.services.status import get_all_statuses
from src.utils.page_config import plotly_layout


def render_water_usage() -> None:
    water    = get_water_context()
    ctx      = get_event_context()
    statuses = get_all_statuses()
    s        = statuses["water"]

    lookup       = {row.metric: row for row in water.itertuples(index=False)}
    wpf          = float(lookup["water_per_attendee"].value)
    total_litres = wpf * ctx.attendance

    history    = get_water_history(total_litres)
    avg_litres = history["total_litres"].mean()
    delta_l    = total_litres - avg_litres

    banner_cls = {"High": "red", "Medium": "yellow", "Stable": ""}.get(s.status, "")

    st.markdown('<div class="ap-kicker">Water</div>', unsafe_allow_html=True)
    st.title("Water")

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
            _kpi("Total water", f"{total_litres:,.0f} L",
                 f"{wpf:.1f} L per fan — estimated from venue submeters", "neu"),
            unsafe_allow_html=True,
        )
    with k2:
        direction = "▲" if delta_l > 0 else "▼"
        delta_cls = "neg" if delta_l > 0 else "pos"
        st.markdown(
            _kpi("vs. 10-event avg",
                 f"{direction} {abs(delta_l):,.0f} L",
                 f"Avg: {avg_litres:,.0f} L · {'above' if delta_l > 0 else 'below'} average tonight",
                 delta_cls),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Water pace — tonight vs avg ───────────────────────────────────────────
    current_minute = get_current_minute(ctx)

    st.markdown(
        '<div class="ap-section-header">📈 Water pace — tonight vs average</div>'
        f'<div class="ap-section-sub">Cumulative litres through the game · '
        f'halftime spike reflects restroom demand peak · '
        f'{ctx.event_phase} · {ctx.minutes_to_next_phase} min to {ctx.next_phase}</div>',
        unsafe_allow_html=True,
    )

    ts = get_water_timeseries(total_litres, current_minute)
    live_now = ts.dropna(subset=["live_litres"]).iloc[-1]

    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=ts["minute"], y=ts["avg_litres"],
        mode="lines+markers",
        line={"color": "#6b7a8d", "width": 2},
        marker={"size": 5, "color": "#6b7a8d"},
        name="10-event avg",
        hovertemplate="%{customdata}: %{y:,.0f} L avg<extra></extra>",
        customdata=ts["label"],
    ))
    fig_ts.add_trace(go.Scatter(
        x=ts["minute"], y=ts["live_litres"],
        mode="lines+markers",
        line={"color": "#16d9e8", "width": 2.5},
        marker={"size": 5, "color": "#16d9e8"},
        name="Tonight",
        connectgaps=False,
        hovertemplate="%{customdata}: %{y:,.0f} L tonight<extra></extra>",
        customdata=ts["label"],
    ))
    fig_ts.add_trace(go.Scatter(
        x=[live_now["minute"]], y=[live_now["live_litres"]],
        mode="markers",
        marker={"size": 11, "color": "#16d9e8",
                "line": {"color": "#101722", "width": 2}},
        showlegend=False, hoverinfo="skip",
    ))
    fig_ts.update_layout(
        yaxis=dict(title="Cumulative litres", tickformat=","),
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

    # ── Usage by system ───────────────────────────────────────────────────────
    st.subheader("Usage by system")
    st.caption("Estimated split from venue submeters — restrooms dominate on event nights")

    status_colors = {"Monitor": "#e8b84d", "Stable": "#12b981", "High": "#ff5b65"}
    systems = get_water_by_system(total_litres)
    for sys in systems:
        bar_color = status_colors.get(sys["status"], "#16d9e8")
        pill_cls  = sys["status"].lower()
        pct_width = f"{sys['share']:.0%}"
        st.markdown(
            f'<div style="background:#151c25;border:1px solid #2b3645;border-radius:10px;'
            f'padding:10px 14px;margin-bottom:6px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">'
            f'<strong style="color:#f4f7fb;font-size:13px;">{_html.escape(sys["system"])}</strong>'
            f'<span class="ap-pill {pill_cls}">{_html.escape(sys["status"])}</span>'
            f'</div>'
            f'<div style="background:#2b3645;border-radius:4px;height:5px;margin-bottom:5px;">'
            f'<div style="background:{bar_color};width:{pct_width};height:5px;border-radius:4px;"></div>'
            f'</div>'
            f'<span style="font-size:11px;color:#9aa8ba;">'
            f'{pct_width} of total · {sys["litres"]:,} L estimated · {_html.escape(sys["note"])}'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── AI assistant ──────────────────────────────────────────────────────────
    from src.components.arena_components import ai_chat
    from src.services.ai_assistant import get_water_response
    ai_chat(get_water_response,
            placeholder="e.g. Is tonight's usage unusually high? Which system is driving the increase?",
            input_key="water_ai_input")
