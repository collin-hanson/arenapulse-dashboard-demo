from dataclasses import dataclass
import html

import streamlit as st


@dataclass(frozen=True)
class PriorityCard:
    title: str
    status: str
    message: str
    rationale: str
    action_label: str | None = None


def render_priority_card(card: PriorityCard) -> None:
    status = card.status.lower()
    st.markdown(
        f"""
        <div class="ap-alert {status}">
            <span class="ap-status {status}">{html.escape(card.status.upper())}</span>
            <h3>{html.escape(card.title)}</h3>
            <p>{html.escape(card.message)}</p>
            <p class="ap-small">{html.escape(card.rationale)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if card.action_label:
        st.button(card.action_label, key=f"action_{card.title}", width="stretch")
