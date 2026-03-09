import streamlit as st
from utils import data_io as io
import charts
from PIL import Image

st.set_page_config(page_title="Project Overview & Central Narrative:", layout="wide")

st.title("Narrative Visualization - Childcare Costs and Associated National Socioeconomic Factors")
st.write(Image.open('images/st_project_graphic.jpg'))
st.write(
    """
**Introduction**

Childcare costs have become one of the most pressing economic concerns for families in the United States. Over the past two decades, the cost of formal childcare services has risen substantially, reshaping household financial decisions and influencing labor market participation, particularly for women. For families with young children, childcare is not a discretionary expense but a prerequisite for employment. As a result, fluctuations in childcare prices can affect whether parents—especially mothers—enter or remain in the labor force.

At the same time, the burden of childcare costs is unlikely to be evenly distributed across geographic regions. The United States exhibits substantial variation in income levels, poverty rates, labor market structures, and demographic composition across counties. Urban counties tend to have higher wages and higher living costs, while rural counties often face lower income levels, different labor market opportunities, and more limited service availability. These structural differences may shape both the supply of childcare providers and the demand for formal childcare services.

Understanding how childcare costs evolve across space and time is therefore critical for evaluating economic inequality and labor market dynamics. Rising childcare prices may constrain employment for lower-income households, exacerbate regional disparities, or reinforce existing inequalities in women’s labor force participation. Conversely, higher childcare costs may also reflect stronger labor markets and higher demand in economically vibrant areas.

This project investigates how childcare costs evolve over time across U.S. counties and how these changes relate to poverty and women’s labor force participation, with particular emphasis on differences between rural and urban counties. By examining county-level data over a ten-year period, we aim to situate childcare affordability within broader socioeconomic conditions and regional variation.
"""
)

st.write("On the sidebar: the Methods tab goes into detail on the data, preprocessing, and research analysis questions. The Explore tab displays the visualizations, allows for interactivity, and explains key findings in a narrative format.")

st.info("Dataset: [National Database of Childcare Prices](https://github.com/rfordatascience/tidytuesday/blob/main/data/2023/2023-05-09/readme.md).")
st.info("The link above leads to Github repository where the historical childcare cost data is hosted in a structured format." \
" The README file for the repository directly links the original data source, the National Database of Childcare Prices.")
