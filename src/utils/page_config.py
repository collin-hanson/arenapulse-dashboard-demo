import streamlit as st


def configure_page() -> None:
    st.set_page_config(
        page_title="ArenaPulse",
        page_icon="🏟",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        :root {
            --ap-bg: #0b1017;
            --ap-surface: #151c25;
            --ap-surface-2: #1c2530;
            --ap-line: #2b3645;
            --ap-text: #f4f7fb;
            --ap-muted: #9aa8ba;
            --ap-cyan: #16d9e8;
            --ap-teal: #12b981;
            --ap-red: #ff5b65;
            --ap-yellow: #e8b84d;
            --ap-purple: #8b5cf6;
        }

        /* ── Base ── */
        .stApp { background: var(--ap-bg); color: var(--ap-text); }
        [data-testid="stSidebar"] {
            background: #0e1420;
            border-right: 1px solid var(--ap-line);
        }
        [data-testid="stSidebar"] * { color: var(--ap-text); }
        .main .block-container { padding-top: 1.2rem; max-width: 1380px; }
        h1, h2, h3 { letter-spacing: 0; color: var(--ap-text); }
        p, span, li { color: var(--ap-text); }

        /* ── Kicker label ── */
        .ap-kicker {
            color: var(--ap-cyan);
            font-size: .72rem;
            font-weight: 850;
            letter-spacing: .10em;
            text-transform: uppercase;
            margin-bottom: .2rem;
        }

        /* ── Phase banner ── */
        .ap-phase-banner {
            display: flex;
            align-items: center;
            gap: 1rem;
            background: linear-gradient(90deg, rgba(22,217,232,.10) 0%, rgba(139,92,246,.06) 100%);
            border: 1px solid var(--ap-line);
            border-left: 4px solid var(--ap-cyan);
            border-radius: 8px;
            padding: .7rem 1.1rem;
            margin-bottom: 1rem;
        }
        .ap-phase-banner .phase-tag {
            color: var(--ap-cyan);
            font-size: .7rem;
            font-weight: 850;
            letter-spacing: .10em;
            text-transform: uppercase;
            background: rgba(22,217,232,.12);
            border: 1px solid rgba(22,217,232,.25);
            border-radius: 4px;
            padding: .18rem .55rem;
            white-space: nowrap;
        }
        .ap-phase-banner .phase-countdown {
            font-weight: 800;
            font-size: .95rem;
            color: var(--ap-text);
        }
        .ap-phase-banner .phase-countdown strong { color: var(--ap-yellow); }
        .ap-phase-banner .phase-meta {
            color: var(--ap-muted);
            font-size: .84rem;
            margin-left: auto;
        }

        /* ── Bold KPI cards ── */
        .ap-kpi {
            background: var(--ap-surface);
            border: 1px solid var(--ap-line);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            height: 100%;
        }
        .kpi-label {
            color: var(--ap-muted);
            font-size: .68rem;
            font-weight: 850;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin-bottom: .35rem;
        }
        .kpi-value {
            color: var(--ap-text);
            font-size: 2.15rem;
            font-weight: 850;
            line-height: 1;
            margin-bottom: .28rem;
        }
        .kpi-delta { font-size: .78rem; font-weight: 700; }
        .kpi-delta.neg { color: var(--ap-red); }
        .kpi-delta.pos { color: var(--ap-teal); }
        .kpi-delta.neu { color: var(--ap-muted); }

        /* ── Priority cards ── */
        .ap-priority-card {
            background: var(--ap-surface);
            border: 1px solid var(--ap-line);
            border-top: 3px solid var(--ap-line);
            border-radius: 8px;
            padding: 1rem 1.05rem;
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        .ap-priority-card.high   { border-top-color: var(--ap-red); }
        .ap-priority-card.medium { border-top-color: var(--ap-yellow); }
        .ap-priority-card.monitor{ border-top-color: var(--ap-yellow); }
        .ap-priority-card.stable { border-top-color: var(--ap-teal); }
        .pc-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: .55rem;
        }
        .pc-system {
            color: var(--ap-muted);
            font-size: .68rem;
            font-weight: 850;
            letter-spacing: .09em;
            text-transform: uppercase;
        }
        .pc-headline {
            color: var(--ap-text);
            font-size: .95rem;
            font-weight: 800;
            line-height: 1.35;
            margin-bottom: .55rem;
        }
        .pc-actions {
            color: var(--ap-muted);
            font-size: .82rem;
            margin: 0 0 .6rem 0;
            padding-left: 1.05rem;
            flex: 1;
        }
        .pc-actions li { margin-bottom: .22rem; }
        .pc-impact {
            color: var(--ap-cyan);
            font-size: .76rem;
            font-weight: 700;
            border-top: 1px solid var(--ap-line);
            padding-top: .45rem;
        }

        /* ── Diversion gap bar ── */
        .ap-gap-hero {
            display: flex;
            align-items: center;
            gap: 1.25rem;
            background: var(--ap-surface);
            border: 1px solid var(--ap-line);
            border-radius: 8px;
            padding: 1.05rem 1.3rem;
            margin-bottom: 1rem;
        }
        .gap-anchor { text-align: center; min-width: 76px; }
        .gap-anchor .gap-pct {
            display: block;
            font-size: 1.85rem;
            font-weight: 850;
            line-height: 1;
            color: var(--ap-cyan);
        }
        .gap-anchor small { color: var(--ap-muted); font-size: .7rem; }
        .gap-center { flex: 1; }
        .gap-bar {
            height: 10px;
            border-radius: 5px;
            overflow: hidden;
            display: flex;
            margin-bottom: .5rem;
            background: rgba(255,255,255,.04);
        }
        .gap-fill-current   { background: #12b981; }
        .gap-fill-available { background: rgba(232,184,77,.72); }
        .gap-fill-escape    { background: rgba(255,91,101,.35); }
        .gap-label { text-align: center; font-weight: 800; font-size: .92rem; color: var(--ap-text); }
        .gap-sub   { text-align: center; color: var(--ap-muted); font-size: .74rem; margin-top: .15rem; }

        /* ── Status list panel ── */
        .ap-panel {
            background: var(--ap-surface);
            border: 1px solid var(--ap-line);
            border-radius: 8px;
            padding: .85rem 1rem;
        }
        .ap-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: .75rem;
            padding: .65rem 0;
            border-bottom: 1px solid var(--ap-line);
        }
        .ap-row:last-child { border-bottom: 0; }
        .ap-row strong { color: var(--ap-text); display: block; margin-bottom: .1rem; }
        .ap-row small  { color: var(--ap-muted); font-size: .82rem; }

        /* ── Status pills ── */
        .ap-pill {
            display: inline-block;
            border-radius: 999px;
            padding: .2rem .58rem;
            font-size: .7rem;
            font-weight: 850;
            white-space: nowrap;
        }
        .ap-pill.high, .ap-pill.blocked {
            color: #ffd7da; background: rgba(255,91,101,.18);
        }
        .ap-pill.medium, .ap-pill.monitor, .ap-pill.delayed {
            color: #ffe3a3; background: rgba(232,184,77,.18);
        }
        .ap-pill.stable, .ap-pill.low, .ap-pill.active {
            color: #b7f7d8; background: rgba(18,185,129,.18);
        }

        /* ── Action note ── */
        .ap-action {
            border-left: 4px solid var(--ap-cyan);
            background: rgba(22,217,232,.07);
            border-radius: 8px;
            padding: .8rem 1rem;
            color: var(--ap-text);
            font-weight: 700;
            font-size: .88rem;
            margin-top: .65rem;
        }

        /* ── Monitor banners ── */
        .ap-monitor-banner {
            display: flex;
            align-items: center;
            gap: .75rem;
            background: rgba(18,185,129,.08);
            border: 1px solid rgba(18,185,129,.22);
            border-radius: 8px;
            padding: .65rem 1rem;
            margin-bottom: 1rem;
            color: #b7f7d8;
            font-size: .88rem;
            font-weight: 700;
        }
        .ap-monitor-banner.yellow {
            background: rgba(232,184,77,.08);
            border-color: rgba(232,184,77,.25);
            color: #ffe3a3;
        }
        .ap-monitor-banner.red {
            background: rgba(255,91,101,.08);
            border-color: rgba(255,91,101,.25);
            color: #ffd7da;
        }

        /* ── Environmental health cards ── */
        .ap-env-card {
            background: var(--ap-surface);
            border: 1px solid var(--ap-line);
            border-top: 3px solid var(--ap-line);
            border-radius: 8px;
            padding: 1rem;
        }
        .ap-env-card.high    { border-top-color: var(--ap-red); }
        .ap-env-card.monitor { border-top-color: var(--ap-yellow); }
        .ap-env-card.stable  { border-top-color: var(--ap-teal); }
        .env-factor {
            color: var(--ap-muted);
            font-size: .68rem;
            font-weight: 850;
            letter-spacing: .09em;
            text-transform: uppercase;
            margin-bottom: .4rem;
        }
        .env-headline {
            color: var(--ap-text);
            font-weight: 800;
            font-size: .9rem;
            margin-bottom: .45rem;
            line-height: 1.4;
        }
        .env-detail { color: var(--ap-muted); font-size: .82rem; margin-bottom: .5rem; line-height: 1.5; }
        .env-watch  { color: var(--ap-yellow); font-size: .78rem; font-weight: 700; }
        .env-notify {
            color: var(--ap-muted);
            font-size: .74rem;
            border-top: 1px solid var(--ap-line);
            padding-top: .4rem;
            margin-top: .5rem;
        }
        .env-notify strong { color: var(--ap-red); }

        /* ── Conditions strip ── */
        .ap-conditions {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: .65rem;
            margin-bottom: 1rem;
        }
        .ap-cond-tile {
            background: var(--ap-surface);
            border: 1px solid var(--ap-line);
            border-radius: 8px;
            padding: .8rem .9rem;
            text-align: center;
        }
        .ap-cond-tile .cond-label {
            color: var(--ap-muted);
            font-size: .65rem;
            font-weight: 850;
            letter-spacing: .07em;
            text-transform: uppercase;
            margin-bottom: .3rem;
        }
        .ap-cond-tile .cond-value {
            color: var(--ap-text);
            font-size: 1.45rem;
            font-weight: 850;
            line-height: 1;
        }
        .ap-cond-tile .cond-note { color: var(--ap-muted); font-size: .7rem; margin-top: .2rem; }

        /* ── Command block (Overview primary action) ── */
        .ap-command {
            background: linear-gradient(135deg, rgba(255,91,101,.14) 0%, rgba(22,217,232,.07) 100%);
            border: 1px solid var(--ap-line);
            border-left: 5px solid var(--ap-red);
            border-radius: 8px;
            padding: 1.1rem 1.2rem;
        }
        .ap-command .eyebrow {
            color: #ffd7da;
            font-size: .7rem;
            font-weight: 850;
            letter-spacing: .06em;
            text-transform: uppercase;
        }
        .ap-command h2 { margin: .3rem 0 .4rem 0; font-size: 1.75rem; line-height: 1.15; }
        .ap-command p  { margin: .45rem 0; color: var(--ap-muted); font-size: .9rem; }
        .ap-command p strong { color: var(--ap-text); }

        /* ── Priority insight cards (his layout) ── */
        .priority-red, .priority-yellow, .priority-green {
            border-radius: 12px;
            padding: 16px 18px;
            margin-bottom: 8px;
            font-size: .84rem;
            line-height: 1.55;
        }
        .priority-red    { background: #3d1a1a; border-left: 4px solid var(--ap-red); }
        .priority-yellow { background: #2d2510; border-left: 4px solid var(--ap-yellow); }
        .priority-green  { background: #0d2b1a; border-left: 4px solid var(--ap-teal); }
        .priority-title  {
            font-size: .78rem;
            font-weight: 850;
            letter-spacing: .04em;
            text-transform: uppercase;
            margin-bottom: .45rem;
        }
        .priority-red    .priority-title { color: var(--ap-red); }
        .priority-yellow .priority-title { color: var(--ap-yellow); }
        .priority-green  .priority-title { color: var(--ap-teal); }
        .priority-insight { color: var(--ap-text); margin-bottom: .35rem; }
        .priority-action  { color: var(--ap-muted); font-size: .8rem; }

        /* ── Section header (his layout) ── */
        .ap-section-header {
            font-size: 14px;
            font-weight: 700;
            color: var(--ap-text);
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: .06em;
        }
        .ap-section-sub { font-size: 12px; color: var(--ap-muted); margin-bottom: 12px; }

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab-list"] {
            gap: .3rem;
            border-bottom: 1px solid var(--ap-line);
        }
        .stTabs [data-baseweb="tab"] { color: var(--ap-muted); }

        /* ── Native metric override ── */
        div[data-testid="stMetric"] {
            background: var(--ap-surface);
            border: 1px solid var(--ap-line);
            border-radius: 8px;
            padding: 1rem;
        }

        @media (max-width: 900px) {
            .ap-conditions { grid-template-columns: repeat(3, 1fr); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def plotly_layout(fig, height: int = 330):
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=12, t=32, b=20),
        plot_bgcolor="#101722",
        paper_bgcolor="#101722",
        font=dict(color="#d7dee9"),
        legend=dict(font=dict(color="#d7dee9")),
        xaxis=dict(gridcolor="#2b3645", zerolinecolor="#2b3645"),
        yaxis=dict(gridcolor="#2b3645", zerolinecolor="#2b3645"),
    )
    return fig
