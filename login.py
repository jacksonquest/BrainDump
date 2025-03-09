import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

from utils.helper_functions import add_user, authenticate_user, get_user_info


# Load credentials securely
FIRESTORE_KEY = st.secrets["FIRESTORE_KEY"]

# Firebase Setup
if not firebase_admin._apps:
    cred = credentials.Certificate(eval(FIRESTORE_KEY))
    firebase_admin.initialize_app(cred)
db = firestore.client()


# Store credentials securely in session state
if 'db' not in st.session_state:
    st.session_state['db'] = db
if 'together_api_key' not in st.session_state:
    st.session_state['together_api_key'] = TOGETHER_API_KEY

# Streamlit UI

st.set_page_config(layout="centered", initial_sidebar_state="collapsed")

def main():
    st.markdown('<div style="display: flex; justify-content: center;"><h1>BrainDump</h1></div>',unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

    with tab2:
        st.subheader("Create New Account")
        new_user = st.text_input("Username", key='username_up')
        new_password = st.text_input("Password", type='password', key='pass_up')
        name = st.text_input("Name")
        dob = st.date_input("Date of Birth", min_value=datetime(1900, 1, 1))
        height = st.number_input("Height (cm)", min_value=50, max_value=250)
        weight = st.number_input("Weight (kg)", min_value=20, max_value=300)

        if st.button("Sign Up"):
            try:
                add_user(st.session_state['db'], new_user, new_password, name, dob, height, weight)
                st.success("Account created successfully! Please Sign In.")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab1:
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Sign In"):
            if authenticate_user(st.session_state['db'], username, password):
                st.success(f"Welcome back, {username}!")
                st.session_state['username'] = username
                st.session_state.user_info = get_user_info(st.session_state['db'], username)
                st.switch_page('pages/app.py')
            else:
                st.error("Invalid Username or Password")

if __name__ == "__main__":
    main()
