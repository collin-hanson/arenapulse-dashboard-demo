# ArenaPulse — Stadium Sustainability Dashboard

A real-time operations dashboard for stadium sustainability management. Built to consolidate waste, energy, water, and environmental health data into a single decision-making interface for venue operations managers.

**Live demo:** [arenapulse-dashboard-demo.streamlit.app](https://arenapulse-dashboard-demo-vsugksbudetfmtjpwbxxac.streamlit.app/)

---

## Overview

ArenaPulse addresses a core frustration in venue operations: sustainability and environmental data is spread across multiple software systems. This dashboard brings it all into one place, surfacing actionable decisions in real time rather than post-event reports.

**Pages:**
- **Overview** — Decision board with live venue status, zone density map, and operational priorities across all systems
- **Energy** — Load tracking, lighting vs occupancy divergence detection, and pace vs historical average
- **Waste** — Diversion opportunity by zone, POS-driven bin placement intelligence, and procurement flags
- **Water** — Usage monitoring, cumulative pace chart, and system-level breakdown
- **Environmental Health** — Live conditions (temp, AQI, humidity, wind, density) and risk factor assessment

**AI Assistant** — Each page includes a simulated AI assistant that answers questions grounded in live event data. Designed to be replaced with a live OpenAI API integration when a key is available.

---

## Status

This is a prototype built on demo data. No live POS, payment, or customer data is stored or processed.

---

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Project Structure

```
app.py                        # Entry point and navigation
src/
  pages/                      # One file per dashboard page
  components/                 # Reusable UI components
  services/                   # Data loading, demo data, AI assistant
  utils/                      # Page config and shared formatting
data/
  raw/                        # Demo Excel workbook
```

---

## Security Notes

- All POS data must pass through a strict allow-list sanitization layer before ingestion
- Approved operational fields only: item category, quantity, timestamp, vendor location, section, packaging type, waste stream flags
- Payment data, customer IDs, loyalty IDs, and transaction amounts are never stored or processed
- Do not commit real credentials, API keys, or raw POS payloads to this repository

---

## Roadmap

- [ ] Live OpenAI API integration (key pending)
- [ ] Real-time data ingestion layer — multi-format (CSV, Excel, JSON, API), allow-listed, sanitized
- [ ] Venue configuration — multi-stadium support
