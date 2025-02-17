import streamlit as st
import pandas as pd
from datetime import datetime
import time
import boto3
import io
import os

# local packages
import sys
from dotenv import load_dotenv

sys.path.append("App")
# from scraper import run_scraper
# from compare_two_teams import compare_teams

os.makedirs("./results", exist_ok=True)

load_dotenv()

SEND_EMAIL = False
SEND_SLACK = False

# Add these near the top of your file
AWS_ACCESS_KEY_ID = os.getenv("PERSONAL_AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("PERSONAL_AWS_SECRET_ACCESS_KEY")
AWS_REGION = "us-east-1"  # or your preferred region
BUCKET_NAME = "college-basketball"  # your bucket name


def load_data_from_s3(date_str):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )

    try:
        # Check if file exists first
        try:
            s3.head_object(Bucket=BUCKET_NAME, Key=f"ScoutingReports/{date_str}.xlsx")
        except s3.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                st.warning(
                    f"No data available for {date_str}. The scraper may not have run yet."
                )
                return None, False, None
            else:
                raise

        # Load Excel file from S3
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=f"ScoutingReports/{date_str}.xlsx")

        # Read Excel file into pandas DataFrames
        excel_data = pd.read_excel(
            io.BytesIO(obj["Body"].read()), sheet_name=["Summary", "Raw Data"]
        )

        summary = excel_data["Summary"]
        df = excel_data["Raw Data"]

        return df, True, summary

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, False, None


# Streamlit UI
def main():
    st.set_page_config(layout="wide", page_title="Kenpom Data Viewer")

    # Create tabs
    tab1, tab2, tab3 = st.tabs(
        ["Today's Games", "Custom Game Scraper", "Team Comparison"]
    )

    with tab1:
        st.title("Today's Games")

        # Get today's date
        today = datetime.today()
        today_str = today.strftime("%Y-%m-%d")

        try:
            # Load today's data from S3
            df, success, summary = load_data_from_s3(today_str)

            if success:
                # Format the summary DataFrame
                formatted_summary = summary.copy()
                formatted_summary = formatted_summary.round(2)
                formatted_summary["WinProbability"] = formatted_summary[
                    "WinProbability"
                ].apply(
                    lambda x: (f"{float(x):.1%}" if isinstance(x, (int, float)) else x)
                )

                # Sort by Time (ET)
                formatted_summary = formatted_summary.sort_values("Time (ET)")

                # Apply color styling
                def color_delta(val):
                    if pd.isna(val):  # Handle NaN values
                        return ""
                    color = (
                        "#ffcdd2" if val < 0 else "#c8e6c9"
                    )  # Light red / Light green
                    return f"background-color: {color}"

                styled_df = formatted_summary.style.applymap(
                    color_delta, subset=["TeamA (Delta)", "TeamB (Delta)"]
                ).format(
                    {
                        "TeamA (Delta)": "{:+.1f}",  # Add plus sign for positive values
                        "TeamB (Delta)": "{:+.1f}",
                    }
                )

                # Display all rows
                st.dataframe(
                    styled_df,
                    hide_index=True,
                    use_container_width=True,
                    height=800,  # Increase height to show more rows
                    column_config={
                        "Time (ET)": st.column_config.TextColumn(
                            "Time (ET)", width="small"
                        ),
                        "PredictedScore": st.column_config.TextColumn(
                            "Predicted Score", width="small"
                        ),
                        "WinProbability": st.column_config.TextColumn(
                            "Win Prob", width="small"
                        ),
                        "Team A (Eff)": st.column_config.NumberColumn(
                            "Team A Eff", format="%.1f"
                        ),
                        "Team A (Shoot)": st.column_config.NumberColumn(
                            "Team A Shoot", format="%.1f"
                        ),
                        "TeamA (Delta)": st.column_config.NumberColumn(
                            "Team A Δ", format="%.1f"
                        ),
                        "Team B (Eff)": st.column_config.NumberColumn(
                            "Team B Eff", format="%.1f"
                        ),
                        "Team B (Shoot)": st.column_config.NumberColumn(
                            "Team B Shoot", format="%.1f"
                        ),
                        "TeamB (Delta)": st.column_config.NumberColumn(
                            "Team B Δ", format="%.1f"
                        ),
                    },
                )
            else:
                st.error(f"No data available for today ({today_str})")
        except Exception as e:
            st.error(f"Error loading today's data: {str(e)}")

    with tab2:
        st.title("Custom Game Scraper")  # Updated title

        # # Rest of your existing Games Scraper code
        # # Dropdown menu for user selection
        # user = st.selectbox("Select User", ["Hari", "Nadav", "Wes", "Matt", "Victor"])

        # # Date selection menu
        # selected_date = st.date_input("Select a date", datetime.today())
        # selected_date_str = selected_date.strftime("%Y-%m-%d")

        # # Displaying the email box
        # email = f"{user.lower()}@writewise.com"
        # if user == "Wes":
        #     email = "wvsundram@gmail.com"

        # st.write(f"Results will be sent to {email}")

        # # Console output management
        # if "console_lines" not in st.session_state:
        #     st.session_state.console_lines = []

        # # Function to handle console output in Streamlit
        # def console_output(text):
        #     st.session_state.console_lines.append(text)
        #     st.session_state.console_lines = st.session_state.console_lines[-1:]
        #     console_text = "\n".join(st.session_state.console_lines)
        #     console.text_area("Console Output", console_text, height=200)

        # console = st.empty()

        # if st.button("Run Scraper"):
        #     with st.spinner("Running scraper..."):
        #         df, sent_success, summary = run_scraper(
        #             selected_date_str,
        #             console_output,
        #             email,
        #             send_email=SEND_EMAIL,
        #             send_slack=SEND_SLACK,
        #         )
        #         if sent_success:
        #             st.success(
        #                 "The results were sent by email. It may take a few minutes to arrive..."
        #             )

        #             st.subheader(f"Games for {selected_date_str}")

        #             # Format the summary DataFrame
        #             formatted_summary = summary.copy()
        #             formatted_summary = formatted_summary.round(2)
        #             formatted_summary["WinProbability"] = formatted_summary[
        #                 "WinProbability"
        #             ].apply(
        #                 lambda x: (
        #                     f"{float(x):.1%}" if isinstance(x, (int, float)) else x
        #                 )
        #             )

        #             # Sort by Time (ET)
        #             formatted_summary = formatted_summary.sort_values("Time (ET)")

        #             # Apply color styling
        #             def color_delta(val):
        #                 if pd.isna(val):  # Handle NaN values
        #                     return ""
        #                 color = (
        #                     "#ffcdd2" if val < 0 else "#c8e6c9"
        #                 )  # Light red / Light green
        #                 return f"background-color: {color}"

        #             styled_df = formatted_summary.style.applymap(
        #                 color_delta, subset=["TeamA (Delta)", "TeamB (Delta)"]
        #             ).format(
        #                 {
        #                     "TeamA (Delta)": "{:+.1f}",  # Add plus sign for positive values
        #                     "TeamB (Delta)": "{:+.1f}",
        #                 }
        #             )

        #             # Display all rows
        #             st.dataframe(
        #                 styled_df,
        #                 hide_index=True,
        #                 use_container_width=True,
        #                 height=800,  # Increase height to show more rows
        #                 column_config={
        #                     "Time (ET)": st.column_config.TextColumn(
        #                         "Time (ET)", width="small"
        #                     ),
        #                     "PredictedScore": st.column_config.TextColumn(
        #                         "Predicted Score", width="small"
        #                     ),
        #                     "WinProbability": st.column_config.TextColumn(
        #                         "Win Prob", width="small"
        #                     ),
        #                     "Team A (Eff)": st.column_config.NumberColumn(
        #                         "Team A Eff", format="%.1f"
        #                     ),
        #                     "Team A (Shoot)": st.column_config.NumberColumn(
        #                         "Team A Shoot", format="%.1f"
        #                     ),
        #                     "TeamA (Delta)": st.column_config.NumberColumn(
        #                         "Team A Δ", format="%.1f"
        #                     ),
        #                     "Team B (Eff)": st.column_config.NumberColumn(
        #                         "Team B Eff", format="%.1f"
        #                     ),
        #                     "Team B (Shoot)": st.column_config.NumberColumn(
        #                         "Team B Shoot", format="%.1f"
        #                     ),
        #                     "TeamB (Delta)": st.column_config.NumberColumn(
        #                         "Team B Δ", format="%.1f"
        #                     ),
        #                 },
        #             )

    with tab3:
        st.header("Compare two teams")

        # # one dropdown button for team A
        # kenpom_teams = [
        #     "Connecticut",
        #     "Houston",
        #     "Purdue",
        #     "Auburn",
        #     "Arizona",
        #     "Iowa St.",
        #     "Tennessee",
        #     "Duke",
        #     "North Carolina",
        #     "Illinois",
        #     "Creighton",
        #     "Marquette",
        #     "Alabama",
        #     "Baylor",
        #     "Gonzaga",
        #     "BYU",
        #     "Wisconsin",
        #     "Saint Mary's",
        #     "Michigan St.",
        #     "San Diego St.",
        #     "Kentucky",
        #     "New Mexico",
        #     "Kansas",
        #     "Colorado",
        #     "Texas Tech",
        #     "Texas",
        #     "Nebraska",
        #     "Florida",
        #     "Colorado St.",
        #     "Mississippi St.",
        #     "Dayton",
        #     "Nevada",
        #     "TCU",
        #     "Clemson",
        #     "Boise St.",
        #     "Florida Atlantic",
        #     "Washington St.",
        #     "Texas A&M",
        #     "Northwestern",
        #     "Utah St.",
        #     "South Carolina",
        #     "Drake",
        #     "Grand Canyon",
        #     "Oregon",
        #     "N.C. State",
        #     "James Madison",
        #     "McNeese St.",
        #     "Samford",
        #     "Yale",
        #     "Duquesne",
        #     "Charleston",
        #     "Vermont",
        #     "UAB",
        #     "Morehead St.",
        #     "Akron",
        #     "Western Kentucky",
        #     "South Dakota St.",
        #     "Oakland",
        #     "Colgate",
        #     "Longwood",
        #     "Long Beach St.",
        #     "Saint Peter's",
        #     "Montana St.",
        #     "Stetson",
        #     "Gambling St.",
        #     "Wagner",
        # ]
        # # sort alphabetically
        # kenpom_teams.sort()

        # team_a = st.selectbox("Select Team A", kenpom_teams)
        # team_b = st.selectbox("Select Team B", kenpom_teams)

        # if st.button("Compare"):
        #     with st.spinner("Comparing teams..."):
        #         df_fm = compare_teams(
        #             team_a,
        #             team_b,
        #             year=2024,
        #         )
        #         st.dataframe(
        #             df_fm.style.set_table_styles(
        #                 [{"selector": "th", "props": [("text-align", "center")]}]
        #             )
        #         )


if __name__ == "__main__":
    main()
