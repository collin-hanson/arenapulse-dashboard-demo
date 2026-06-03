"""
Shared visual components — adapted from agribeiro17/arenapulse_dashboard.
Stadium map, action card, and alert banner used across all pages.
"""
import html as _html

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ── Colour palette ─────────────────────────────────────────────────────────────
C = {
    "card_bg":  "#151c25",
    "plot_bg":  "#101722",
    "text":     "#f4f7fb",
    "subtext":  "#9aa8ba",
    "border":   "#2b3645",
    "accent1":  "#16d9e8",   # cyan
    "accent2":  "#12b981",   # teal / green
    "accent3":  "#ff5b65",   # red
    "accent4":  "#e8b84d",   # yellow
}


# ── Stadium zone map ───────────────────────────────────────────────────────────
def stadium_zone_map(zone_data: dict, title: str = "Venue zone density") -> go.Figure:
    """
    zone_data = {"A": 60, "B": 75, "C": 92, "D": 55}  (% capacity, 0–100)
    Renders a top-down oval stadium with 4 curved stand zones.
    A = West, B = North, C = East, D = South
    """
    def zone_color(pct):
        if pct >= 88:
            return ("#ff5b65", "rgba(255,91,101,0.55)",  "rgba(255,91,101,0.15)")
        elif pct >= 72:
            return ("#e8b84d", "rgba(232,184,77,0.55)",  "rgba(232,184,77,0.15)")
        else:
            return ("#12b981", "rgba(18,185,129,0.55)",  "rgba(18,185,129,0.12)")

    def zone_label(pct):
        if pct >= 88:   return "High"
        elif pct >= 72: return "Medium"
        else:           return "Stable"

    fig = go.Figure()

    t = np.linspace(0, 2 * np.pi, 300)

    # Outer stadium ring (dark concrete)
    ox, oy = 1.55 * np.cos(t), 1.0 * np.sin(t)
    fig.add_trace(go.Scatter(
        x=ox, y=oy, fill="toself",
        fillcolor="rgba(20,28,40,0.95)",
        line={"color": "#3a4a5e", "width": 2},
        hoverinfo="skip", showlegend=False,
    ))

    # Inner oval (concourse / track gap)
    ix, iy = 0.95 * np.cos(t), 0.60 * np.sin(t)
    fig.add_trace(go.Scatter(
        x=ix, y=iy, fill="toself",
        fillcolor="rgba(12,18,28,0.8)",
        line={"color": "#2a3a50", "width": 1},
        hoverinfo="skip", showlegend=False,
    ))

    # Pitch (green rectangle)
    fig.add_shape(type="rect", x0=-0.70, y0=-0.38, x1=0.70, y1=0.38,
                  fillcolor="#1a5c1a", line={"color": "#2a8c2a", "width": 2})
    # Pitch stripes
    for xi in np.linspace(-0.70, 0.70, 8):
        fig.add_shape(type="line", x0=xi, y0=-0.38, x1=xi, y1=0.38,
                      line={"color": "rgba(30,100,30,0.4)", "width": 6})
    # Centre line + circle + spot
    fig.add_shape(type="line", x0=0, y0=-0.38, x1=0, y1=0.38,
                  line={"color": "rgba(255,255,255,0.35)", "width": 1})
    fig.add_shape(type="circle", x0=-0.14, y0=-0.14, x1=0.14, y1=0.14,
                  fillcolor="rgba(0,0,0,0)",
                  line={"color": "rgba(255,255,255,0.35)", "width": 1})
    fig.add_shape(type="circle", x0=-0.02, y0=-0.02, x1=0.02, y1=0.02,
                  fillcolor="rgba(255,255,255,0.4)",
                  line={"color": "rgba(255,255,255,0.4)", "width": 1})
    # Goal boxes
    for sign in [-1, 1]:
        fig.add_shape(type="rect",
                      x0=sign * 0.70, y0=-0.14, x1=sign * 0.55, y1=0.14,
                      fillcolor="rgba(0,0,0,0)",
                      line={"color": "rgba(255,255,255,0.3)", "width": 1})

    # Zone stand polygons
    zone_angles = {
        "A": np.linspace(0.60 * np.pi, 1.40 * np.pi, 60),          # West
        "B": np.linspace(0.05 * np.pi, 0.95 * np.pi, 60),           # North
        "C": np.concatenate([                                         # East
            np.linspace(1.60 * np.pi, 2.0 * np.pi, 30),
            np.linspace(0.0, 0.40 * np.pi, 30),
        ]),
        "D": np.linspace(1.05 * np.pi, 1.95 * np.pi, 60),           # South
    }
    rx_out, ry_out = 1.50, 0.95
    rx_in,  ry_in  = 0.96, 0.61

    label_pos = {
        "A": (-1.25,  0.0),
        "B": ( 0.0,   0.80),
        "C": ( 1.25,  0.0),
        "D": ( 0.0,  -0.80),
    }
    zone_names = {
        "A": "West",
        "B": "North",
        "C": "East",
        "D": "South",
    }

    annotations = []
    for zone, angles in zone_angles.items():
        pct = zone_data.get(zone, 50)
        color, fill_mid, fill_light = zone_color(pct)
        label = zone_label(pct)
        name  = zone_names[zone]

        outer_x = rx_out * np.cos(angles)
        outer_y = ry_out * np.sin(angles)
        inner_x = rx_in  * np.cos(angles[::-1])
        inner_y = ry_in  * np.sin(angles[::-1])
        px = np.concatenate([outer_x, inner_x, [outer_x[0]]])
        py = np.concatenate([outer_y, inner_y, [outer_y[0]]])

        fig.add_trace(go.Scatter(
            x=px, y=py, fill="toself",
            fillcolor=fill_mid,
            line={"color": color, "width": 1.5},
            hoverinfo="text",
            hovertext=f"<b>{name} Stand (Zone {zone})</b><br>Density: {pct}%<br>Status: {label}",
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=px, y=py, fill="toself",
            fillcolor=fill_light,
            line={"color": "rgba(0,0,0,0)", "width": 0},
            hoverinfo="skip", showlegend=False,
        ))

        lx, ly = label_pos[zone]
        annotations.append(dict(
            x=lx, y=ly,
            text=(
                f"<b>{zone}</b><br>"
                f"<span style='font-size:13px;font-weight:700'>{pct}%</span><br>"
                f"<span style='font-size:10px'>{label}</span>"
            ),
            showarrow=False,
            font={"size": 12, "color": color},
            align="center",
            bgcolor="rgba(0,0,0,0.55)",
            borderpad=4,
        ))

    # Legend
    legend_items = [
        ("≥88%  High",     "#ff5b65"),
        ("72–87%  Medium", "#e8b84d"),
        ("<72%  Stable",   "#12b981"),
    ]
    for i, (lbl, col) in enumerate(legend_items):
        annotations.append(dict(
            x=1.65, y=0.55 - i * 0.30,
            text=f"<span style='color:{col}'>■</span>  {lbl}",
            showarrow=False,
            font={"size": 11, "color": C["text"]},
            xanchor="left", align="left",
        ))

    fig.update_layout(
        title={"text": title, "font": {"color": C["text"], "size": 13}},
        paper_bgcolor=C["card_bg"],
        plot_bgcolor=C["card_bg"],
        xaxis={"range": [-1.75, 2.55], "visible": False, "scaleanchor": "y"},
        yaxis={"range": [-1.15, 1.15], "visible": False},
        annotations=annotations,
        height=380,
        margin=dict(l=10, r=10, t=44, b=10),
        showlegend=False,
        hoverlabel={"bgcolor": "#1c2128", "font_color": "#e6edf3",
                    "bordercolor": "#30363d"},
    )
    return fig


# ── Action recommendation card ─────────────────────────────────────────────────
def action_card(
    title: str,
    kpi_value: str,
    gap_text: str,
    insight: str,
    actions: list[str],
    impact: str,
    priority: str = "red",       # "red" | "yellow" | "green"
    compact: bool = False,       # True = hide insight + impact (overview use)
    priority_num: int | None = None,  # e.g. 1 → shows "PRIORITY 1" badge
) -> None:
    border_color = {"red": "#ff5b65", "yellow": "#e8b84d", "green": "#12b981"}.get(priority, "#ff5b65")
    badge_bg     = {"red": "#3d1a1a",  "yellow": "#2d2510",  "green": "#0d2b1a"}.get(priority, "#3d1a1a")
    icon         = {"red": "🔴", "yellow": "🟡", "green": "🟢"}.get(priority, "🔴")
    actions_html = "".join(
        f"<li style='margin-bottom:5px;color:{C['text']}'>{_html.escape(a)}</li>"
        for a in actions
    )
    priority_badge = (
        f"<span style='font-size:10px;font-weight:700;letter-spacing:1px;"
        f"text-transform:uppercase;background:{border_color};color:#0d1117;"
        f"border-radius:4px;padding:2px 7px;margin-left:8px;'>#{priority_num}</span>"
        if priority_num else ""
    )
    insight_html = "" if compact else (
        f"<div style='font-size:12px;color:{C['subtext']};margin-bottom:10px;font-style:italic;'>"
        f"💡 {_html.escape(insight)}</div>"
    )
    impact_html = "" if compact else (
        f"<div style='background:{C['plot_bg']};border-radius:8px;padding:8px 12px;"
        f"font-size:12px;color:{C['accent2']};'>"
        f"📈 Impact: {_html.escape(impact)}</div>"
    )
    st.markdown(
        f"""
        <div style='background:{C["card_bg"]};border:1px solid {border_color};
                    border-radius:14px;padding:20px 22px;margin-bottom:16px;'>
          <div style='font-size:11px;font-weight:700;letter-spacing:1px;
                      text-transform:uppercase;color:{C["subtext"]};margin-bottom:6px;
                      display:flex;align-items:center;'>
            {icon} &nbsp;{_html.escape(title)}{priority_badge}
          </div>
          <div style='font-size:30px;font-weight:800;color:{C["accent1"]};
                      line-height:1.1;margin-bottom:8px;'>{_html.escape(kpi_value)}</div>
          <div style='background:{badge_bg};border-radius:8px;padding:8px 12px;margin-bottom:12px;'>
            <div style='font-size:13px;font-weight:600;color:{border_color};'>
              ❗ {_html.escape(gap_text)}
            </div>
          </div>
          {insight_html}
          <ul style='font-size:12px;padding-left:18px;margin:0 0 12px 0;'>{actions_html}</ul>
          {impact_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Risk / status alert banner ─────────────────────────────────────────────────
def risk_alert_banner(zone_data: dict, zone_names: dict | None = None) -> None:
    """
    zone_data  = {"A": 92, "B": 87, "C": 60, "D": 55}   (% density, 0–100)
    zone_names = {"A": "West Stand", ...}                  optional display names
    """
    names = zone_names or {"A": "West", "B": "North", "C": "East", "D": "South"}
    overcrowded = [z for z, p in zone_data.items() if p >= 88]
    medium      = [z for z, p in zone_data.items() if 72 <= p < 88]

    if not overcrowded and not medium:
        st.markdown(
            f"<div style='background:#0d2b1a;border-left:4px solid {C['accent2']};"
            f"border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
            f"<span style='font-weight:700;color:{C['accent2']};'>✅ All zones operating normally</span>"
            f"<span style='font-size:12px;color:{C['subtext']};margin-left:8px;'>"
            f"No crowd density alerts</span></div>",
            unsafe_allow_html=True,
        )
        return

    if overcrowded:
        zones_str = ", ".join(f"{names.get(z, z)} Stand" for z in overcrowded)
        st.markdown(
            f"<div style='background:#3d1a1a;border-left:4px solid #ff5b65;"
            f"border-radius:10px;padding:14px 18px;margin-bottom:8px;'>"
            f"<div style='font-weight:700;color:#ff5b65;font-size:14px;'>"
            f"🚨 HIGH DENSITY — {zones_str}</div>"
            f"<div style='font-size:12px;color:{C['subtext']};margin-top:4px;'>"
            f"Crowd density above 88%. Immediate action required.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if medium:
        zones_str = ", ".join(f"{names.get(z, z)} Stand" for z in medium)
        st.markdown(
            f"<div style='background:#2d2510;border-left:4px solid #e8b84d;"
            f"border-radius:10px;padding:14px 18px;margin-bottom:8px;'>"
            f"<div style='font-weight:700;color:#e8b84d;font-size:13px;'>"
            f"⚠️ Elevated Density — {zones_str}</div>"
            f"<div style='font-size:12px;color:{C['subtext']};margin-top:4px;'>"
            f"Monitor flow — prepare intervention if density rises.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


def ai_chat(get_response_fn, placeholder: str, input_key: str) -> None:
    """
    Reusable AI assistant chat box with multi-turn conversation history.
    get_response_fn: callable(question, history) → response str.
    placeholder: hint text shown on first message.
    input_key: unique Streamlit key prefix for this chat instance.
    """
    from src.services.ai_assistant import stream_response

    history_key = f"{input_key}_history"
    counter_key = f"{input_key}_counter"

    if history_key not in st.session_state:
        st.session_state[history_key] = []
    if counter_key not in st.session_state:
        st.session_state[counter_key] = 0

    history = st.session_state[history_key]

    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):

        # ── Header + clear button ─────────────────────────────────────────────
        h_col, c_col = st.columns([5, 1])
        with h_col:
            st.markdown(
                '<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
                '<span style="font-size:18px;">🤖</span>'
                '<span style="font-size:14px;font-weight:700;color:#f4f7fb;">AI Assistant</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        with c_col:
            if history:
                if st.button("Clear", key=f"{input_key}_clear", use_container_width=True):
                    st.session_state[history_key] = []
                    st.rerun()

        # ── Conversation history ──────────────────────────────────────────────
        for msg in history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div style="background:#1a2535;border-radius:8px;padding:10px 14px;margin-bottom:6px;">'
                    f'<div style="font-size:11px;font-weight:700;color:#9aa8ba;'
                    f'text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">You</div>'
                    f'<div style="font-size:13px;color:#f4f7fb;">{_html.escape(msg["content"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                formatted = msg["content"].replace("\n\n", "<br><br>").replace("\n", "<br>")
                st.markdown(
                    f'<div style="background:#0d1017;border-left:3px solid #16d9e8;'
                    f'border-radius:8px;padding:10px 14px;margin-bottom:6px;">'
                    f'<div style="font-size:11px;font-weight:700;color:#16d9e8;'
                    f'text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">AI</div>'
                    f'<div style="font-size:13px;color:#f4f7fb;line-height:1.6;">{formatted}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # ── Input — counter in key clears field after each submission ─────────
        current_placeholder = placeholder if not history else "Ask a follow-up..."
        question = st.text_input(
            "Ask a question",
            placeholder=current_placeholder,
            label_visibility="collapsed",
            key=f"{input_key}_{st.session_state[counter_key]}",
        )

        if question:
            # Capture history before appending this turn
            prior_history = list(history)
            st.session_state[history_key].append({"role": "user", "content": question})

            # Get response — passes full prior history for Gemini multi-turn context
            response = get_response_fn(question, prior_history)

            # Stream the response live before rerun
            st.markdown(
                '<div style="margin-top:8px;padding:14px 16px;background:#0d1017;'
                'border-left:3px solid #16d9e8;border-radius:8px;">'
                '<div style="font-size:11px;font-weight:700;color:#16d9e8;'
                'text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">AI</div>',
                unsafe_allow_html=True,
            )
            st.write_stream(stream_response(response))
            st.markdown('</div>', unsafe_allow_html=True)

            # Store response, clear input on next render
            st.session_state[history_key].append({"role": "assistant", "content": response})
            st.session_state[counter_key] += 1
            st.rerun()
