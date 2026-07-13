import html as _html

import plotly.graph_objects as go
import streamlit as st

from src.components.arena_components import action_card, ai_chat
from src.services.demo_data import (
    get_current_minute,
    get_event_context,
    get_product_risk,
    get_section_hotspots,
    get_section_sales_breakdown,
    get_waste_streams,
    get_waste_diversion_timeseries,
)
from src.services.status import get_all_statuses
from src.utils.page_config import plotly_layout

# ── Zone packaging panel ───────────────────────────────────────────────────────
def _zone_packaging_panel(section_data: list[dict]) -> None:
    """
    2×2 grid of zone cards. Each card shows packaging split from POS + bin recommendation.
    """
    def _bin_rec(rec_pct, comp_pct, landfill_pct):
        if rec_pct >= 0.50:
            return "#16d9e8", "Prioritize recycling bins — high can/bottle volume"
        elif comp_pct >= 0.20:
            return "#12b981", "Add compost bins — food packaging heavy"
        elif landfill_pct >= 0.55:
            return "#e8b84d", "Monitor — high unavoidable waste, limit bin moves"
        else:
            return "#9aa8ba", "Current bin mix sufficient — maintain coverage"

    def _card(s: dict) -> str:
        rec  = s["recyclable_pct"]
        comp = s["compostable_pct"]
        land = s["landfill_pct"]
        rec_w  = f"{rec:.0%}"
        comp_w = f"{comp:.0%}"
        land_w = f"{land:.0%}"
        items_html = "".join(
            f'<span style="background:#1e2d3d;color:#9aa8ba;border-radius:999px;'
            f'padding:2px 8px;font-size:10px;margin-right:4px;">{_html.escape(i)}</span>'
            for i in s["top_items"]
        )
        rec_color, rec_text = _bin_rec(rec, comp, land)
        return (
            f'<div style="background:#151c25;border:1px solid #2b3645;border-radius:12px;'
            f'padding:14px 16px;height:100%;">'
            # Header
            f'<div style="font-size:13px;font-weight:700;color:#f4f7fb;margin-bottom:10px;">'
            f'{_html.escape(s["section"])}</div>'
            # Top items
            f'<div style="margin-bottom:10px;">{items_html}</div>'
            # Stacked bar
            f'<div style="display:flex;height:10px;border-radius:5px;overflow:hidden;margin-bottom:6px;">'
            f'<div style="width:{rec_w};background:#16d9e8;" title="Recyclable {rec_w}"></div>'
            f'<div style="width:{comp_w};background:#12b981;" title="Compostable {comp_w}"></div>'
            f'<div style="width:{land_w};background:#ff5b65;opacity:.7;" title="Landfill {land_w}"></div>'
            f'</div>'
            # Bar legend
            f'<div style="display:flex;gap:12px;font-size:10px;color:#9aa8ba;margin-bottom:12px;">'
            f'<span><span style="color:#16d9e8;">■</span> Recyclable {rec_w}</span>'
            f'<span><span style="color:#12b981;">■</span> Compostable {comp_w}</span>'
            f'<span><span style="color:#ff5b65;">■</span> Landfill {land_w}</span>'
            f'</div>'
            # Recommendation
            f'<div style="background:#0d1017;border-left:3px solid {rec_color};'
            f'border-radius:6px;padding:8px 10px;font-size:11px;font-weight:600;color:{rec_color};">'
            f'→ {_html.escape(rec_text)}</div>'
            f'</div>'
        )

    # 2×2 grid
    for i in range(0, len(section_data), 2):
        pair = section_data[i:i + 2]
        cols = st.columns(len(pair))
        for col, s in zip(cols, pair):
            with col:
                st.markdown(_card(s), unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)


# ── Product risk rows ──────────────────────────────────────────────────────────
def _product_row(row) -> str:
    color_map = {"High": "#ff5b65", "Medium": "#e8b84d", "Low": "#12b981"}
    rgb_map   = {"High": "255,91,101", "Medium": "232,184,77", "Low": "18,185,129"}
    risk  = row.landfill_risk
    color = color_map.get(risk, "#9aa8ba")
    rgb   = rgb_map.get(risk, "154,168,186")
    pill  = (
        f'<span style="background:rgba({rgb},.18);color:{color};border-radius:999px;'
        f'padding:.18rem .55rem;font-size:.7rem;font-weight:850;white-space:nowrap">'
        f'{_html.escape(risk)}</span>'
    )
    return (
        '<div class="ap-row" style="align-items:flex-start;gap:.75rem">'
        "<div style='flex:1;min-width:0'>"
        f"<strong>{_html.escape(row.product)}</strong>"
        f"<small>{_html.escape(row.packaging_type)} &mdash; {_html.escape(row.waste_stream)}"
        f" &mdash; {row.units_sold:,} units sold</small>"
        f"<div style='color:#9aa8ba;font-size:.8rem;margin-top:.15rem'>{_html.escape(row.note)}</div>"
        "</div>"
        f"{pill}"
        "</div>"
    )


# ── Main render ────────────────────────────────────────────────────────────────
def render_waste_intelligence() -> None:
    ctx      = get_event_context()
    streams  = get_waste_streams()
    hotspots = get_section_hotspots()
    products = get_product_risk()
    statuses = get_all_statuses()
    s        = statuses["waste"]

    total_expected = streams["expected_lbs"].sum()
    current_div    = streams["current_captured_lbs"].sum() / total_expected
    max_div        = streams["max_recoverable_lbs"].sum() / total_expected
    gap_pts        = round((max_div - current_div) * 100)
    landfill_lbs   = total_expected - streams["current_captured_lbs"].sum()

    banner_cls = {"High": "red", "Medium": "yellow", "Stable": ""}.get(s.status, "")

    st.markdown('<div class="ap-kicker">Waste</div>', unsafe_allow_html=True)
    st.title("Waste")

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
        st.markdown(_kpi("Max possible diversion", f"{max_div:.0%}",
                         "Ceiling if all recoverable material is sorted tonight", "neu"),
                    unsafe_allow_html=True)
    with k2:
        st.markdown(_kpi("Est. landfill", f"{landfill_lbs:,.0f} lb",
                         "Based on packaging sold — verified by hauler post-event", "neg"),
                    unsafe_allow_html=True)


    # ── Diversion rate — tonight vs average ──────────────────────────────────
    current_minute = get_current_minute(ctx)

    st.markdown(
        '<div class="ap-section-header">📈 Diversion rate — tonight vs average</div>'
        f'<div class="ap-section-sub">How diversion is building through the game · '
        f'{ctx.event_phase} · {ctx.minutes_to_next_phase} min to {ctx.next_phase}</div>',
        unsafe_allow_html=True,
    )

    ts = get_waste_diversion_timeseries(current_div, current_minute)
    live_now = ts.dropna(subset=["live_pct"]).iloc[-1]

    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=ts["minute"], y=ts["avg_pct"],
        mode="lines+markers",
        line={"color": "#6b7a8d", "width": 2},
        marker={"size": 5, "color": "#6b7a8d"},
        name="10-event avg",
        hovertemplate="%{customdata}: %{y:.1f}% avg<extra></extra>",
        customdata=ts["label"],
    ))
    fig_ts.add_trace(go.Scatter(
        x=ts["minute"], y=ts["live_pct"],
        mode="lines+markers",
        line={"color": "#16d9e8", "width": 2.5},
        marker={"size": 5, "color": "#16d9e8"},
        name="Tonight",
        connectgaps=False,
        hovertemplate="%{customdata}: %{y:.1f}% tonight<extra></extra>",
        customdata=ts["label"],
    ))
    fig_ts.add_trace(go.Scatter(
        x=[live_now["minute"]], y=[live_now["live_pct"]],
        mode="markers",
        marker={"size": 11, "color": "#16d9e8",
                "line": {"color": "#101722", "width": 2}},
        showlegend=False, hoverinfo="skip",
    ))
    fig_ts.update_layout(
        yaxis=dict(title="Diversion rate (%)", tickformat=".0f"),
        xaxis=dict(tickvals=ts["minute"].tolist(), ticktext=ts["label"].tolist(), title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color="#9aa8ba", size=12)),
    )
    st.plotly_chart(plotly_layout(fig_ts, 280), use_container_width=True,
                    config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Priority action cards ─────────────────────────────────────────────────
    st.markdown(
        '<div class="ap-section-header">🎯 Priority actions</div>'
        '<div class="ap-section-sub">What to do right now to close the gap</div>',
        unsafe_allow_html=True,
    )

    actions = []
    top = hotspots.sort_values("waste_lbs", ascending=False).iloc[0]
    actions.append({
        "priority": "red" if s.status == "High" else "yellow",
        "title":    "Diversion opportunity — act now",
        "kpi":      f"{top.waste_lbs:,} lb",
        "gap":      f"{top.section} — {top.risk} risk",
        "key":      "waste_diversion",
        "insight":  (
            f"Highest waste volume section — food-heavy, best chance to lift diversion "
            f"before {ctx.next_phase} in {ctx.minutes_to_next_phase} min."
        ),
        "actions": [
            f"Redirect green team ambassador to {top.section}",
            "Place compost signage at hot food vendor stands in this section",
            "Confirm bin coverage before halftime surge",
        ],
        "impact": f"Compostable packaging is the largest stream — bin labelling directly lifts diversion. {gap_pts} pts still recoverable.",
    })

    gate = hotspots.loc[hotspots["section"].str.contains("Gate", case=False)]
    if not gate.empty and str(gate.iloc[0].risk) in ("High", "Medium"):
        gr = gate.iloc[0]
        actions.append({
            "priority": "red",
            "title":    "Overflow bin risk",
            "kpi":      f"{gr.waste_lbs:,} lb",
            "gap":      "Gate Plaza — bins near capacity before halftime",
            "key":      "waste_overflow",
            "insight":  f"Halftime surge in {ctx.minutes_to_next_phase} min will push existing bins over capacity.",
            "actions":  ["Move overflow bins to Gate Plaza now", "Pre-position 2 extra compost bins"],
            "impact":   "Prevents overflow and fan complaints at peak halftime volume.",
        })

    for i in range(0, len(actions), 2):
        pair = actions[i:i + 2]
        cols = st.columns(len(pair))
        for col, a in zip(cols, pair):
            with col:
                action_card(
                    title=a["title"], kpi_value=a["kpi"], gap_text=a["gap"],
                    insight=a["insight"], actions=a["actions"],
                    impact=a["impact"], priority=a["priority"],
                    card_key=a.get("key"),
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Zone packaging panel ──────────────────────────────────────────────────
    st.markdown(
        '<div class="ap-section-header">📍 Bin placement intelligence</div>'
        '<div class="ap-section-sub">Live POS packaging mix by zone — tells you where to move which bins right now</div>',
        unsafe_allow_html=True,
    )
    section_data = get_section_sales_breakdown()
    _zone_packaging_panel(section_data)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Procurement flags (expander) ──────────────────────────────────────────
    with st.expander("Procurement flags — packaging risk by product"):
        st.caption(
            "Unavoidable landfill waste by packaging type. "
            "Purchasing intelligence for future events — not a game-night action."
        )
        top_landfill = (
            products[products["landfill_risk"] == "High"]
            .sort_values("units_sold", ascending=False)
            .head(3)
        )
        if not top_landfill.empty:
            st.markdown(
                '<div style="font-size:.72rem;font-weight:850;letter-spacing:.07em;'
                'text-transform:uppercase;color:#ff5b65;margin-bottom:8px;">'
                'Top landfill contributors tonight</div>',
                unsafe_allow_html=True,
            )
            for row in top_landfill.itertuples(index=False):
                est_lbs = int(row.units_sold * 0.12)
                st.markdown(
                    f'<div style="background:#151c25;border-left:3px solid #ff5b65;'
                    f'border-radius:6px;padding:8px 12px;margin-bottom:6px;font-size:.8rem;">'
                    f'<strong style="color:#f4f7fb">{_html.escape(row.product)}</strong>'
                    f'<span style="color:#9aa8ba;margin:0 6px">·</span>'
                    f'<span style="color:#9aa8ba">{_html.escape(row.packaging_type)}</span>'
                    f'<div style="color:#ff5b65;font-weight:700;margin-top:3px;">'
                    f'~{est_lbs:,} lb unavoidable · {row.units_sold:,} units sold</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("<br>", unsafe_allow_html=True)

        products_sorted = products.sort_values("units_sold", ascending=False)
        rows_html = "".join(_product_row(row) for row in products_sorted.itertuples(index=False))
        st.markdown(f'<div class="ap-panel">{rows_html}</div>', unsafe_allow_html=True)

    # ── AI assistant ──────────────────────────────────────────────────────────
    from src.services.ai_assistant import get_waste_response
    ai_chat(get_waste_response,
            placeholder="e.g. Why is diversion low? Which zones should I prioritise?",
            input_key="waste_ai_input")
