import streamlit as st
from utils import data_io as io
import charts
from PIL import Image

st.set_page_config(page_title="Project Overview & Central Narrative:", layout="wide")

st.title("Narrative Visualization - Childcare Costs and Associated National Socioeconomic Factors")
st.write(Image.open('images/st_project_graphic.jpg'))
st.write("Outline central analysis questions/aims in numbered list.")
st.write("Brief overview of each page in the side bar.")

st.info("Dataset: [National Database of Childcare Prices](https://github.com/rfordatascience/tidytuesday/blob/main/data/2023/2023-05-09/readme.md).")
