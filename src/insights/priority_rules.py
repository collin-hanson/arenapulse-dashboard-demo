def classify_threshold(value: float, yellow_at: float, red_at: float) -> str:
    if value >= red_at:
        return "red"
    if value >= yellow_at:
        return "yellow"
    return "green"


def diversion_gap(expected_diversion: float, current_capture: float) -> float:
    return max(expected_diversion - current_capture, 0)


def status_label(status: str) -> str:
    return {"red": "High priority", "yellow": "Monitor", "green": "Stable"}.get(status, status)
