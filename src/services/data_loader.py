"""Load prototype Excel data into pandas dataframes."""

from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw"


@st.cache_data
def load_excel_workbook(filename: str) -> dict[str, pd.DataFrame]:
    path = DATA_DIR / filename
    return pd.read_excel(path, sheet_name=None)
