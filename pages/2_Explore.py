import streamlit as st
from utils.io import load_data
from charts.charts import chart_home_away_wins, chart_red_cards_wins, chart_referee_penalties


st.set_page_config(page_title="Data Story & Interactive Exploration", layout="wide")
both_szns_df, szn_2425_df, teams_rcards_df, teams_wins_df, melted_df = load_data() 

st.title("A Data Story: English Premier League Patterns")
st.markdown("**Central question:** *How do team performance, disciplinary action, and referee behaviour shape outcomes across the 2023-24 and 2024-25 seasons?*")

st.header("1) Home vs Away Performance by Season")
st.write("Switch between seasons and select a team to follow their home and away win trajectory month by month.")
st.markdown("**Guided prompts:**")
st.write("- Does your selected team perform better at home or away? Does this change between seasons?")
st.write("- Which teams show the biggest home/away performance gap?")
st.altair_chart(chart_home_away_wins(both_szns_df), use_container_width=True)
st.caption("Takeaway: Generally, there appears to be consistency in how well a team performs in both home and away games - though there are some exceptions. While most teams perform similarly in both seasons, certain teams also perform distinctly better/worse between the seasons.") 
with st.expander("Interesting caveats from the takeaway and details in the interactive plot:"):
    st.write("Not all teams maintain the same success in performance between home and away games. Select Newcastle team and the filter for the 2023-24 Season. We can see that there is a clear home advantage for Newcastle's performance in the 2023-24 season. However, this home advantage is not as prominent in the 2024-25 season. Between seasons, Arsenal has about the same level of success. However, Nott'm Forest has a much improved performance in both home and away games from the 2023-24 season to the 2024-25 season.")


st.header("2) Do Red Cards Cost Teams Wins?")
st.write("After exploring team performance across seasons and in both home/away teams, we can narrow down on exploring match-specific factors that may contribute to the pattern of wins. We examine whether teams that accumulate more red cards tend to win less over the 2024-25 season. Brush over teams in the bar chart to highlight their win trajectories.")
st.write("Brush over teams in the bar chart to highlight their win trajectory in the line chart.")
st.markdown("**Guided prompts:**")
st.write("- Do the most disciplined teams consistently win more?")
st.write("- Are there any surprising outliers — high cards but high wins, or vice versa?")
st.altair_chart(chart_red_cards_wins(teams_rcards_df, teams_wins_df), use_container_width=True)
st.caption("Takeaway: The relationship is not straightforward — some high-card teams still perform well, suggesting other factors dominate.")
with st.expander("Interesting details related to the takeaway in the interactive plot:"):
    st.write("The top two teams with the highest red card penalty count are Arsenal and Ipswich. Both have very different trajectories in the 2024-25 season. Arsenal is top 3 in the # of cumulative wins throughout the season. Ipswich is second to last in team performance in the season.")


st.header("3) Referee Strictness and Match-Level Penalties")
st.write("Now that we have explored the lack of a strong relationship between frequency of red cards and team performance across a season, we can further examine the factors that actually contribute the the frequency of red cards at a match-specific level. Here, we look at how referees differ in the penalties they award, and whether fouls and cards are more extreme in specific matches. Brush referees on the left, then click a match point to see its penalty breakdown by team within that match.")
st.write("Brush referees to filter the scatter plot by matches refereed by the selected individual, then click a match to inspect its penalty breakdown by home and away team.")
st.markdown("**Guided prompts:**")
st.write("- Which referee awards the most penalties on average?")
st.write("- Do high-foul matches always result in more cards, or does it vary by referee?")
# st.altair_chart(chart_referee_penalties(szn_2425_df, melted_df))
ref_chart, match_plot, penalty_plot = chart_referee_penalties(szn_2425_df, melted_df)
col1, col2, col3 = st.columns([1.5, 2, 1.2])
with col1:
    st.altair_chart(ref_chart)
with col2:
    st.altair_chart(match_plot)
with col3:
    st.altair_chart(penalty_plot)
st.caption("Takeaway: Certain referees consistently award more penalties. High-foul matches don't always produce high card counts. There does not appear to be a significant trend in the teams in the extreme penalty matches.")
with st.expander("Interesting details related to the takeaway in the interactive plot:"):
    st.write("Though some referees have higher average penalties (both fouls & cards), the extreme points with high fouls and cards don't have a large imbalance in which team (home versus away) are being given these penalties. Generally, there is an equal distribution of penalties between the teams for high foul + high card matches.")
