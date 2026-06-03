import streamlit as st

from src.pages.energy_carbon import render_energy_carbon
from src.pages.environmental_health import render_environmental_health
from src.pages.executive_scorecard import render_executive_scorecard
from src.pages.waste_intelligence import render_waste_intelligence
from src.pages.water_usage import render_water_usage
from src.services.status import get_all_statuses, status_emoji
from src.utils.page_config import configure_page

configure_page()

statuses = get_all_statuses()

st.sidebar.title("ArenaPulse")
st.sidebar.caption("Stadium sustainability intelligence")

waste_label  = f"{status_emoji(statuses['waste'].status)} Waste"
energy_label = f"{status_emoji(statuses['energy'].status)} Energy"
water_label  = f"{status_emoji(statuses['water'].status)} Water"
env_label    = f"{status_emoji(statuses['environment'].status)} Environmental Health"

view = st.sidebar.radio(
    "Navigation",
    ["Overview", energy_label, waste_label, water_label, env_label],
)

st.sidebar.markdown("---")

_sport_options = {"⚽  Soccer / FIFA": "soccer", "🏈  NFL / American Football": "nfl"}
_sport_label = st.sidebar.radio("Sport", list(_sport_options.keys()), key="sport_radio")
st.session_state["sport"] = _sport_options[_sport_label]

st.sidebar.markdown("---")
st.sidebar.caption(
    "Demo mode — sample data only. "
    "No live POS, payment, or customer data is stored."
)

if view == "Overview":
    render_executive_scorecard()
elif view == energy_label:
    render_energy_carbon()
elif view == waste_label:
    render_waste_intelligence()
elif view == water_label:
    render_water_usage()
else:
    render_environmental_health()
