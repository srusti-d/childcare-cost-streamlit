import streamlit as st
import altair as alt
import pandas as pd
from utils import data_io as io
import charts
from PIL import Image
import copy

GEOJSON_URL = "https://raw.githubusercontent.com/srusti-d/childcare-cost-streamlit/main/data/geojson-counties-fips.json"

# Page config
st.set_page_config(page_title="Explore Childcare Cost Analysis", layout="wide")

# Load data 

@st.cache_data(show_spinner="Loading and preprocessing data…")
def get_data():
    return io.load_and_preprocess_all(
        childcare_path="./data/childcare_costs.csv",
        counties_path ="./data/counties.csv",
        rucc_path     ="./data/Ruralurbancontinuumcodes2023.csv",
        geojson_path  ="./data/geojson-counties-fips.json",
    )

if "data" not in st.session_state:
    st.session_state["data"] = get_data()

data = st.session_state["data"]

st.title("Exploring U.S. Childcare Costs (2008–2018)")
st.markdown(
    """
    This page walks through five visualisations that together tell the story of
    how childcare costs relate to poverty, female labour-force participation rate (FLFPR or female LFPR), and
    across the United States over a decade and within varying rural/urban geography.
    Many of these plots are interactive.
    """
)

st.divider()

# National average childcare cost trend

st.header("National Average Childcare Cost Over Time")

st.markdown(
    """
**Why we start here:**

Before examining inequality across counties, we first step back and ask a simpler question: **what is happening to childcare costs overall?**

Because our dataset varies across both **space (counties)** and **time (years)**, it is important to establish the broad temporal pattern before zooming into geographic variation.  
If childcare costs were mostly stable over time, then county-level differences might dominate the story. But if costs are rising nationally, then spatial disparities occur against a backdrop of **increasing baseline costs across the country**.

To establish this baseline, we aggregate childcare costs across all counties and examine the **national median weekly center-based childcare cost (mcsa)** from 2008 to 2018.
"""
)

cost_chart = charts.make_cost_trend_line(data["cost_trend"])
st.altair_chart(cost_chart, use_container_width=False)
st.caption("Figure 1: Line plot displaying average U.S. national childcare cost (median, weekly center-based care) over one decade.")

with st.expander("Key findings", expanded=False):
    st.markdown(
        """
- The national average childcare cost shows a **clear and steady upward trend** over the decade.
- Average weekly costs increase from roughly **\$90 in 2008 to more than \$110 by 2018**.
- This suggests rising childcare costs reflect a broad, nationwide trend.
- County-level differences therefore emerge **within a system where the overall cost baseline is steadily increasing**.
        """
    )

st.divider()

# State-level choropleth maps with year slider

st.header("Childcare Cost, Female Labor Force Participation Rate (FLFPR) & Poverty Rate by State")
st.markdown(
    """
After establishing the national trend in childcare costs, we next ask whether
this pattern appears consistently **across states and over time**.

Use the **Year** slider to step through each study year and compare how
three state-level metrics change together:

* Center-based childcare cost  
* Female labor-force participation rate (ages 20–64)  
* Family poverty rate  

Viewing these maps together allows us to compare how childcare prices align
with broader socioeconomic conditions across the United States.

"""
)

# choropleth = charts.make_sliding_choropleth_maps(
#     data["geo_features"],
#     data["state_metrics"],
    
# )
# st.altair_chart(choropleth, use_container_width=False)

st.write(Image.open('images/2008_choropleth_screenshot.png'))
st.caption("Figure 2: Static image of interactive choropleth map with slider at *2008* year displaying changes in childcare cost, poverty rate, and female labor force participation rate across the United States.")

st.write(Image.open('images/2018_choropleth_screenshot.png'))
st.caption("Figure 3: Static image of interactive choropleth map with slider at *2018* year displaying changes in childcare cost, poverty rate, and female labor force participation rate across the United States.")
st.write("*Note:* Our original interactive visualization allows for the year slider to be directly adjusted by the viewer, enabling a personalized interaction experience showing patterns in missing data, but due to streamlit incompatibility issues, we are displaying static images of the first and last year for the plot in this report. The interactive plot also contains a tooltip enabling details of state-specific metrics to be shown.")

with st.expander("Key findings", expanded=False):
    st.markdown(
        """
The figure serves an important **data diagnostic purpose**. As we move
through the years, it becomes clear that some states (especially in the Southwest and Northwest) appear or disappear in
the childcare cost map due to missing observations in the underlying dataset. This
uneven coverage means that apparent changes over time could reflect shifts
in data availability rather than real economic trends if the current data is used without additional processing.

Identifying this missing data issue motivated a key methodological decision in the next step of our
analysis: restricting parts of the study to a balanced subset of states
with complete data coverage across the 2008-2018 period.

Beyond the missing childcare data, three broad patterns emerge from the state-level maps.

• **Childcare costs rise steadily across much of the country.**  
Some states in particular show increasing childcare prices between 2008 and 2018,
influencing the national upward trend (e.g. see California's increase in childcare cost over a decade).

• **Regional differences are persistent.**  
States in the Northeast and West Coast tend to have the highest
childcare costs, while many Southern states remain lower-cost markets.

• **Socioeconomic patterns are geographically concentrated.**  
Higher female labor force participation is common in the Midwest and
Northeast, while higher poverty rates remain concentrated in the South.
    """)

st.divider()


# Urban vs rural county classification maps

st.header("Urban vs Rural Counties — 8 State Sample")
st.markdown("Given that the national chorpleth map can obscure local (within state) data patterns, and the presence of missing childcare cost data, we now sample both primarily rural and primarily urban states for our analysis.")
st.markdown(
    """

**How to use this map**

Hover over any county within each state to view:
    - Average weekly childcare cost  
    - Female labor force participation rate  
    - Family poverty rate  
    - Whether the county is classified as **Urban** or **Rural**


As we explored the state-level maps across years, a clear issue emerged: **data availability is not uniform across states**. 
Some states contain complete observations for childcare costs, poverty, and female labor force participation throughout 
the 2008–2018 period, while others have missing values in certain years or variables. Including all states without accounting 
for this missingness could distort the trends we observe over time.

To preserve comparability, we therefore restrict part of our analysis to a **balanced sample of states with full data coverage**. 
Focusing on this subset ensures that the patterns we analyze reflect genuine economic differences rather than shifts in which 
states appear in the dataset.

Within these states, we then examine variation at the **county level**, counties are classified as **Urban** (USDA RUCC code ≤ 3) or **Rural**
(code ≥ 4) using the 2023 Rural-Urban Continuum Codes. The sample covers four predominantly urban states (Massachusetts, California, Arizona, Delaware)
and four predominantly rural states (North Dakota, Kansas, Oklahoma, Vermont).Hover over any county to see its average childcare cost, poverty rate, and
female labor-force participation rate.

This map provides a geographic overview of the counties included in our balanced sample. By visualizing the spatial 
distribution of urban and rural counties within each state, the figure establishes the core comparison that drives the 
rest of our analysis: how childcare costs, poverty, and female labor force participation differ across fundamentally 
different county types.
    

"""
)

urb_rural = charts.make_urban_rural_state_maps(
    data["county_avg"],
    data["geo_counties_raw"],
    data["sample_states"],

)
st.altair_chart(urb_rural, use_container_width=False)
st.caption("Figure 4: Static plot displaying state maps for the rural and urban sample we selected, with a tooltip showing county-level metrics for three socioeconomic variables.")

with st.expander("Key findings", expanded=False):
    st.markdown(
"""
Three central patterns that you can explore the details of using the tooltip for the urban/rural state maps.

• **Urban counties consistently face higher childcare costs.**  
Across the sample, childcare prices tend to be significantly higher in urban counties. 
In several states—including Alaska, New York, Colorado, and Maryland—the gap between 
urban and rural counties exceeds $40 per week.

• **Rural counties generally experience higher poverty rates.**  
Although childcare costs are lower in rural areas, these counties often face higher 
poverty rates. On average, rural poverty exceeds urban poverty by roughly three 
percentage points, suggesting that affordability challenges remain despite lower prices.

• **Female labor force participation rate differences are smaller and less consistent.**  
Participation rates do not display a uniform urban–rural pattern. In some states urban 
counties have higher participation rates, while in others rural counties do. This suggests 
that higher urban childcare costs may be more closely tied to broader socioeconomic conditions than simply to female labor participation.
"""
)

st.divider()


# Density heatmaps (poverty + LFPR)

st.header("Childcare Cost vs Poverty Rate & Female Labor Force Participation Rate (LFPR)")
st.markdown(
    """
After sampling states, we aim to make the patterns described in the key findings above more easily visible and identifiable at a local level through a perceptually straightforward visualization.
Here, we zoom in on **how childcare costs relate to key socioeconomic conditions**.
These heatmaps let us see the **overall distribution** (where most counties cluster) while the regression lines
summarize the **direction of the relationship** within each county type.
"""
)

st.markdown(
    """
Each square represents a bin of counties: darker bins mean **more counties** fall in that combination of values.
The overlaid trend lines show whether the relationship differs across county types.

**Top chart** — childcare cost vs family poverty rate  
**Bottom chart** — childcare cost vs female labor-force participation rate  
"""
)

heatmaps = charts.make_heatmap_stacked(data["county_avg"])
st.altair_chart(heatmaps, use_container_width=False)
st.caption("Figure 5: Combined heatmap and line plot displaying urban-rural differences in childcare cost versus poverty rate and female LFPR, respectively")
with st.expander("Key findings", expanded=False):
    st.markdown(
        """
- **Urban counties sit at a higher cost baseline** across the entire distribution: even where poverty/female LFPR is similar, urban bins tend to appear at higher childcare-cost levels.
- The **within-type relationships are weakly negative** here (both lines slope slightly downward), meaning higher poverty or higher female LFPR is *not* strongly associated with higher childcare costs within county type in this sample.
- The biggest visual pattern is **level differences (urban vs rural)** rather than steep within-type slopes—suggesting geography/urbanicity matters more for cost levels than these predictors alone.
- The densest clusters show where “typical” counties are concentrated: **rural counties cluster at lower costs**, while **urban counties cluster at higher costs**, reinforcing the persistent cost gap.
"""
    )


st.divider()

st.header("Interactive County-Level Dashboard")
st.markdown(
    """
This dashboard lets you zoom in from the national picture down to **individual states and counties**.

**How to explore the dashboard**

1. Use the **year slider** to change the year of the data.
2. Select a **state** from the dropdown menu.
3. **Hover over counties** on the state map to view childcare cost, poverty rate, and female labor force participation.
4. **Click a data point in the scatterplot** to highlight that county on the map (or vice versa, click on map to highlight on scatterplot) and compare its socioeconomic metrics with others using the scatterplot and bar chart.
3. Each point on the scatter plot for the state corresponds to a county in the displayed state. **Click a county** (each point) in the scatter plot to compare its female labor force participation rate against its state average in the bar chart.

We built this dashboard to move from the question **“Are childcare costs rising?”** to a more detailed one:
**“What kinds of places experience higher childcare costs?”**

By combining three views—a county map, a poverty–cost scatterplot, and a labor force participation comparison—
the dashboard allows us to examine how childcare prices align with **local economic conditions within each state**.

The map shows the geographic distribution of childcare costs across counties.  
The scatterplot reveals how childcare prices relate to poverty levels.  
The labor participation comparison highlights differences in female labor market engagement.

Together, these views make it possible to explore how childcare costs interact with **regional labor markets and
economic conditions at the county level.**

"""
)

# Make dashboard

st.markdown("##### State Map Dashboard with County-Level Childcare Cost, Poverty Rate, and Female LFPR Exploration")

dashboard = charts.make_county_dashboard(data["geo_merged"])
st.altair_chart(dashboard, use_container_width=False)
st.caption("Figure 6: Interactive dashboard displaying state-specific maps, with clickable counties and their county-specific poverty rate and female labor force participation rate as related to childcare cost.")

with st.expander("Key findings", expanded=False):
    st.markdown(
"""
Several important patterns emerge when exploring the dashboard.

• **Higher childcare costs tend to appear in economically stronger counties.**  
Across the sample, counties with higher childcare prices often display **lower poverty rates and higher female labor force participation**.

• **This relationship becomes especially strong in urban economies after the early 2010s.**  
In the years immediately following the Great Recession (2008), childcare costs and female labor participation show little or even negative association in urban areas. Beginning around 2014, however, the relationship becomes strongly positive: counties with higher childcare costs are increasingly those with stronger female labor market engagement.

• **Rural counties show a weaker but more stable pattern.**  
In rural states the relationship between childcare costs and labor participation remains moderately positive throughout the period, without the sharp shift seen in urban areas.

Taken together, these results suggest that **rising childcare costs are not solely a sign of overall national economic distress**. Instead, they increasingly appear connected to **location, active regional labor markets, and higher levels of female employment**, particularly in urban regions.

This reframes the analysis of the research question about the relationship of childcare cost to broader socioeconomic conditions across state geography and time. The relationship between poverty rate and female labor force participation as related to childcare costs is more variable when compared across predominantly urban vs rural states. 
This means that rising childcare prices, though a national pattern, reflect the structure and strength of U.S. regional, state, and local/county-level economic conditions and labor markets.

"""
)