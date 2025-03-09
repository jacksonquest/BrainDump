import streamlit as st
import pandas as pd
import numpy as np
import time

from utils.helper_functions import score_mood, save_journal_entry, generate_ai_report, score_reflection_ai, \
                                    score_stress_ai, score_anxiety_ai, fetch_journal_entries, generate_wordcloud

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

if "ai_output" not in st.session_state:
    st.session_state["ai_output"] = ""  # Default value


def stream_data():
    for word in st.session_state['ai_output'].split(" "):
        yield word + " "
        time.sleep(0.02)

# Structure
st.markdown('<div style="display: flex; justify-content: center;"><h4>BrainDump</h4></div>',unsafe_allow_html=True)

with st.expander(f"Welcome {st.session_state.user_info['name']}"):
    st.write("Your Profile Info")
    st.write(f"**Name:** {st.session_state.user_info['name']}")
    st.write(f"**Username:** {st.session_state.user_info['username']}")
    st.write(f"**Date of Birth:** {st.session_state.user_info['dob']}")
    st.write(f"**Height:** {st.session_state.user_info['height']} cm")
    st.write(f"**Weight:** {st.session_state.user_info['weight']} kg")


tab1,tab2 = st.tabs(['Journal Tab', 'Analytics Tab'])


def filter_data(df, horizon):
    """Filter data based on selected horizon."""

    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.sort_values('timestamp', ascending=True)

    if horizon == '1d':
        return df[df['timestamp'] >= pd.Timestamp.now() - pd.Timedelta(days=1)]
    elif horizon == '1w':
        return df[df['timestamp'] >= pd.Timestamp.now() - pd.Timedelta(weeks=1)]
    elif horizon == '1m':
        return df[df['timestamp'] >= pd.Timestamp.now() - pd.DateOffset(months=1)]
    elif horizon == '6m':
        return df[df['timestamp'] >= pd.Timestamp.now() - pd.DateOffset(months=6)]
    elif horizon == '1y':
        return df[df['timestamp'] >= pd.Timestamp.now() - pd.DateOffset(years=1)]
    elif horizon == '5y':
        return df[df['timestamp'] >= pd.Timestamp.now() - pd.DateOffset(years=5)]
    else:
        return df

df = fetch_journal_entries(st.session_state.db, st.session_state.user_info['username'])


with tab2:
    # selection = col2.segmented_control("Horizon", ['1d', '1w', '1m', '6m', '1y', '5y', 'all'], label_visibility='collapsed')

    selection = st.select_slider("Horizon", ['1d', '1w', '1m', '6m', '1y', '5y'], label_visibility='collapsed')

    filtered_df = filter_data(df, selection)
    filtered_df = filtered_df.set_index('timestamp')
    print(filtered_df)

    c1, c2 = st.columns([1,1.5])

    with c1.container(border=True, height=600):
        # Reflection Score Chart
        reflection_chart_data = pd.DataFrame(filtered_df[['reflection_score']])
        st.markdown('<div style="display: flex; justify-content: center;"><h6>Reflection Score</h6></div>', unsafe_allow_html=True)
        st.line_chart(reflection_chart_data, height=130)

        # Stress Chart
        stress_chart_data = pd.DataFrame(filtered_df[['stress_score']])
        st.markdown('<div style="display: flex; justify-content: center;"><h6>Stress</h6></div>', unsafe_allow_html=True)
        st.line_chart(stress_chart_data, height=130)

        # Anxiety Chart
        anxiety_chart_data = pd.DataFrame(filtered_df[['anxiety_score']])
        st.markdown('<div style="display: flex; justify-content: center;"><h6>Anxiety</h6></div>', unsafe_allow_html=True)
        st.line_chart(anxiety_chart_data, height=130)

    with c2.container(border=True, height=600):
        # Recurring Themes Chart
        recurring_themes_data = pd.DataFrame(np.abs(np.random.randn(len(filtered_df), 1)), columns=["Themes"])
        st.markdown('<div style="display: flex; justify-content: center;"><h6>Recurring Themes</h6></div>', unsafe_allow_html=True)
        wordcloud_fig = generate_wordcloud(filtered_df['journal_text'])
        st.pyplot(wordcloud_fig)


with tab1:
    col1,col2 = st.columns(2)
    col1.markdown('<div style="display: flex; justify-content: center;"><h6>Journal</h6></div>',unsafe_allow_html=True)
    journal_text = col1.text_area(
        "Journal",
        placeholder="Write down your thoughts ...", height=400, label_visibility='collapsed'
    )

    col2.markdown('<div style="display: flex; justify-content: center;"><h6>AI Reflections & Recommendations</h6></div>',unsafe_allow_html=True)
    text_output = col2.container(border=True, height=400)

    if st.button("Submit", use_container_width=True, type='primary'):
        reflection_score = score_reflection_ai(journal_text)
        stress_score = score_stress_ai(journal_text)
        anxiety_score = score_anxiety_ai(journal_text)

        st.session_state['ai_output'] = generate_ai_report(journal_text)
        text_output.write_stream(stream_data)
        save_journal_entry(st.session_state['db'], st.session_state.user_info['username'], journal_text, reflection_score, stress_score, anxiety_score)

