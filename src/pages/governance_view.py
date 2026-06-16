import streamlit as st

from src.components.list_panel import render_action_note, render_status_list
from src.governance.data_quality import get_demo_data_quality_statuses
from src.services.pos_ingestion import get_demo_payload, sanitize_pos_payload


def render_governance_view() -> None:
    st.markdown('<div class="ap-kicker">Governance and security</div>', unsafe_allow_html=True)
    st.title("Only approved operational fields reach the dashboard")
    st.caption("Prototype demonstration of the POS allow-list sanitization policy.")

    statuses = get_demo_data_quality_statuses()
    status_rows = [{"feed": s.feed_name, "status": s.status, "message": s.message} for s in statuses]
    st.markdown(
        '<div class="ap-section-header">📡 Data feed status</div>',
        unsafe_allow_html=True,
    )
    render_status_list(status_rows, "feed", "message", "status")

    payload = get_demo_payload()
    sanitized = sanitize_pos_payload(payload)

    st.markdown(
        f"""
        <div class="ap-strip">
            <div class="ap-strip-item">
                <strong>Allowed fields</strong>
                <span>{len(sanitized.accepted)} retained for operations.</span>
            </div>
            <div class="ap-strip-item">
                <strong>Dropped fields</strong>
                <span>{len(sanitized.dropped_fields)} rejected before storage.</span>
            </div>
            <div class="ap-strip-item">
                <strong>Sensitive fields</strong>
                <span>{len(sanitized.sensitive_drops)} blocked in this sample.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="ap-section-header">✅ Accepted operational fields</div>', unsafe_allow_html=True)
        accepted_rows = [
            {"field": key, "value": value, "status": "Active"} for key, value in sanitized.accepted.items()
        ]
        render_status_list(accepted_rows, "field", "value", "status")
    with right:
        st.markdown('<div class="ap-section-header">🚫 Rejected before storage</div>', unsafe_allow_html=True)
        dropped_rows = [
            {"field": key, "value": "Removed from payload", "status": "Blocked"}
            for key in sanitized.dropped_fields
        ]
        render_status_list(dropped_rows, "field", "value", "status")

    if sanitized.sensitive_drops:
        st.error("Sensitive fields rejected before storage: " + ", ".join(sanitized.sensitive_drops))

    with st.expander("Inspect raw demo payload"):
        st.json(payload)

    render_action_note(
        "Production path: venue POS webhook -> API gateway -> sanitization function -> "
        "sanitized database -> ArenaPulse dashboard. Raw payment and customer fields should not be stored."
    )
