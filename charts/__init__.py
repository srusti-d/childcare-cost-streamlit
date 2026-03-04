import altair as alt
import pandas as pd
import geopandas as gpd

from utils.data_io import normalize_features_to_unit_box

def base_theme():
    return {
        "config": {
            "view": {"stroke": None},
            "axis": {"labelFontSize": 12, "titleFontSize": 14},
            "legend": {"labelFontSize": 12, "titleFontSize": 14},
        }
    }


def _prep_heatmap_df(county_avg: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to display-friendly labels and keep Urban/Rural rows."""
    df = county_avg.rename(columns={
        "mcsa":           "Average Childcare Cost",
        "pr_p":           "Poverty Rate (%)",
        "flfpr_20to64":   "Female LFPR (%)",
        "urbanicity_rucc":"County Type",
    })
    return df[df["County Type"].isin(["Urban", "Rural"])].copy()


# Sliding state-level choropleth maps

def make_sliding_choropleth_maps(
    geo_features:  list,
    state_metrics: pd.DataFrame,
) -> alt.VConcatChart:
    """
    Three choropleth maps sharing a year slider for average weekly center-based childcare cost,
    average female labor force participation rate (ages 20-64), and average poverty rate for families.
    """
    geo_data = alt.Data(values=geo_features)
    years    = state_metrics["study_year"].unique()

    year_slider = alt.binding_range(
        min=int(min(years)), max=int(max(years)), step=1, name="Year: "
    )
    year_selection = alt.param(
        name="selected_year", value=int(min(years)), bind=year_slider
    )
    year_filter = "toNumber(datum.properties.study_year) == selected_year"

    def _base_map(field, scheme, domain, legend_title):
        return (
            alt.Chart(geo_data)
            .mark_geoshape(stroke="white", strokeWidth=0.5)
            .transform_filter(year_filter)
            .encode(
                color=alt.Color(
                    f"properties.{field}:Q",
                    scale=alt.Scale(scheme=scheme, domain=domain),
                    title=legend_title,
                ),
                tooltip=[
                    alt.Tooltip("properties.state_name:N", title="State"),
                    alt.Tooltip(f"properties.{field}:Q",   title=legend_title if isinstance(legend_title, str) else legend_title[0], format=".2f"),
                    alt.Tooltip("properties.study_year:Q", title="Year"),
                ],
            )
            .project(type="albersUsa")
        )

    childcare_chart = _base_map(
        "mcsa_mean", "blues",
        [state_metrics["mcsa_mean"].min(), state_metrics["mcsa_mean"].max()],
        ["Average Weekly", "Childcare Cost (Center-Based)"],
    ).properties(
        width=450, height=280,
        title="Average weekly center-based childcare cost (school-age children) by state over a decade",
    )

    poverty_chart = _base_map(
        "pr_f_mean", "oranges",
        [state_metrics["pr_f_mean"].min(), state_metrics["pr_f_mean"].max()],
        "Average poverty rate for families",
    ).properties(
        width=450, height=280,
        title="Average poverty rate for families by state over a decade",
    )

    labor_chart = _base_map(
        "flfpr_20to64_mean", "purples",
        [state_metrics["flfpr_20to64_mean"].min(), state_metrics["flfpr_20to64_mean"].max()],
        ["Average female labor", "participation rate (20-64 y/o)"],
    ).properties(
        width=500, height=300,
        title="Average female labor participation rate (20-64 y/o) by state over a decade",
    )

    bottom_row = alt.hconcat(labor_chart, poverty_chart).resolve_scale(color="independent")

    return (
        alt.vconcat(childcare_chart, bottom_row)
        .add_params(year_selection)
        .resolve_scale(color="independent")
        .properties(title="Childcare cost and socioeconomic metrics (2008-2018) in U.S.")
    )


# 2.  Urban/rural state county maps in an 8-state panel

def make_urban_rural_state_maps(
    county_avg:       pd.DataFrame,
    geo_counties_raw: dict,
    sample_states:    list | None = None,
) -> alt.VConcatChart:
    """
    Panel of county maps coloured by urban/rural classification.
    """
    if sample_states is None:
        sample_states = [
            "California", "New York", "New Jersey", "Massachusetts",
            "North Dakota", "South Dakota", "Vermont", "Wyoming",
        ]

    COST, WLF, POV = "mcsa", "flfpr_20to64", "pr_p"
    county_avg_8 = county_avg[county_avg["state_name"].isin(sample_states)].copy()

    charts = []
    for i, st in enumerate(sample_states):
        state_df = county_avg_8[county_avg_8["state_name"] == st].copy()
        fips_set = set(state_df["county_fips_code"].tolist())

        feats      = [ft for ft in geo_counties_raw["features"] if ft["properties"]["fips5"] in fips_set]
        feats_norm = normalize_features_to_unit_box(feats, pad=0.02)

        ch = (
            alt.Chart(alt.Data(values=feats_norm))
            .mark_geoshape(stroke="white", strokeWidth=0.4)
            .project(type="identity", reflectY=True)
            .transform_lookup(
                lookup="properties.fips5",
                from_=alt.LookupData(
                    state_df,
                    key="county_fips_code",
                    fields=["state_name", "county_name", "urbanicity_rucc", COST, WLF, POV],
                ),
            )
            .encode(
                color=alt.Color(
                    "urbanicity_rucc:N",
                    scale=alt.Scale(domain=["Urban", "Rural"]),
                    legend=alt.Legend(title="County type") if i == 0 else None,
                    title="County type",
                ),
                tooltip=[
                    alt.Tooltip("state_name:N",      title="State"),
                    alt.Tooltip("properties.NAME:N", title="County"),
                    alt.Tooltip("urbanicity_rucc:N", title="Urban/Rural"),
                    alt.Tooltip(f"{COST}:Q", title="Avg childcare cost", format=",.2f"),
                    alt.Tooltip(f"{WLF}:Q", title="Female Labor Force Participation Rate", format=",.2f"),
                    alt.Tooltip(f"{POV}:Q", itle="Poverty rate", format=",.2f"),
                ],
            )
            .properties(
                title=alt.TitleParams(text=st, anchor="middle"),
                width=300, height=240,
            )
        )
        charts.append(ch)

    row1 = alt.hconcat(*charts[:4], spacing=10)
    row2 = alt.hconcat(*charts[4:], spacing=10)
    return (
        alt.vconcat(row1, row2, spacing=14)
        .configure_view(stroke=None)
        .properties(title={
            "text": "Urban vs Rural County Comparison",
            "subtitle": "8-state sample with full data coverage",
        })
    )

# National childcare cost trend line

def make_cost_trend_line(cost_trend: pd.DataFrame) -> alt.LayerChart:
    """
    Line chart of average national childcare cost (mcsa) over time with a
    shaded band marking the 2008-2010 financial crisis period.
    """
    recession = pd.DataFrame({"x1": [2008], "x2": [2010]})
    band = (
        alt.Chart(recession)
        .mark_rect(opacity=0.15, color="gray")
        .encode(x=alt.X("x1:Q", title=""), x2="x2:Q")
    )

    recession_label = pd.DataFrame({
        "x": [2009],
        "y": [cost_trend["mcsa"].max() * 0.98],
        "text": ["Financial Crisis"],
    })
    annotation = (
        alt.Chart(recession_label)
        .mark_text(color="gray", fontSize=11, fontStyle="italic")
        .encode(x="x:Q", y="y:Q", text="text:N")
    )

    line = (
        alt.Chart(cost_trend)
        .mark_line(point=alt.OverlayMarkDef(filled=True, size=60), color="steelblue")
        .encode(
            x=alt.X(
                "study_year:Q",
                title="Year",
                axis=alt.Axis(format="d", tickCount=cost_trend["study_year"].nunique()),
            ),
            y=alt.Y("mcsa:Q", title="Average Childcare Cost (mcsa)", scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip("study_year:Q", title="Year"),
                alt.Tooltip("mcsa:Q",       title="Avg Childcare Cost", format=".2f"),
            ],
        )
    )

    return (
        alt.layer(band, annotation, line)
        .properties(
            width=680, height=380,
            title="Average National Childcare Cost Trend with Financial Crisis Period",
        )
        .resolve_scale(y="shared")
    )


# Heatmap graphs of childcare cost vs poverty rate

def make_heatmap_poverty(county_avg: pd.DataFrame) -> alt.LayerChart:
    """
    Binned density heatmap of childcare cost vs family poverty rate, 
    overlaid with per-county-type OLS regression lines.
    """
    df = _prep_heatmap_df(county_avg)

    heat = (
        alt.Chart(df).mark_rect()
        .encode(
            x=alt.X("Poverty Rate (%):Q", bin=alt.Bin(maxbins=30), title="Poverty Rate (%)"),
            y=alt.Y("Average Childcare Cost:Q", bin=alt.Bin(maxbins=30), title="Average Childcare Cost"),
            color=alt.Color("count():Q", title="# Counties"),
            tooltip=[alt.Tooltip("count():Q", title="# Counties")],
        )
    )

    lines = (
        alt.Chart(df)
        .transform_regression("Poverty Rate (%)", "Average Childcare Cost", groupby=["County Type"])
        .mark_line(size=3)
        .encode(
            x=alt.X("Poverty Rate (%):Q",       title="Poverty Rate (%)"),
            y=alt.Y("Average Childcare Cost:Q", title="Average Childcare Cost"),
            color=alt.Color("County Type:N",    title="County Type"),
        )
    )

    return (heat + lines).properties(
        title="Childcare Cost vs Poverty (Density + Urban/Rural Trend Lines)"
    )


# Heatmap graphs of childcare cost vs female LFPR

def make_heatmap_lfpr(county_avg: pd.DataFrame) -> alt.LayerChart:
    """
    Binned density heatmap of childcare cost vs female LFPR,
    overlaid with per-county-type OLS regression lines.
    """
    df = _prep_heatmap_df(county_avg)

    heat = (
        alt.Chart(df).mark_rect()
        .encode(
            x=alt.X("Female LFPR (%):Q", bin=alt.Bin(maxbins=30), title="Female LFPR (%)"),
            y=alt.Y("Average Childcare Cost:Q", bin=alt.Bin(maxbins=30), title="Average Childcare Cost"),
            color=alt.Color("count():Q", title="# of Counties"),
            tooltip=[alt.Tooltip("count():Q", title="# of Counties")],
        )
    )

    lines = (
        alt.Chart(df)
        .transform_regression("Female LFPR (%)", "Average Childcare Cost", groupby=["County Type"])
        .mark_line(size=3)
        .encode(
            x=alt.X("Female LFPR (%):Q",        title="Female LFPR (%)"),
            y=alt.Y("Average Childcare Cost:Q", title="Average Childcare Cost"),
            color=alt.Color("County Type:N",    title="County Type"),
        )
    )

    return (heat + lines).resolve_scale(x="shared", y="shared").properties(
        title="Childcare Cost vs Female LFPR (Density + Urban/Rural Trend Lines)"
    )


# Both heatmap plots stacked vertically

def make_heatmap_stacked(county_avg: pd.DataFrame) -> alt.VConcatChart:
    """
   Stacks the previous two heatmap graphs vertically
    """
    return alt.vconcat(
        make_heatmap_poverty(county_avg).properties(
            title="Childcare Cost vs Poverty (Density + Trend Lines)"
        ),
        make_heatmap_lfpr(county_avg).properties(
            title="Childcare Cost vs Female LFPR (Density + Trend Lines)"
        ),
        spacing=18,
    )

# Interactive county-level dashboard for urban vs rural, labor force participation, and poverty rate over time

def make_county_dashboard(geo_merged: gpd.GeoDataFrame) -> alt.HConcatChart:
    """
    Interactive three-panel dashboard driven by a year slider and a
    Urban/Rural state-group selector showing US county choropleth coloured by childcare cost (mcsa),
    can click a state to highlight it in the right panels, a scatter plot (childcare cost vs poverty rate)
    coloured by state, filtered to the clicked state and bar chart 
    comparing selected-county vs state-average female LFPR, filtered to the clicked state.
    """
    alt.data_transformers.disable_max_rows()

    years = sorted(geo_merged["study_year"].unique())

    # hared params
    year_param = alt.param(
        value=min(years),
        bind=alt.binding_range(min=min(years), max=max(years), step=1, name="Year: "),
    )
    group_param = alt.param(
        value="Rural",
        bind=alt.binding_select(options=["Rural", "Urban"], name="State group: "),
    )
    state_select  = alt.selection_point(fields=["state_name"])
    county_select = alt.selection_point(fields=["county_fips_code"])

    gdf_base = geo_merged[["geometry", "county_fips_code"]].drop_duplicates(
        subset="county_fips_code"
    ).copy()

    us_basemap = (
        alt.Chart(gdf_base)
        .mark_geoshape(fill="#E0E0E0", stroke="white", strokeWidth=0.3)
        .project(type="albersUsa")
    )

    colored_states = (
        alt.Chart(geo_merged)
        .mark_geoshape(stroke="#333333", strokeWidth=0.4)
        .transform_filter(alt.datum.state_group == group_param)
        .transform_filter(alt.datum.study_year  == year_param)
        .encode(
            color=alt.Color(
                "mcsa:Q",
                title="Childcare cost",
                scale=alt.Scale(scheme="viridis", reverse=True),
            ),
            opacity=alt.condition(state_select, alt.value(1.0), alt.value(0.8)),
            tooltip=[
                alt.Tooltip("state_name:N", title="State"),
                alt.Tooltip("county_name:N", title="County"),
                alt.Tooltip("mcsa:Q", title="Childcare cost", format=",.0f"),
                alt.Tooltip("pr_p:Q", title="Poverty rate",   format=".1f"),
                alt.Tooltip("flfpr_20to64:Q", title="Female LFPR",   format=".1f"),
            ],
        )
        .add_params(year_param, group_param, state_select)
        .project(type="albersUsa")
    )

    map_chart = (
        alt.layer(us_basemap, colored_states)
        .properties(width=850, height=650)
    )

    # Scatterplot of cost vs poverty, filtered to clicked state
    scatter = (
        alt.Chart(geo_merged)
        .mark_circle(size=70)
        .transform_filter(alt.datum.state_group == group_param)
        .transform_filter(alt.datum.study_year  == year_param)
        .transform_filter(state_select)
        .encode(
            x=alt.X("mcsa:Q",  title="Childcare cost"),
            y=alt.Y("pr_p:Q",  title="Poverty rate"),
            color=alt.Color("state_name:N"),
            opacity=alt.condition(county_select, alt.value(1.0), alt.value(0.6)),
            tooltip=[
                alt.Tooltip("state_name:N",  title="State"),
                alt.Tooltip("county_name:N", title="County"),
                alt.Tooltip("mcsa:Q",        title="Childcare cost", format=",.0f"),
                alt.Tooltip("pr_p:Q",        title="Poverty rate",   format=".1f"),
            ],
        )
        .add_params(county_select)
        .properties(width=350, height=300)
    )

    # LFPR bars for selected county vs state average
    lfpr_base = (
        alt.Chart(geo_merged)
        .transform_filter(alt.datum.state_group == group_param)
        .transform_filter(alt.datum.study_year  == year_param)
        .transform_filter(state_select)
    )

    county_bar = (
        lfpr_base
        .transform_filter(county_select)
        .transform_calculate(label='"Selected county"')
        .mark_bar()
        .encode(
            x=alt.X("label:N", title=""),
            y=alt.Y("flfpr_20to64:Q", title="Female LFPR (20–64)"),
        )
    )

    state_bar = (
        lfpr_base
        .transform_aggregate(state_avg="mean(flfpr_20to64)", groupby=["state_name"])
        .transform_calculate(label='"State average"')
        .mark_bar(color="orange")
        .encode(
            x=alt.X("label:N", title=""),
            y=alt.Y("state_avg:Q", title="Female LFPR (20–64)"),
        )
    )

    lfpr_chart = (county_bar + state_bar).properties(width=350, height=200)

    return (
        alt.hconcat(map_chart, alt.vconcat(scatter, lfpr_chart))
        .resolve_scale(color="shared")
    )
