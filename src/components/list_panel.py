import html

import streamlit as st


def render_status_list(rows: list[dict[str, object]], title_key: str, detail_key: str, status_key: str) -> None:
    html_rows = []
    for row in rows:
        title = html.escape(str(row[title_key]))
        detail = html.escape(str(row[detail_key]))
        status = html.escape(str(row[status_key]))
        status_class = status.lower().replace(" ", "-")
        html_rows.append(
            f'<div class="ap-row"><div><strong>{title}</strong>'
            f'<small>{detail}</small></div><span class="ap-pill {status_class}">{status}</span></div>'
        )
    st.markdown(f'<div class="ap-panel">{"".join(html_rows)}</div>', unsafe_allow_html=True)


def render_action_note(text: str) -> None:
    st.markdown(f'<div class="ap-action">{html.escape(text)}</div>', unsafe_allow_html=True)
