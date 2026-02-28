import streamlit as st
import pandas as pd
from vega_datasets import data

@st.cache_data
def load_weather() -> pd.DataFrame:
    df = data.seattle_weather()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")
    return df
