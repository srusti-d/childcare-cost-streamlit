import altair as alt
import pandas as pd

def base_theme():
    return {
        "config": {
            "view": {"stroke": None},
            "axis": {"labelFontSize": 12, "titleFontSize": 14},
            "legend": {"labelFontSize": 12, "titleFontSize": 14},
        }
    }

def chart_hook_temp_over_time(df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("temp_max:Q", title="Daily max temp (°C)"),
            tooltip=[alt.Tooltip("date:T"), alt.Tooltip("temp_max:Q", format=".1f")],
        )
        .properties(height=320)
    )

def chart_context_seasonality(df: pd.DataFrame) -> alt.Chart:
    month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return (
        alt.Chart(df)
        .mark_boxplot()
        .encode(
            x=alt.X("month_name:N", title="Month", sort=month_order),
            y=alt.Y("temp_max:Q", title="Daily max temp (°C)"),
        )
        .properties(height=320)
    )

def chart_surprise_extremes(df: pd.DataFrame) -> alt.Chart:
    q = float(df["temp_max"].quantile(0.99))
    df2 = df.copy()
    df2["extreme"] = df2["temp_max"] >= q

    base = (
        alt.Chart(df2)
        .mark_point(filled=True, size=35)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("temp_max:Q", title="Daily max temp (°C)"),
            color=alt.condition("datum.extreme", alt.value("red"), alt.value("lightgray")),
            tooltip=[alt.Tooltip("date:T"), alt.Tooltip("temp_max:Q", format=".1f")],
        )
        .properties(height=320)
    )

    rule = alt.Chart(pd.DataFrame({"q": [q]})).mark_rule(strokeDash=[6, 4]).encode(y="q:Q")
    return base + rule

def chart_explain_precip_vs_temp(df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_point(opacity=0.45)
        .encode(
            x=alt.X("precipitation:Q", title="Precipitation (in)"),
            y=alt.Y("temp_max:Q", title="Daily max temp (°C)"),
            tooltip=[
                "date:T",
                alt.Tooltip("precipitation:Q", format=".2f"),
                alt.Tooltip("temp_max:Q", format=".1f"),
            ],
        )
        .properties(height=320)
    )

def chart_dashboard(df: pd.DataFrame) -> alt.Chart:
    weather_types = sorted(df["weather"].unique())

    w_select = alt.selection_point(
        fields=["weather"],
        bind=alt.binding_select(options=weather_types, name="Weather: "),
    )
    brush = alt.selection_interval(encodings=["x"], name="Time window")

    line = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("temp_max:Q", title="Daily max temp (°C)"),
            color=alt.Color("weather:N", title="Weather"),
            tooltip=["date:T", "weather:N", alt.Tooltip("temp_max:Q", format=".1f")],
        )
        .add_params(w_select, brush)
        .transform_filter(w_select)
        .properties(height=260)
    )

    hist = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("temp_max:Q", bin=alt.Bin(maxbins=30), title="Daily max temp (°C)"),
            y=alt.Y("count():Q", title="Days"),
            tooltip=[alt.Tooltip("count():Q", title="Days")],
        )
        .transform_filter(w_select)
        .transform_filter(brush)
        .properties(height=260)
    )

    return alt.vconcat(line, hist).resolve_scale(color="independent")

# Exercise 7: create static visualization 

def chart_bar_temp_diff(df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("weather:N", title="Weather Type"),
            y=alt.Y("mean(temp_diff):Q", title="Average Temperature (°C) Difference (Max - Min) Recorded across Days"),
            color=alt.Color("weather:N", legend=None),
        )
        .properties(width=300, height=400, title="Daily Temperature Difference (°C) by Weather Type")
    )

# Exercise 7: create interactive visualization
def chart_temp_diff_wind(df: pd.DataFrame) -> alt.Chart:
    weathers = df["weather"].unique()
    time_brush = alt.selection_interval(encodings=['x'])
    selectWeather = alt.selection_point(
        fields=['weather'],
        bind=alt.binding_radio(options=weathers, name="Select Weather: "),
        value='sun'
    )

    temp_diff_chart = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("temp_diff:Q", title="Daily Temperature Difference (Max - Min)"),
        )
        .add_params(selectWeather, time_brush)
        .transform_filter(selectWeather)
        .properties(title="Daily Temperature Difference (°C) by Weather Type", width=400, height=300)
    )

    wind_plot = (
        alt.Chart(df)
        .mark_circle(size=60)
        .encode(
            x=alt.X('wind:Q', title='Wind Speed'),
            y=alt.Y('precipitation:Q', title='Precipitation Level'),
            color=alt.condition(time_brush, alt.value('green'), alt.value('steelblue'), legend=None),
            opacity=alt.condition(time_brush, alt.value(1), alt.value(0.25)),
            tooltip=[
                alt.Tooltip('wind', title='Wind Speed'),
                alt.Tooltip('precipitation', title='Precipitation Level'),
            ]
        )
        .transform_filter(time_brush)
        .properties(width=400, height=400, title="Wind Speed vs Precipitation for Each Day")
    )

    return temp_diff_chart | wind_plot


