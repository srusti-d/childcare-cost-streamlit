# U.S. Childcare Cost Explorer

An interactive data visualization app built with Streamlit that explores childcare costs across the United States. Users can explore county and state-level trends in childcare pricing to better understand the socioeconomic landscape facing American families.

**[Live App](https://childcare-cost-app-ixjwc9c8pjjb4b3viq2wgf.streamlit.app/Explore)**

---

## Features

- **Interactive Maps** — Visualize childcare costs geographically across U.S. states and counties
- **Explore Page** — Filter and drill down into cost data by region, care type, and child age group
- **Comparative Analysis** — Compare childcare costs across states or counties side by side
- **Trend Insights** — Understand how costs vary by demographic and geographic factors

---

## Project Structure

```
childcare-cost-streamlit/
├── charts/                 # Python scripts that generate all visualizations and charts
├── data/                   # Childcare and GEOJSON datasets
├── images/                 # Images used in the app 
├── pages/                  # Multipage Streamlit app pages
├── utils/                  # Helper functions for full chart visualization
├── app.py                  # App entry point and home page
└── requirements.txt        # Python dependencies
```

---

## Data Source

This app uses the [National Database of Childcare Prices](https://www.dol.gov/agencies/wb/topics/childcare/national-database-childcare-prices) published by the U.S. Department of Labor, Women's Bureau. The dataset includes median weekly childcare prices by county, care type (home-based vs. center-based), and child age group.

---

## Reprodicible Implementation of Application

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/srusti-d/childcare-cost-streamlit.git
   cd childcare-cost-streamlit
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**

   ```bash
   streamlit run app.py
   ```
This will open your own local copy/version of the application.

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| [Streamlit](https://streamlit.io/) | Web app framework |
| [Pandas](https://pandas.pydata.org/) | Data manipulation |
| [Plotly](https://plotly.com/python/) / [Altair](https://altair-viz.github.io/) | Data visualization |
| [NumPy](https://numpy.org/) | Numerical operations |

---

## Authors and Contributors

**Srusti D.** 
**Ornella N.**
**Alex D.**
