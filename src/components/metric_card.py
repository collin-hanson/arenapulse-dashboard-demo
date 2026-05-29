import html

import streamlit as st


def render_metric_card(title: str, value: str, label: str) -> None:
    st.markdown(
        f"""
        <div class="ap-card">
            <h3>{html.escape(title)}</h3>
            <div class="metric">{html.escape(value)}</div>
            <div class="label">{html.escape(label)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
