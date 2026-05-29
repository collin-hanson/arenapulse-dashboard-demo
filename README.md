# ArenaPulse Dashboard Prototype

Streamlit prototype for a pilot venue sustainability and operations dashboard.

Run locally:

```powershell
streamlit run app.py
```

Project layout:

- `app.py`: Streamlit entry point and navigation.
- `src/pages`: Top-level dashboard views.
- `src/components`: Reusable UI blocks.
- `src/services`: Data loading and integration code.
- `src/insights`: Priority rules and recommendation logic.
- `src/governance`: Data quality and compliance helpers.
- `src/utils`: Shared formatting and configuration.
- `data/raw`: Demo input workbooks, including `ArenaPulse_Demo_Data.xlsx`.
- `data/processed`: Cleaned or generated data outputs.

Deployment path:

1. Push this folder to GitHub.
2. In Streamlit Community Cloud, connect the GitHub repo.
3. Set the app entry point to `app.py`.
4. Keep demo data only in the public repo. Do not commit real credentials or raw POS payloads.
