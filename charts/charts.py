import altair as alt
import pandas as pd
import geopandas as gpd
alt.data_transformers.disable_max_rows()
from utils.data_io import normalize_features_to_unit_box
import json

def base_theme():
    return {
        "config": {
            "view": {"stroke": None},
            "axis": {"labelFontSize": 12, "titleFontSize": 14},
            "legend": {"labelFontSize": 12, "titleFontSize": 14},
        }
    }

def make_cost_trend_line(cost_trend: pd.DataFrame) -> alt.LayerChart:
    """
    Line chart of average national childcare cost (mcsa) over time.
    """
    line = (
        alt.Chart(cost_trend)
        .mark_line(point=alt.OverlayMarkDef(filled=True, size=60), color="steelblue")
        .encode(
            x=alt.X(
                "study_year:Q",
                title="Year",
                axis=alt.Axis(format="d", tickCount=int(cost_trend["study_year"].nunique())),
            ),
            y=alt.Y(
                "mcsa:Q",
                title="Average Weekly Childcare Cost ($)",
                scale=alt.Scale(
                    zero=False,
                    domain=[
                        float(cost_trend["mcsa"].min()) * 0.95,
                        float(cost_trend["mcsa"].max()) * 1.05,
                    ],
                ),
            ),
            tooltip=[
                alt.Tooltip("study_year:Q", title="Year"),
                alt.Tooltip("mcsa:Q", title="Avg Childcare Cost", format=".2f"),
            ],
        )
    )

    return line.properties(
        width=680, height=380,
        title="Average National Childcare Cost Trend (2008-2018)",
    )


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
    geo_features: list,
    state_metrics: pd.DataFrame,
    geojson_url: str | None = None,
) -> alt.VConcatChart:

    # Correct GeoJSON input
    if geojson_url is not None:
        geo_data = alt.UrlData(
            url=geojson_url,
            format=alt.DataFormat(property="features", type="json")
        )
    else:
        geo_data = alt.Data(values=geo_features)

    years = sorted(state_metrics["study_year"].unique())

    # Slider parameter
    year_slider = alt.binding_range(
        min=int(min(years)),
        max=int(max(years)),
        step=1,
        name="Year: "
    )

    year_selection = alt.param(
        name="selected_year",
        value=int(min(years)),
        bind=year_slider
    )

    # Correct filter expression
    year_filter = "datum.properties.study_year == selected_year"

    # Base map (correct geoshape usage)
    base_map = (
        alt.Chart(geo_data)
        .mark_geoshape(stroke="white", strokeWidth=0.5)
        .transform_filter(year_filter)
        .project("albersUsa")
        .properties(width=450, height=280)
    )

    # Childcare cost map
    childcare_chart = base_map.encode(
        color=alt.Color(
            "properties.mcsa_mean:Q",
            scale=alt.Scale(
                scheme="blues",
                domain=[
                    float(state_metrics["mcsa_mean"].min()),
                    float(state_metrics["mcsa_mean"].max()),
                ],
            ),
            title="Average Weekly Childcare Cost",
        ),
        tooltip=[
            alt.Tooltip("properties.state_name:N", title="State"),
            alt.Tooltip("properties.mcsa_mean:Q", title="Avg Weekly Childcare Cost", format=".2f"),
            alt.Tooltip("properties.study_year:Q", title="Year"),
        ],
    ).properties(
        title="Average weekly center-based childcare cost"
    )

    # Poverty rate map
    poverty_chart = base_map.encode(
        color=alt.Color(
            "properties.pr_f_mean:Q",
            scale=alt.Scale(
                scheme="oranges",
                domain=[
                    float(state_metrics["pr_f_mean"].min()),
                    float(state_metrics["pr_f_mean"].max()),
                ],
            ),
            title="Average Poverty Rate",
        ),
        tooltip=[
            alt.Tooltip("properties.state_name:N", title="State"),
            alt.Tooltip("properties.pr_f_mean:Q", title="Average Poverty Rate", format=".2f"),
            alt.Tooltip("properties.study_year:Q", title="Year"),
        ],
    ).properties(
        title="Average poverty rate for families"
    )

    # Female LFPR map
    labor_chart = base_map.encode(
        color=alt.Color(
            "properties.flfpr_20to64_mean:Q",
            scale=alt.Scale(
                scheme="purples",
                domain=[
                    float(state_metrics["flfpr_20to64_mean"].min()),
                    float(state_metrics["flfpr_20to64_mean"].max()),
                ],
            ),
            title="Female LFPR (20–64)",
        ),
        tooltip=[
            alt.Tooltip("properties.state_name:N", title="State"),
            alt.Tooltip("properties.flfpr_20to64_mean:Q", title="Female LFPR", format=".2f"),
            alt.Tooltip("properties.study_year:Q", title="Year"),
        ],
    ).properties(
        title="Female labor-force participation (20–64)"
    )

    bottom_row = alt.hconcat(labor_chart, poverty_chart).resolve_scale(color="independent")

    final_chart = (
        alt.vconcat(childcare_chart, bottom_row)
        .add_params(year_selection)
        .resolve_scale(color="independent")
        .properties(
            title="Childcare Cost and Socioeconomic Metrics Across U.S. States (2008–2018)"
        )
    )

    return final_chart


# Urban/rural state county maps in an 8-state panel

def make_urban_rural_state_maps(
    county_avg:       pd.DataFrame,
    geo_counties_raw: dict,
    sample_states:    list | None = None,
    geojson_url:      str | None = None,
) -> alt.VConcatChart:
    """
    Panel of county maps coloured by urban/rural classification.
    """
    if sample_states is None:
        sample_states = [
            "North Dakota", "Kansas", "Oklahoma", "Vermont", # rural
            "Massachusetts", "California", "Arizona", "Delaware", # urban
        ]

    COST, WLF, POV = "mcsa", "flfpr_20to64", "pr_p"
    county_avg_8 = county_avg[county_avg["state_name"].isin(sample_states)].copy()

    charts_list = []
    for i, st in enumerate(sample_states):
        state_df = county_avg_8[county_avg_8["state_name"] == st].copy()
        fips_set = set(state_df["county_fips_code"].tolist())

        if geojson_url is not None:
            geo_source = alt.UrlData(
                url=geojson_url,
                format=alt.DataFormat(property="features", type="json")
            )
        else:
            feats      = [ft for ft in geo_counties_raw["features"] if ft["properties"]["fips5"] in fips_set]
            feats_norm = normalize_features_to_unit_box(feats, pad=0.02)
            geo_source = alt.Data(values=feats_norm)

        ch = (
            alt.Chart(geo_source)
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
                    scale=alt.Scale(
                        domain=["Urban", "Rural"],
                        range=["#4e79a7", "#f28e2b"]
                    ),
                    legend=alt.Legend(title="County type") if i == 0 else None,
                    title="County type",
                ),
                tooltip=[
                    alt.Tooltip("state_name:N", title="State"),
                    alt.Tooltip("properties.NAME:N", title="County"),
                    alt.Tooltip("urbanicity_rucc:N", title="Urban/Rural"),
                    alt.Tooltip(f"{COST}:Q", title="Avg childcare cost", format=",.2f"),
                    alt.Tooltip(f"{WLF}:Q",  title="Female Labor Force Participation Rate (FLFPR)", format=",.2f"),
                    alt.Tooltip(f"{POV}:Q",  title="Poverty rate", format=",.2f"),
                ],
            )
            .properties(
                title=alt.TitleParams(text=st, anchor="middle"),
                width=300, height=240,
            )
        )
        charts_list.append(ch)

    row1 = alt.hconcat(*charts_list[:4], spacing=10)
    row2 = alt.hconcat(*charts_list[4:], spacing=10)
    return (
        alt.vconcat(row1, row2, spacing=14)
        .configure_view(stroke=None)
        .properties(title={
            "text": "Urban vs Rural County Comparison",
            "subtitle": "8 state sample with full data coverage",
        })
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
            y=alt.Y("Average Childcare Cost:Q", bin=alt.Bin(maxbins=30), title="Average Weekly Childcare Cost"),
            color=alt.Color("count():Q", scale=alt.Scale(scheme="greens"), title="# of Counties"),
            tooltip=[alt.Tooltip("count():Q", title="# of Counties")],
        )
    )

    lines = (
        alt.Chart(df)
        .transform_regression("Poverty Rate (%)", "Average Childcare Cost", groupby=["County Type"])
        .mark_line(size=3)
        .encode(
            x=alt.X("Poverty Rate (%):Q", title="Poverty Rate (%)"),
            y=alt.Y("Average Childcare Cost:Q", title="Average Weekly Childcare Cost"),
            color=alt.Color("County Type:N", scale=alt.Scale(domain=["Urban", "Rural"], range=["#4e79a7", "#f28e2b"]), title="County Type"),
        )
    )

    return (alt.layer(heat, lines).resolve_scale(color="independent")).properties(
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
            x=alt.X("Female LFPR (%):Q", bin=alt.Bin(maxbins=30), title="Female Labor Force Participation Rate (%)"),
            y=alt.Y("Average Childcare Cost:Q", bin=alt.Bin(maxbins=30), title="Average Weekly Childcare Cost"),
            color=alt.Color("count():Q", scale=alt.Scale(scheme="purples"), title="# of Counties"),
            tooltip=[alt.Tooltip("count():Q", title="# of Counties")],
        )
    )

    lines = (
        alt.Chart(df)
        .transform_regression("Female LFPR (%)", "Average Childcare Cost", groupby=["County Type"])
        .mark_line(size=3)
        .encode(
            x=alt.X("Female LFPR (%):Q", title="Female Labor Force Participation Rate (%)"),
            y=alt.Y("Average Childcare Cost:Q", title="Average Weekly Childcare Cost"),
            color=alt.Color("County Type:N", scale=alt.Scale(domain=["Urban", "Rural"], range=["#4e79a7", "#f28e2b"]), title="County Type"),
        )
    )

    return (alt.layer(heat, lines).resolve_scale(color="independent")).properties(
        title="Childcare Cost vs Female Labor Force Participation Rate (Density + Urban/Rural Trend Lines)"
    )


# Both heatmap plots stacked vertically

def make_heatmap_stacked(county_avg: pd.DataFrame) -> alt.VConcatChart:
    """
   Stacks the previous two heatmap graphs vertically
    """
    return alt.vconcat(
        make_heatmap_poverty(county_avg).properties(
            title="Childcare Cost vs Poverty Rate"
        ),
        make_heatmap_lfpr(county_avg).properties(
            title="Childcare Cost vs Female Labor Force Participation Rate"
        ),
        spacing=18,
    )

# Interactive county-level dashboard for urban vs rural, labor force participation, and poverty rate over time


def make_county_dashboard(geo_merged):

    alt.data_transformers.disable_max_rows()

    if hasattr(geo_merged, "to_json"):
        geo_merged_json = json.loads(geo_merged.to_json())
    else:
        geo_merged_json = geo_merged

    geo_features = geo_merged_json["features"]

    # Extract years and states
    years = sorted({
        f["properties"]["study_year"]
        for f in geo_features
        if f["properties"].get("study_year") is not None
    })

    state_names = sorted({
        f["properties"]["state_name"]
        for f in geo_features
        if f["properties"].get("state_name") is not None
    })

    # DataFrame for scatter + bar panels
    df_panel = pd.DataFrame([f["properties"] for f in geo_features])

    year_param = alt.param(
        name="year_param",
        value=min(years),
        bind=alt.binding_range(
            min=min(years),
            max=max(years),
            step=1,
            name="Year: "
        ),
    )

    state_param = alt.param(
        name="state_param",
        value=state_names[0],
        bind=alt.binding_select(
            options=state_names,
            name="State: "
        ),
    )

    county_select = alt.selection_point(fields=["county_fips_code"])

    # County map
    state_map = (
        alt.Chart(alt.Data(values=geo_features))
        .mark_geoshape(stroke="#333333", strokeWidth=0.4)
        .transform_filter("datum.properties.state_name === state_param")
        .transform_filter("datum.properties.study_year === year_param")
        .transform_calculate(
            county_fips_code="datum.properties.county_fips_code",
            county_name="datum.properties.county_name",
            state_name="datum.properties.state_name",
            mcsa="datum.properties.mcsa",
            pr_p="datum.properties.pr_p",
            flfpr_20to64="datum.properties.flfpr_20to64"
        )
        .encode(
            color=alt.Color(
                "mcsa:Q",
                title="Childcare cost",
                scale=alt.Scale(scheme="blues", reverse=True),
            ),
            opacity=alt.condition(county_select, alt.value(1.0), alt.value(0.5)),
            tooltip=[
                alt.Tooltip("state_name:N", title="State"),
                alt.Tooltip("county_name:N", title="County"),
                alt.Tooltip("mcsa:Q", title="Avg weekly childcare cost", format=",.0f"),
                alt.Tooltip("pr_p:Q", title="Poverty rate", format=".1f"),
                alt.Tooltip("flfpr_20to64:Q", title="Female LFPR", format=".1f"),
            ],
        )
        .add_params(county_select)
        .project(type="albersUsa")
        .properties(
            width=400, height=500,
            title=alt.TitleParams(text="County Childcare Cost by State", anchor="middle"),
        )
    )

    # Scatter plot
    scatter = (
        alt.Chart(df_panel)
        .mark_circle(size=70)
        .transform_filter(alt.datum.state_name == state_param)
        .transform_filter(alt.datum.study_year == year_param)
        .encode(
            x=alt.X("mcsa:Q", title="Avg weekly childcare cost"),
            y=alt.Y("pr_p:Q", title="Poverty rate"),
            opacity=alt.condition(county_select, alt.value(1.0), alt.value(0.6)),
            tooltip=[
                alt.Tooltip("state_name:N", title="State"),
                alt.Tooltip("county_name:N", title="County"),
                alt.Tooltip("mcsa:Q", format=",.0f"),
                alt.Tooltip("pr_p:Q", format=".1f"),
            ],
        )
        .add_params(county_select)
        .properties(
            width=350, height=300,
            title=alt.TitleParams(text="Childcare Cost vs. Poverty Rate (County-Level)", anchor="middle"),
        )
    )

    # Base filtered data for LFPR chart
    lfpr_base = (
        alt.Chart(df_panel)
        .transform_filter(alt.datum.state_name == state_param)
        .transform_filter(alt.datum.study_year == year_param)
    )

    # Selected county bar
    county_bar = (
        lfpr_base
        .transform_filter(county_select)
        .transform_calculate(label='"Selected county"')
        .mark_bar()
        .encode(
            x=alt.X("label:N", title=""),
            y=alt.Y(
                "flfpr_20to64:Q",
                title="Female LFPR (20–64)"
            ),
        )
    )

    # State average bar
    state_bar = (
        lfpr_base
        .transform_aggregate(
            state_avg="mean(flfpr_20to64)",
            groupby=["state_name"]
        )
        .transform_calculate(label='"State average"')
        .mark_bar(color="orange")
        .encode(
            x=alt.X("label:N", title=""),
            y=alt.Y("state_avg:Q"),
        )
    )

    lfpr_chart = (
        county_bar + state_bar
    ).properties(
        width=350, height=200,
        title=alt.TitleParams(
            text="Female Labor Force Participation Rate: County vs State Average",
            anchor="middle",
        ),
    )

    dashboard = (
        alt.hconcat(
            state_map,
            alt.vconcat(scatter, lfpr_chart)
        )
        .add_params(year_param, state_param)
        .resolve_scale(color="shared")
        .configure_title(fontSize=14, anchor="middle")
    )

    return dashboard