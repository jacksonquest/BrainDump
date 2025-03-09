import hashlib
from datetime import datetime
import numpy as np
from together import Together
import pandas as pd
import streamlit as st

from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt

TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]

if 'together_api_key' not in st.session_state:
    st.session_state['together_api_key'] = TOGETHER_API_KEY

client = Together(api_key=st.session_state['together_api_key'])
model_name = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"


# User Management Functions
def add_user(db, username, password, name, dob, height, weight):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user_data = {
        "username": username,
        "password": hashed_password,
        "name": name,
        "dob": dob.isoformat(),
        "height": height,
        "weight": weight
    }
    db.collection("users").document(username).set(user_data)

def authenticate_user(db, username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user_ref = db.collection("users").document(username).get()
    if user_ref.exists:
        return user_ref.to_dict()["password"] == hashed_password
    return False

def get_user_info(db, username):
    user_ref = db.collection("users").document(username).get()
    if user_ref.exists:
        return user_ref.to_dict()
    return None


def save_journal_entry(db, username, journal_text, reflection_score, stress_score, anxiety_score):
    entry_data = {
        "journal_text": journal_text,
        "reflection_score": reflection_score,
        "stress_score": stress_score,
        "anxiety_score": anxiety_score,
        "timestamp": datetime.now().isoformat()
    }
    db.collection("users").document(username).collection("journal_entries").add(entry_data)

def score_mood(text):
    return np.random.randint(1, 10)  # Dummy model for scoring


def score_reflection_ai(text):
    response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": f'Based on the {text}, Generate a score between (1-10) for the mood of the user with 0 being negative and 10 being positive. The output should just be a number and there should not be any text.'}],
        )
    
    bot_reply = response.choices[0].message.content
    return int(bot_reply)

def score_stress_ai(text):
    response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": f'Based on the {text}, Generate a score between (1-10) for the stress of the user with 0 being no stress and 10 being highly stressed. The output should just be a number and there should not be any text.'}],
        )
    
    bot_reply = response.choices[0].message.content
    return int(bot_reply)

def score_anxiety_ai(text):
    response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": f'Based on the {text}, Generate a score between (1-10) for the anxiety of the user with 0 being no anxiety and 10 being highly anxieous. The output should just be a number and there should not be any text.'}],
        )
    
    bot_reply = response.choices[0].message.content
    return int(bot_reply)

def generate_ai_report(journal_text):
    prompt = f"""You are an insightful and empathetic mental wellness coach. The user has provided a journal entry describing their thoughts, feelings, and experiences. Your task is to analyze the entry and provide meaningful suggestions or thoughtful remarks that can help the user reflect, improve their mindset, or take positive actions. Focus on emotional well-being, personal growth, and mental clarity. Keep it short and in bullets.
                Journal Entry:
                {journal_text}
                Output Format:
                Summary of Emotions: (e.g., Positive, Anxious, Reflective, etc.)
                Key Themes Identified: (e.g., Stress at work, Relationship concerns, etc.)
                Actionable Suggestions: (Provide 2-3 helpful suggestions or reflections.)"""
    
    response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
    
    bot_reply = response.choices[0].message.content
    return bot_reply


def fetch_journal_entries(db, username):
    entries_ref = db.collection("users").document(username).collection("journal_entries").stream()
    
    data = []
    for entry in entries_ref:
        entry_data = entry.to_dict()
        data.append({
            "timestamp": entry_data.get("timestamp", ""),
            "reflection_score": entry_data.get("reflection_score", ""),  # Assuming mood score maps to reflection
            "stress_score": entry_data.get("stress_score", ""),  # Mapping emotional intensity to stress
            "anxiety_score": entry_data.get("anxiety_score", ""),  # Mapping clarity score to anxiety
            "journal_text": entry_data.get("journal_text", "")
        })

    df = pd.DataFrame(data)
    return df


def generate_wordcloud(text_data):
    """Generate a word cloud from text data with stopwords removed."""
    text_combined = ' '.join(text_data.dropna())  # Combine all journal entries
    
    # Custom stopwords (optional: add domain-specific or unwanted words)
    custom_stopwords = set(STOPWORDS).union({"journal", "entry", "thoughts", "day", "today"})

    # Generate word cloud
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        colormap='viridis',
        stopwords=custom_stopwords  # Remove stopwords
    ).generate(text_combined)

    # Display Word Cloud
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig