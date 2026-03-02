import altair as alt
import pandas as pd
from utils.io import MONTH_ORDER

def base_theme():
    return {
        "config": {
            "view": {"stroke": None},
            "axis": {"labelFontSize": 12, "titleFontSize": 14},
            "legend": {"labelFontSize": 12, "titleFontSize": 14},
        }
    }

def chart_home_away_wins(both_szns_df: pd.DataFrame) -> alt.Chart:
    seasons = list(both_szns_df["Season"].unique())
    teams = list(both_szns_df["HomeTeam"].unique())

    selectSeason = alt.selection_point(
        fields=['Season'],
        bind=alt.binding_radio(options=seasons, name="Select Season: "),
        value='2023-24'
    )
    selectTeam = alt.selection_point(
        fields=['TargetTeam'],
        bind=alt.binding_select(options=teams, name="Select Team: "),
        value='Arsenal'
    )

    home_chart = alt.Chart(both_szns_df).transform_calculate(
        TargetTeam=alt.datum.HomeTeam
    ).mark_line(point=True).encode(
        x=alt.X("Month_Name:O", title="Month of Season", sort=MONTH_ORDER),
        y=alt.Y("HomeWinCount:Q", title="Cumulative # of Home Game Wins"),
        color=alt.Color("HomeTeam:N", scale=alt.Scale(scheme='category20'), legend=None),
        opacity=alt.condition(selectTeam, alt.value(0.75), alt.value(0.05))
    ).add_params(selectSeason, selectTeam).transform_filter(selectSeason).properties(
        title="Team Performance in Home Games", width=400, height=300
    )

    away_chart = alt.Chart(both_szns_df).transform_calculate(
        TargetTeam=alt.datum.AwayTeam
    ).mark_line(point=True).encode(
        x=alt.X("Month_Name:O", title="Month of Season", sort=MONTH_ORDER),
        y=alt.Y("AwayWinCount:Q", title="Cumulative # of Away Game Wins"),
        color=alt.Color("AwayTeam:N", scale=alt.Scale(scheme='category20'), legend=None),
        opacity=alt.condition(selectTeam, alt.value(0.75), alt.value(0.05))
    ).add_params(selectSeason, selectTeam).transform_filter(selectSeason).properties(
        title="Team Performance in Away Games", width=400, height=300
    )

    return alt.hconcat(home_chart, away_chart).properties(
        title="How does Team Performance Vary in Home and Away Games by Season?"
    ).configure_title(fontSize=15)


def chart_red_cards_wins(teams_rcards_df: pd.DataFrame, teams_wins_df: pd.DataFrame) -> alt.Chart:
    brush = alt.selection_interval(encodings=['x'])

    bar_chart = alt.Chart(teams_rcards_df).mark_bar().add_params(brush).encode(
        alt.X('team:N', title='Team', sort='-y'),
        alt.Y('red_cards:Q', title='# of Cumulative Red Cards'),
        alt.Color('red_cards:Q', scale=alt.Scale(scheme='reds'), legend=None)
    ).properties(width=500, height=300, title="Total Number of Red Cards by Team")

    line_chart = alt.Chart(teams_wins_df).mark_line(point=True).encode(
        x=alt.X("Month_Name:O", title="Month of Season", sort=MONTH_ORDER),
        y=alt.Y("TotalWinCount:Q", title="Cumulative Wins (Home & Away)"),
        color=alt.Color("team:N", scale=alt.Scale(scheme='category20'), legend=None),
        opacity=alt.condition(brush, alt.value(1), alt.value(0.10)),
        tooltip=[
            alt.Tooltip('team', title='Team'),
            alt.Tooltip('TotalWinCount', title='Total Wins in Season So Far')
        ]
    ).properties(title="Team Wins Throughout Season", width=500, height=400)

    return alt.hconcat(bar_chart, line_chart).properties(
        spacing=5,
        title="Is there a relationship between red cards and performance in the 2024-25 season?"
    ).configure_title(fontSize=16)


def chart_referee_penalties(szn_2425_df: pd.DataFrame, melted_df: pd.DataFrame) -> alt.Chart:
    ref_brush = alt.selection_interval(encodings=['y'])
    point_select = alt.selection_point(fields=['match_id'], empty='none')
    max_count = int(szn_2425_df[['HF', 'AF', 'HY', 'AY', 'HR', 'AR']].max().max())

    ref_chart = alt.Chart(szn_2425_df).mark_bar().encode(
        x=alt.X('mean(total_penalties):Q', title='Average Penalties Given (Cards + Fouls)'),
        y=alt.Y('Referee:N', sort='-x'),
        color=alt.condition(
            ref_brush,
            alt.value('orange'),
            alt.Color('mean(total_penalties):Q', legend=None)
        ),
        opacity=alt.condition(ref_brush, alt.value(1.0), alt.value(0.5))
    ).add_params(ref_brush).properties(width=250, height = 350, title="EPL Referees Penalties Ranking (2024-25)")

    match_plot = alt.Chart(szn_2425_df).mark_circle(size=60).encode(
        x=alt.X('total_fouls:Q', title='# of Fouls'),
        y=alt.Y('total_cards:Q', title='# of Cards'),
        color=alt.condition(point_select, alt.value('orange'), alt.value('steelblue')),
        tooltip=[
            alt.Tooltip('HomeTeam', title='Home Team'),
            alt.Tooltip('AwayTeam', title='Away Team'),
            alt.Tooltip('Referee')
        ]
    ).add_params(point_select).transform_filter(ref_brush).properties(
        width=250, height=400, title="Fouls and Cards at Match-Level"
    )

    penalty_plot = alt.Chart(melted_df).transform_filter(point_select).mark_bar().encode(
        x=alt.X('Category:N', sort=['Foul', 'Yellow Card', 'Red Card'], title="Type of Penalty"),
        xOffset=alt.XOffset('Team:N', sort=['Home Team', 'Away Team']),
        y=alt.Y('Count:Q', title='Count',
                scale=alt.Scale(domain=[0, max_count]),
                axis=alt.Axis(tickMinStep=1, format='d')),
        color=alt.Color('Team:N',
                        sort=['Home Team', 'Away Team'],
                        scale=alt.Scale(domain=['Home Team', 'Away Team'], range=['blue', 'red']),
                        legend=alt.Legend(title='Team'))
    ).properties(width=250, height=400, title='Selected Match Penalty Breakdown')
    return ref_chart, match_plot, penalty_plot
    #return (ref_chart | match_plot | penalty_plot).resolve_scale(x='independent')