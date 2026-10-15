import streamlit as st
import requests
from db import init_db, get_or_create_player, log_session, get_leaderboard

# api AWSURL
API_URL = "https://62x9u9qzf1.execute-api.us-east-1.amazonaws.com/flashcard"

# init the database
init_db()

st.title("🧮 Math Flashcards with db")

# Initialize cross-refresh session states
if "question" not in st.session_state:
    st.session_state.question = "Welcome to the flashcard practice application. Enter your name and select what type of math you want to practice"
    st.session_state.expected = None
    st.session_state.correct_answers = 0
    st.session_state.wrong_answers = 0
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "player_name" not in st.session_state:
    st.session_state.player_name = ""
if "player_id" not in st.session_state:
    st.session_state.player_id = 0


# function to fetch a question
def fetch_question(practice_code):
    try:
        response = requests.get(f"{API_URL}?practice_type={practice_code}").json()
        # If your Lambda returns the structure you defined:
        st.session_state.question = response.get("question")
        st.session_state.expected = response.get("expected_answer")
        st.session_state.submitted = False
        st.session_state.user_input = ""
    except Exception as e:
        # Fallback if the API response structure differs slightly
        st.error(f"Could not fetch question: {e}")


# sidebar setup:
st.sidebar.header("game setup")
# Bind text input to session state
st.session_state.player_name = st.sidebar.text_input(
    "Player Name", value=st.session_state.player_name
)

practice_options = {"addition": 1, "subtraction": 2, "multiplication": 3, "division": 4}

selected_option = st.sidebar.selectbox("Practice Type", list(practice_options.keys()))
practice_type_code = practice_options[selected_option]

# Create columns in the sidebar for Start and Quit buttons
sb_col1, sb_col2 = st.sidebar.columns(2)

with sb_col1:
    if st.session_state.player_name != "" and selected_option is not None:
        if sb_col1.button("Start"):
            st.session_state.player_id = get_or_create_player(
                st.session_state.player_name
            )
            fetch_question(practice_type_code)
            st.rerun()
with sb_col2:
    if st.session_state.player_name != "" and selected_option is not None:
        if sb_col2.button("quit"):
            log_session(
                st.session_state.player_id,
                selected_option,
                st.session_state.correct_answers,
                st.session_state.correct_answers + st.session_state.wrong_answers,
            )
            st.session_state.question = (
                "Welcome to the flashcard practice application. Enter your name and"
                " select what type of math you want to practice"
            )
            st.session_state.expected = None
            st.session_state.correct_answers = 0
            st.session_state.wrong_answers = 0
            st.session_state.submitted = False
            st.session_state.user_input = ""
            selected_option = None
            st.session_state.player_name = ""
            st.rerun()


st.sidebar.markdown("---")
st.sidebar.markdown(f"**Score:** {st.session_state.correct_answers} correct")

st.subheader(st.session_state.player_name + st.session_state.question)

if st.session_state.expected is not None:
    user_ans = st.text_input("Enter your answer:", key="user_input")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit"):
            st.session_state.submitted = True
            if int(user_ans) == st.session_state.expected:
                st.success("Correct! Great job!")
                st.session_state.correct_answers += 1
                st.rerun()

            else:
                st.error(f"Incorrect. The answer was {st.session_state.expected}")
                st.session_state.wrong_answers += 1
    with col2:
        if st.button("next Question", disabled=not st.session_state.submitted):
            fetch_question(practice_type_code)
            st.rerun()
