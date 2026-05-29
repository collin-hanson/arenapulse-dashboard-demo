"""
Simulated AI assistant for ArenaPulse demo.

Matches user questions against pre-written responses using keyword scoring.
Streams responses character-by-character to simulate live generation.
When a real OpenAI key is available, swap _get_response() for an API call.
"""

from __future__ import annotations

import time


# ── Matching logic ─────────────────────────────────────────────────────────────

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


def stream_response(text: str, delay: float = 0.018):
    """Yields the response one character at a time for st.write_stream()."""
    for char in text:
        yield char
        time.sleep(delay)


# ── Waste responses ────────────────────────────────────────────────────────────

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
        ["gate", "plaza", "overflow", "capacity"],
        (
            "Gate Plaza bins are near capacity and the halftime surge arrives in approximately "
            "18 minutes. Current flow is manageable but will hit overflow during peak demand.\n\n"
            "Action: move overflow bins to Gate Plaza now and pre-position 2 extra compost "
            "bins before halftime. This is time-sensitive — once the surge starts it's too "
            "late to reposition without disrupting fan flow."
        ),
    ),
    (
        ["ambassador", "green team", "staff", "team"],
        (
            "Your green team ambassador should be redirected to Lower Concourse East "
            "immediately. That's the highest-volume waste zone with the most diversion "
            "opportunity tonight.\n\n"
            "Key tasks:\n"
            "• Place compost signage at the hot food vendor stands\n"
            "• Assist fans with sorting at the bin stations\n"
            "• Confirm bin coverage before the halftime surge\n\n"
            "After halftime, Gate Plaza becomes the priority as density peaks there "
            "during the second half."
        ),
    ),
]

WASTE_FALLBACK = (
    "Based on tonight's data, the highest-leverage action is redirecting your green team "
    "ambassador to Lower Concourse East and moving overflow bins to Gate Plaza before halftime.\n\n"
    "The 54% max possible diversion ceiling is set by the packaging mix sold tonight — "
    "the gap between current diversion and that ceiling is closeable through bin placement "
    "and ambassador coverage in the right zones.\n\n"
    "Is there a specific zone or action you'd like more detail on?"
)


# ── Energy responses ───────────────────────────────────────────────────────────

ENERGY_RESPONSES: list[tuple[list[str], str]] = [
    (
        ["lighting", "high", "why", "load"],
        (
            "Lighting is at 73% of tracked load tonight, which is elevated but not yet "
            "critical. The issue isn't the load percentage itself — it's whether occupancy "
            "has diverged from lighting coverage.\n\n"
            "Right now occupancy hasn't dropped enough to trigger adaptive dimming. The "
            "action is to watch section by section — specifically the lower bowl — and act "
            "the moment a zone empties out. Pre-identify which zones can be dimmed so the "
            "response is immediate when the trigger hits."
        ),
    ),
    (
        ["halftime", "watch", "occupancy", "diverge", "drop"],
        (
            "At halftime, fans move to concourses and restrooms — sections in the lower bowl "
            "will empty out temporarily. That's the trigger point for adaptive lighting.\n\n"
            "Before halftime:\n"
            "• Identify which lower bowl sections are likely to empty\n"
            "• Confirm the dimming zones are pre-configured\n"
            "• Monitor occupancy in real time as halftime starts\n\n"
            "If any section drops below 75% occupancy while lighting stays at full load, "
            "that's your signal to apply adaptive dimming. Act within the first 5 minutes "
            "of halftime to capture the full energy saving window."
        ),
    ),
    (
        ["hvac", "cooling", "air"],
        (
            "HVAC is at 18% of tracked load tonight and is currently Stable. Zone-based "
            "cooling is running as expected.\n\n"
            "If occupancy drops in any section at halftime, check whether HVAC is still "
            "conditioning those zones — unoccupied sections running at full cooling is "
            "the secondary energy action after lighting. It's a smaller lever but worth "
            "checking if lighting divergence is already being addressed."
        ),
    ),
    (
        ["average", "avg", "above", "below", "compare", "history"],
        (
            "Tonight is running approximately 2,931 kWh above the 10-event average. "
            "That's within a normal range for a high-attendance night — 91% occupancy "
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
    "Tonight's energy is running slightly above average at 1.8 kWh per fan. The main "
    "thing to watch is lighting vs occupancy divergence — if any section empties at "
    "halftime while lighting stays at full load, that's the trigger to apply adaptive dimming.\n\n"
    "Lighting accounts for 73% of tracked load, so it's the highest-leverage system. "
    "Is there a specific system or action you'd like more detail on?"
)


# ── Water responses ────────────────────────────────────────────────────────────

WATER_RESPONSES: list[tuple[list[str], str]] = [
    (
        ["high", "why", "above", "average", "usage", "elevated"],
        (
            "Tonight's water usage is running about 55,615 L above the 10-event average. "
            "At 91% occupancy, that's expected — restroom demand scales directly with "
            "attendance and tonight is a high-density event.\n\n"
            "The 24.5 L per fan figure is above the 20 L sustainability guide, but that "
            "guide is a planning benchmark, not a game-night target. You can't meaningfully "
            "reduce it mid-event. The number is useful for post-event reporting and "
            "long-term fixture planning."
        ),
    ),
    (
        ["restroom", "halftime", "surge", "blockage", "fault"],
        (
            "Restrooms account for approximately 67% of total water usage on event nights "
            "and peak sharply at halftime.\n\n"
            "The one operational action available: walk the restroom banks at Lower Concourse "
            "East before halftime. If a fixture is blocked or faulted, catching it now "
            "prevents a fan-facing incident at peak demand.\n\n"
            "You have roughly 18 minutes before halftime. A blocked fixture during the surge "
            "is the only water scenario that creates an operational problem tonight."
        ),
    ),
    (
        ["system", "restroom", "concession", "hvac", "irrigation", "breakdown"],
        (
            "Tonight's estimated water split by system:\n\n"
            "• Restrooms — 67% (~1,053,843 L). Dominant consumer, peaks at halftime.\n"
            "• Concessions & food prep — 19% (~298,851 L). Steady throughout the event.\n"
            "• HVAC & cooling — 9% (~141,561 L). Higher on warm nights like tonight.\n"
            "• Field irrigation — 5% (~78,645 L). Confirmed off during event window.\n\n"
            "Restrooms are the only system with real-time operational relevance. "
            "The rest are background and stable."
        ),
    ),
    (
        ["leak", "detection", "anomaly", "spike"],
        (
            "Active leak detection is in monitor mode tonight. No anomalies have been "
            "flagged from the submeters.\n\n"
            "If a submeter spike is reported above baseline during the event, escalate "
            "immediately — do not wait for the post-event report. A slow leak during a "
            "high-attendance event can result in significant undetected loss.\n\n"
            "Field irrigation is confirmed off for the event window, so any spike in "
            "that submeter would warrant an immediate check."
        ),
    ),
]

WATER_FALLBACK = (
    "Water is in monitor mode tonight. Usage is slightly above average, which is expected "
    "at 91% occupancy.\n\n"
    "The one action available before halftime: walk the restroom banks at Lower Concourse "
    "East to catch any fixture fault before the surge hits. Everything else — leak detection, "
    "irrigation, HVAC cooling — is passive and stable.\n\n"
    "Is there a specific system or concern you'd like more detail on?"
)


# ── Environmental health responses ─────────────────────────────────────────────

ENV_RESPONSES: list[tuple[list[str], str]] = [
    (
        ["heat", "stress", "why", "elevated", "hot", "temperature"],
        (
            "Heat stress is flagged as Monitor tonight because of the combination of three "
            "factors — not temperature alone.\n\n"
            "78°F outdoor temperature compounds with 65% humidity and 84% average crowd density. "
            "At this humidity level, the body's ability to cool through sweat is reduced. "
            "High crowd density slows heat dissipation further — body heat builds up in "
            "enclosed concourse sections faster than HVAC can compensate.\n\n"
            "Outdoor areas without shade are the highest risk zones. Lower Concourse East "
            "has the highest density tonight and should be the focus for any welfare checks."
        ),
    ),
    (
        ["humidity", "combination", "dangerous", "exhaustion"],
        (
            "Humidity + heat is a more dangerous combination than either factor alone. "
            "Above 75°F with humidity over 65%, heat exhaustion onset accelerates — "
            "the body struggles to cool itself through perspiration.\n\n"
            "Tonight is sitting right at the threshold: 78°F and 65% humidity. It's not "
            "critical, but the combination means fans in enclosed sections are at elevated "
            "risk, particularly during the halftime crowd surge when density peaks.\n\n"
            "Watch for fans showing visible distress in Lower Concourse East. Water station "
            "queue lengths are an early indicator of heat stress onset."
        ),
    ),
    (
        ["aqi", "air", "quality", "ventilation"],
        (
            "AQI is 52 tonight — moderate, but acceptable. At this level there's no risk "
            "to the general population and no action required.\n\n"
            "Ventilation is running at capacity in indoor concourses. CO₂ buildup in enclosed "
            "areas is possible at high crowd density but not yet flagged.\n\n"
            "Watch for any HVAC fault alerts or unusual odor reports from concourses — those "
            "are the triggers for escalation. If outdoor AQI climbs above 100, a PA guidance "
            "to move fans indoors would be warranted."
        ),
    ),
    (
        ["egress", "exit", "crowd", "gate", "plaza", "safety"],
        (
            "Egress is currently Stable across all exits. Gate Plaza at 92% density is the "
            "highest-risk exit zone — current flow is managed, but halftime will test it.\n\n"
            "Key things to watch at halftime:\n"
            "• Gate Plaza density before and during halftime\n"
            "• Any exit obstruction reports\n"
            "• Emergency egress path clearance\n\n"
            "Notify immediately if an exit blockage is reported OR if Gate Plaza density "
            "exceeds 95%. Above 92% in a zone, clear exit paths take priority over "
            "all other actions."
        ),
    ),
    (
        ["water", "station", "hydration", "restock"],
        (
            "Given 78°F outdoor temperature and 65% humidity, hydration demand will spike "
            "at halftime. Water stations at Gate Plaza and Lower Concourse East are the "
            "highest-demand locations based on current crowd density.\n\n"
            "Restock both stations before halftime if they haven't been checked recently. "
            "Empty water stations during peak heat and density is the most likely "
            "fan-facing incident from tonight's environmental conditions."
        ),
    ),
]

ENV_FALLBACK = (
    "Tonight's environmental conditions are at a Medium monitoring level — 78°F outdoor, "
    "65% humidity, and 84% average crowd density. No single factor is critical, but the "
    "combination elevates heat stress risk, particularly in enclosed sections.\n\n"
    "The main things to watch before halftime are water station levels at Gate Plaza "
    "and Lower Concourse East, and fan welfare in high-density enclosed areas.\n\n"
    "Is there a specific risk factor you'd like more detail on?"
)


# ── Overview responses ─────────────────────────────────────────────────────────

OVERVIEW_RESPONSES: list[tuple[list[str], str]] = [
    (
        ["priority", "first", "most important", "urgent", "act", "now"],
        (
            "The highest priority right now is waste response in Lower Concourse East.\n\n"
            "It has the highest waste volume, a food-heavy packaging mix, and the most "
            "diversion opportunity before halftime in 18 minutes. Redirect your green team "
            "ambassador there now and place compost signage at the hot food vendor stands.\n\n"
            "Second priority: move overflow bins to Gate Plaza before the halftime surge — "
            "existing bins will hit capacity during peak demand."
        ),
    ),
    (
        ["halftime", "before", "prepare", "surge", "next"],
        (
            "Before halftime in 18 minutes, three things need to happen:\n\n"
            "1. Waste — Move overflow bins to Gate Plaza and redirect the green team "
            "ambassador to Lower Concourse East.\n\n"
            "2. Water — Walk the restroom banks at Lower Concourse East to catch any "
            "fixture fault before the surge hits.\n\n"
            "3. Energy — Pre-identify lower bowl sections that may empty at halftime. "
            "If occupancy drops while lighting stays high, apply adaptive dimming.\n\n"
            "Environmental conditions are at monitoring level — restock water stations "
            "at Gate Plaza if they haven't been checked recently."
        ),
    ),
    (
        ["waste", "diversion"],
        (
            "Waste is the highest-alert system tonight. Diversion is 26 points below the "
            "maximum possible ceiling of 54%.\n\n"
            "The gap is closeable through bin placement and ambassador coverage — specifically "
            "in Lower Concourse East, which has the highest waste volume and food-heavy "
            "packaging mix. Gate Plaza bins are also near capacity ahead of halftime.\n\n"
            "Go to the Waste page for the full breakdown by zone."
        ),
    ),
    (
        ["energy", "lighting", "power"],
        (
            "Energy is at Medium status tonight. Lighting is running at 73% of tracked load "
            "which is elevated but not yet critical.\n\n"
            "The trigger for action is occupancy divergence — if a section empties at "
            "halftime while lighting stays at full load, apply adaptive dimming immediately. "
            "Pre-identify the lower bowl sections most likely to empty.\n\n"
            "Go to the Energy page for the full system breakdown."
        ),
    ),
    (
        ["water", "restroom"],
        (
            "Water is at Medium monitoring status. Usage is above the 20 L per fan guide "
            "at 24.5 L, which is expected at 91% occupancy.\n\n"
            "The one game-night action: walk the restroom banks at Lower Concourse East "
            "before halftime. A blocked fixture during the surge is the only water scenario "
            "that creates a real operational problem tonight.\n\n"
            "Go to the Water page for the system breakdown."
        ),
    ),
    (
        ["environment", "heat", "temperature", "humidity"],
        (
            "Environmental health is at Medium monitoring level. 78°F outdoor with 65% "
            "humidity and 84% average crowd density creates elevated heat stress risk in "
            "enclosed sections.\n\n"
            "Watch for fans showing distress in Lower Concourse East, and restock water "
            "stations at Gate Plaza and Lower Concourse East before halftime.\n\n"
            "Go to the Environmental Health page for the full risk factor breakdown."
        ),
    ),
]

OVERVIEW_FALLBACK = (
    "Right now the highest priority is waste response — redirect your green team ambassador "
    "to Lower Concourse East and move overflow bins to Gate Plaza before halftime in 18 minutes.\n\n"
    "All four systems are active tonight: Waste is High, Energy and Water are Medium, "
    "Environmental Health is Medium. The Waste page has the most actionable decisions right now.\n\n"
    "Is there a specific system or action you'd like more detail on?"
)


# ── Public API ─────────────────────────────────────────────────────────────────

def get_waste_response(question: str) -> str:
    return _match(question, WASTE_RESPONSES, WASTE_FALLBACK)

def get_energy_response(question: str) -> str:
    return _match(question, ENERGY_RESPONSES, ENERGY_FALLBACK)

def get_water_response(question: str) -> str:
    return _match(question, WATER_RESPONSES, WATER_FALLBACK)

def get_env_response(question: str) -> str:
    return _match(question, ENV_RESPONSES, ENV_FALLBACK)

def get_overview_response(question: str) -> str:
    return _match(question, OVERVIEW_RESPONSES, OVERVIEW_FALLBACK)
