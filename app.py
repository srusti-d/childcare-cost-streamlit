import streamlit as st
from utils import data_io as io
import charts
from PIL import Image

st.set_page_config(page_title="Project Overview & Central Narrative:", layout="wide")

st.title("Narrative Visualization - English Premier League")
st.write(Image.open('images/epl.jpg'))
st.write("This project is a data story analyzing and visualizing English Premier League team data from two seasons, examining team performance and penalties.\n")
st.write("The data story will explore the following central analysis questions:\n\n 1) How does EPL team performance vary in home games within and across seasons?\n\n 2) Is there a relationship between the cumulative number of red cards a team gets and their performance in the season?\n\n 3) How does disciplinary action vary between referees at a match-level, and what type of penalties occur in each of these matches?\n\n")
st.write(
    "To explore this visual data story, please navigate it through the pages in the sidebar:\n\n"
    "- **Methodology**: We lay down some key details about the data, preprocessing, visualization, and limitations to our analysis.\n"
    "- **Exploration**: Enables viewer-driven exploration of the interactive visualizations. We begin by taking into account season-wide performance metrics, then allowing match-level selection and referee filtering. \n"
)

st.info("Dataset: [English Premier League Data](https://datahub.io/core/english-premier-league).")
