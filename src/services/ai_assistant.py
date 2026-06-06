"""
AI assistant for ArenaPulse.

Uses Google Gemini Flash when GEMINI_API_KEY is set in Streamlit secrets.
Falls back to keyword-matched simulated responses when no key is present —
so the demo works without a key and upgrades automatically when one is added.
"""

from __future__ import annotations

import time

import streamlit as st


# ── Gemini integration ─────────────────────────────────────────────────────────

def _base_context() -> str:
    """Build a live event context string to anchor Gemini responses."""
    try:
        from src.services.demo_data import get_event_context
        ctx = get_event_context()
        return (
            "You are an AI assistant embedded in ArenaPulse, a stadium sustainability "
            "operations dashboard. You help venue operations managers make real-time decisions "
            "during live events.\n\n"
            f"Current event: {ctx.event_name} at {ctx.venue}\n"
            f"Attendance: {ctx.attendance:,} fans ({ctx.occupancy_rate:.0%} occupancy)\n"
            f"Game phase: {ctx.event_phase} — {ctx.next_phase} in "
            f"{ctx.minutes_to_next_phase} minutes\n"
            f"LEED status: {ctx.leed_status}\n\n"
            "Respond in 2–4 sentences. Be concise, practical, and actionable. "
            "Focus on what the operations manager can do right now. "
            "Do not mention data you don't have. "
            "Use plain language — no jargon. "
            "Only use a numbered list if there are 3 or more distinct steps."
        )
    except Exception:
        return (
            "You are an AI assistant for ArenaPulse, a stadium sustainability operations "
            "dashboard. Help operations managers make practical, real-time decisions. "
            "Be concise (2–4 sentences) and actionable."
        )


def _ask_gemini(
    page_context: str,
    question: str,
    history: list[dict] | None = None,
) -> str | None:
    """
    Send a question to Gemini with event context, page context, and conversation history.
    history: list of {"role": "user"|"assistant", "content": "..."} dicts.
    Returns the response text, or None if the call fails or no key is configured.
    """
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            return None
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        system_instruction = f"{_base_context()}\n\nPage context: {page_context}"
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=system_instruction,
        )

        # Convert history to Gemini's {"role", "parts"} format
        gemini_history = []
        for msg in (history or []):
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(question)
        return response.text.strip()
    except Exception:
        return None


# ── Streaming ──────────────────────────────────────────────────────────────────

def stream_response(text: str, delay: float = 0.018):
    """Yield one character at a time for st.write_stream() typewriter effect."""
    for char in text:
        yield char
        time.sleep(delay)


# ── Simulated fallback responses ───────────────────────────────────────────────

def _match(question: str, responses: list[tuple[list[str], str]], fallback: str) -> str:
    q = question.lower()
    best_score = 0
    best_response = fallback
    for keywords, response in responses:
        score = sum(1 for kw in keywords if kw in q)
        if score > best_score:
            best_score = score
            best_response = response
    return best_response


WASTE_RESPONSES: list[tuple[list[str], str]] = [
    (
        ["diversion", "low", "why", "rate", "below"],
        (
            "Diversion is low tonight primarily because of the food-heavy sales mix in Lower "
            "Concourse East. Hot dogs, nachos, and food packaging generate high landfill waste "
            "that can't be composted without proper bin infrastructure in place.\n\n"
            "The max possible diversion ceiling is 54% — meaning even with perfect sorting, "
            "you can't exceed that given what's been sold. The gap between where you are now "
            "and that ceiling is where the opportunity lives. Bin placement and ambassador "
            "coverage in Lower Concourse East is the highest-leverage action right now."
        ),
    ),
    (
        ["prioritize", "priority", "zone", "section", "focus", "where", "first"],
        (
            "Lower Concourse East should be your first priority tonight.\n\n"
            "It has the highest waste volume at 920 lb, a food-heavy packaging mix, and is "
            "rated High risk. Compostable packaging is the dominant stream there — which means "
            "bin labelling and ambassador presence directly lifts diversion.\n\n"
            "Gate Plaza is second priority: bins are near capacity before halftime and the "
            "surge will push them over. Move overflow bins there now."
        ),
    ),
    (
        ["halftime", "before", "surge", "next", "minutes"],
        (
            "Two things to do before halftime:\n\n"
            "1. Move overflow bins to Gate Plaza — the halftime surge will push existing bins "
            "over capacity. Pre-position at least 2 extra compost bins now.\n\n"
            "2. Redirect your green team ambassador to Lower Concourse East and place compost "
            "signage at the hot food vendor stands. The food surge at halftime is your best "
            "window to lift diversion — fans are stationary and more receptive to sorting cues.\n\n"
            "Confirm bin coverage in both zones before the 45-minute mark."
        ),
    ),
    (
        ["landfill", "unavoidable", "estimate", "lb", "pounds"],
        (
            "The 3,354 lb landfill estimate comes from packaging sold tonight that has no "
            "recoverable path — primarily plastic film wrappers, composite packaging, and "
            "non-recyclable food containers.\n\n"
            "This number is based on POS units sold multiplied by estimated packaging weight. "
            "It's verified by the hauler post-event, so treat it as a projection for now.\n\n"
            "The only way to reduce this figure long-term is through procurement — switching "
            "to compostable or recyclable packaging at the vendor level. That's a post-event "
            "conversation, not a game-night action."
        ),
    ),
    (
        ["bin", "placement", "move", "recycling", "compost", "which"],
        (
            "Based on tonight's POS packaging mix:\n\n"
            "• Gate Plaza — prioritize recycling bins. Beer cans, water bottles, and soda "
            "make up the majority of waste there.\n\n"
            "• Upper Concourse West — add compost bins. Food packaging is heavy there and "
            "the compostable stream is underserved.\n\n"
            "• Lower Concourse East and Premium Level — current bin mix is sufficient, "
            "but ambassador presence will help with sorting compliance."
        ),
    ),
    (
        ["ambassador", "green team", "staff", "team"],
        (
            "Your green team ambassador should be redirected to Lower Concourse East "
            "immediately. That's the highest-volume waste zone with the most diversion "
            "opportunity tonight.\n\n"
            "Key tasks: place compost signage at the hot food vendor stands, assist fans "
            "with sorting at the bin stations, and confirm bin coverage before the halftime "
            "surge. After halftime, Gate Plaza becomes the priority as density peaks there."
        ),
    ),
]

WASTE_FALLBACK = (
    "I can help with diversion rates, bin placement, zone priorities, or what to do before "
    "halftime. What do you need?"
)


ENERGY_RESPONSES: list[tuple[list[str], str]] = [
    (
        ["lighting", "high", "why", "load"],
        (
            "Lighting is at 73% of tracked load tonight, which is elevated but not yet "
            "critical. The issue isn't the load percentage itself — it's whether occupancy "
            "has diverged from lighting coverage.\n\n"
            "Right now occupancy hasn't dropped enough to trigger adaptive dimming. Watch "
            "section by section — specifically the lower bowl — and act the moment a zone "
            "empties out. Pre-identify which zones can be dimmed so the response is immediate."
        ),
    ),
    (
        ["halftime", "watch", "occupancy", "diverge", "drop"],
        (
            "At halftime, fans move to concourses and restrooms — lower bowl sections will "
            "empty temporarily. That's the trigger point for adaptive lighting.\n\n"
            "Before halftime: identify which lower bowl sections are likely to empty, confirm "
            "dimming zones are pre-configured, and monitor occupancy in real time as halftime "
            "starts. If any section drops below 75% occupancy while lighting stays at full "
            "load, apply adaptive dimming within the first 5 minutes to capture the full saving."
        ),
    ),
    (
        ["hvac", "cooling", "air"],
        (
            "HVAC is at 18% of tracked load tonight and is currently Stable. Zone-based "
            "cooling is running as expected.\n\n"
            "If occupancy drops in any section at halftime, check whether HVAC is still "
            "conditioning those zones — unoccupied sections running at full cooling is "
            "a secondary energy action after lighting. Smaller lever, but worth checking "
            "if lighting divergence is already being addressed."
        ),
    ),
    (
        ["average", "avg", "above", "below", "compare", "history"],
        (
            "Tonight is running approximately 2,931 kWh above the 10-event average. "
            "That's within normal range for a high-attendance night — 91% occupancy "
            "drives higher baseline load across lighting, HVAC, and AV.\n\n"
            "The more useful comparison is energy per fan: at 1.8 kWh per attendee, "
            "you're slightly above the 1.5 kWh benchmark. Adaptive lighting at halftime "
            "is the most direct path to closing that gap tonight."
        ),
    ),
    (
        ["action", "do", "reduce", "save", "what"],
        (
            "The one actionable lever tonight is lighting divergence.\n\n"
            "If any section drops below 75% occupancy — especially in the lower bowl at "
            "halftime — apply adaptive dimming immediately. Lighting is 73% of tracked "
            "load, so it's the highest-impact system to act on.\n\n"
            "HVAC is secondary: if you dim a zone, check whether cooling can be reduced "
            "in the same zone. AV and displays are fixed — no manual change warranted."
        ),
    ),
]

ENERGY_FALLBACK = (
    "I can help with energy load, lighting vs occupancy, HVAC, or what to watch at halftime. "
    "What do you need?"
)


WATER_RESPONSES: list[tuple[list[str], str]] = [
    (
        ["high", "why", "above", "average", "usage", "elevated"],
        (
            "Tonight's water usage is running above the 10-event average. At 91% occupancy, "
            "that's expected — restroom demand scales directly with attendance.\n\n"
            "The 24.5 L per fan figure is above the 20 L sustainability guide, but that guide "
            "is a planning benchmark, not a game-night target. You can't meaningfully reduce "
            "it mid-event. The number is useful for post-event reporting and long-term "
            "fixture planning."
        ),
    ),
    (
        ["restroom", "halftime", "surge", "blockage", "fault"],
        (
            "Restrooms account for approximately 67% of total water usage and peak sharply "
            "at halftime.\n\n"
            "The one operational action available: walk the restroom banks at Lower Concourse "
            "East before halftime. If a fixture is blocked or faulted, catching it now "
            "prevents a fan-facing incident at peak demand. A blocked fixture during the surge "
            "is the only water scenario that creates a real operational problem tonight."
        ),
    ),
    (
        ["system", "concession", "hvac", "irrigation", "breakdown"],
        (
            "Tonight's estimated water split by system:\n\n"
            "• Restrooms — 67%. Dominant consumer, peaks at halftime.\n"
            "• Concessions & food prep — 19%. Steady throughout the event.\n"
            "• HVAC & cooling — 9%. Higher on warm nights like tonight.\n"
            "• Field irrigation — 5%. Confirmed off during event window.\n\n"
            "Restrooms are the only system with real-time operational relevance. "
            "The rest are background and stable."
        ),
    ),
    (
        ["leak", "detection", "anomaly", "spike"],
        (
            "Active leak detection is in monitor mode tonight — no anomalies flagged "
            "from the submeters.\n\n"
            "If a submeter spike is reported during the event, escalate immediately. "
            "Field irrigation is confirmed off, so any spike in that submeter warrants "
            "an immediate check. Don't wait for the post-event report."
        ),
    ),
]

WATER_FALLBACK = (
    "I can help with water usage, restroom demand, system breakdown, or leak detection. "
    "What do you need?"
)


ENV_RESPONSES: list[tuple[list[str], str]] = [
    (
        ["heat", "stress", "why", "elevated", "hot", "temperature"],
        (
            "Heat stress is flagged as Monitor tonight because of the combination of three "
            "factors — not temperature alone.\n\n"
            "78°F outdoor temperature compounds with 65% humidity and 84% average crowd "
            "density. At this humidity level, the body's ability to cool through sweat is "
            "reduced. High density slows heat dissipation further — body heat builds in "
            "enclosed concourse sections faster than HVAC can compensate."
        ),
    ),
    (
        ["humidity", "combination", "dangerous", "exhaustion"],
        (
            "Humidity and heat together are more dangerous than either factor alone. "
            "Above 75°F with humidity over 65%, heat exhaustion onset accelerates.\n\n"
            "Tonight is right at the threshold: 78°F and 65% humidity. Fans in enclosed "
            "sections are at elevated risk, particularly during the halftime crowd surge "
            "when density peaks. Watch for distress in Lower Concourse East and keep "
            "water stations stocked."
        ),
    ),
    (
        ["aqi", "air", "quality", "ventilation"],
        (
            "AQI is 52 tonight — moderate but acceptable. No action required for the "
            "general population at this level.\n\n"
            "Ventilation is running at capacity in indoor concourses. Watch for any HVAC "
            "fault alerts or unusual odor reports — those are the triggers for escalation. "
            "If outdoor AQI climbs above 100, PA guidance to move fans indoors is warranted."
        ),
    ),
    (
        ["egress", "exit", "crowd", "gate", "plaza", "safety"],
        (
            "Egress is currently Stable across all exits. Gate Plaza at 92% density is the "
            "highest-risk exit zone — current flow is managed, but halftime will test it.\n\n"
            "Watch Gate Plaza density at halftime, monitor for exit obstructions, and keep "
            "emergency egress paths clear. If Gate Plaza density exceeds 95%, clear exit "
            "paths take priority over all other actions."
        ),
    ),
    (
        ["water", "station", "hydration", "restock"],
        (
            "Given 78°F and 65% humidity, hydration demand will spike at halftime. Water "
            "stations at Gate Plaza and Lower Concourse East are the highest-demand locations "
            "based on current crowd density.\n\n"
            "Restock both stations before halftime if they haven't been checked recently. "
            "Empty water stations during peak heat and density is the most likely fan-facing "
            "incident from tonight's environmental conditions."
        ),
    ),
]

ENV_FALLBACK = (
    "I can help with heat stress risk, AQI, crowd density, hydration demand, or egress. "
    "What do you need?"
)


OVERVIEW_RESPONSES: list[tuple[list[str], str]] = [
    (
        ["priority", "first", "most important", "urgent", "act", "now"],
        (
            "The highest priority right now is waste response in Lower Concourse East.\n\n"
            "It has the highest waste volume, a food-heavy packaging mix, and the most "
            "diversion opportunity before halftime. Redirect your green team ambassador "
            "there now and place compost signage at the hot food vendor stands.\n\n"
            "Second priority: move overflow bins to Gate Plaza before the halftime surge."
        ),
    ),
    (
        ["halftime", "before", "prepare", "surge", "next"],
        (
            "Before halftime, three things need to happen:\n\n"
            "1. Waste — Move overflow bins to Gate Plaza and redirect the green team "
            "ambassador to Lower Concourse East.\n"
            "2. Water — Walk the restroom banks at Lower Concourse East to catch any "
            "fixture fault before the surge.\n"
            "3. Energy — Pre-identify lower bowl sections that may empty at halftime. "
            "Apply adaptive dimming if occupancy drops while lighting stays high."
        ),
    ),
    (
        ["waste", "diversion"],
        (
            "Waste is the highest-alert system tonight. Diversion is 26 points below the "
            "maximum possible ceiling of 54%.\n\n"
            "The gap is closeable through bin placement and ambassador coverage in Lower "
            "Concourse East. Gate Plaza bins are also near capacity ahead of halftime. "
            "Go to the Waste page for the full zone breakdown."
        ),
    ),
    (
        ["energy", "lighting", "power"],
        (
            "Energy is at Medium status. Lighting is at 73% of tracked load — elevated "
            "but not yet critical. The trigger for action is occupancy divergence at "
            "halftime. Pre-identify lower bowl sections most likely to empty and have "
            "adaptive dimming ready to apply. Go to the Energy page for the full breakdown."
        ),
    ),
    (
        ["water", "restroom"],
        (
            "Water is at Medium monitoring status. Usage is above the 20 L per fan guide, "
            "which is expected at 91% occupancy.\n\n"
            "The one game-night action: walk the restroom banks at Lower Concourse East "
            "before halftime. A blocked fixture during the surge is the only water scenario "
            "that creates a real operational problem. Go to the Water page for the breakdown."
        ),
    ),
    (
        ["environment", "heat", "temperature", "humidity"],
        (
            "Environmental health is at Medium monitoring level. 78°F outdoor with 65% "
            "humidity and 84% average crowd density creates elevated heat stress risk "
            "in enclosed sections.\n\n"
            "Watch for fan distress in Lower Concourse East and restock water stations at "
            "Gate Plaza before halftime. Go to the Environmental Health page for the full "
            "risk factor breakdown."
        ),
    ),
]

OVERVIEW_FALLBACK = (
    "I can help with any of the four systems — waste, energy, water, or environmental health — "
    "or give you a rundown of what to prioritise right now. What do you need?"
)


AAR_FALLBACK = (
    "I can help you think through what to do differently next event — ask about waste, "
    "energy, water, staffing, or anything else from tonight."
)


# ── Public API ─────────────────────────────────────────────────────────────────

def get_waste_response(question: str, history: list[dict] | None = None) -> str:
    result = _ask_gemini(
        "Waste Intelligence page. Topics: diversion rates, bin placement by zone, "
        "POS packaging mix, green team ambassador actions, procurement flags.",
        question, history,
    )
    return result or _match(question, WASTE_RESPONSES, WASTE_FALLBACK)


def get_energy_response(question: str, history: list[dict] | None = None) -> str:
    result = _ask_gemini(
        "Energy & Carbon page. Topics: total energy load, lighting vs occupancy divergence, "
        "HVAC zoning, adaptive dimming actions, energy pace vs historical average.",
        question, history,
    )
    return result or _match(question, ENERGY_RESPONSES, ENERGY_FALLBACK)


def get_water_response(question: str, history: list[dict] | None = None) -> str:
    result = _ask_gemini(
        "Water Usage page. Topics: total water consumption, L per fan vs 20 L guide, "
        "restroom demand peaks, system breakdown (restrooms 67%, concessions 19%, "
        "HVAC 9%, irrigation 5%), halftime surge preparation.",
        question, history,
    )
    return result or _match(question, WATER_RESPONSES, WATER_FALLBACK)


def get_env_response(question: str, history: list[dict] | None = None) -> str:
    result = _ask_gemini(
        "Environmental Health page. Topics: outdoor temperature, AQI, humidity, "
        "crowd density, heat stress risk, egress status, water station restocking.",
        question, history,
    )
    return result or _match(question, ENV_RESPONSES, ENV_FALLBACK)


def get_overview_response(question: str, history: list[dict] | None = None) -> str:
    result = _ask_gemini(
        "Overview / Decision Board page. This is the main ops dashboard showing all four "
        "systems: Waste (High), Energy (Medium), Water (Medium), Environmental Health (Medium). "
        "Focus on cross-system priorities and what to do before halftime.",
        question, history,
    )
    return result or _match(question, OVERVIEW_RESPONSES, OVERVIEW_FALLBACK)


def get_aar_response(question: str, history: list[dict] | None = None) -> str:
    result = _ask_gemini(
        "After Action Report page. The event has ended. You are helping the operations manager "
        "reflect on what happened and prepare for the next event. Topics: what went well, "
        "what missed targets, what actions to take before the next event, procurement changes, "
        "staffing improvements, bin placement strategy, energy and water benchmarks.",
        question, history,
    )
    return result or AAR_FALLBACK
