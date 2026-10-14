import streamlit as st
import requests

# api AWSURL
API_URL = "https://62x9u9qzf1.execute-api.us-east-1.amazonaws.com/flashcard"

st.title("🧮 Math Flashcards")

# Initialize cross-refresh session states
if "question" not in st.session_state:
    st.session_state.question = "Click below to generate your first live API question."
    st.session_state.expected = None

# function to fetch a question


def fetch_question(practice_code):
    try:
        response = requests.get(f"{API_URL}?practice_type={practice_code}").json()
        # If your Lambda returns the structure you defined:
        st.session_state.question = response.get("question")
        st.session_state.expected = response.get("expected_answer")
    except Exception as e:
        # Fallback if the API response structure differs slightly
        st.error(f"Could not fetch question: {e}")


# sidebar setup:
st.sidebar.header("game setup")
player_name = st.sidebar.text_input("player Name", value="")
practice_options = {"addition": 1, "subtraction": 2, "multiplication": 3, "division": 4}

selected_option = st.sidebar.selectbox("Practice Type", list(practice_options.keys()))
practice_type_code = practice_options[selected_option]

if player_name != "" and selected_option is not None:
    if st.sidebar.button("Start"):
        fetch_question(practice_type_code)


st.subheader(st.session_state.question)

if st.session_state.expected is not None:
    user_ans = st.number_input("Enter your answer:", step=1, value=0)
    if st.button("Submit"):
        if user_ans == st.session_state.expected:
            st.success("Correct! Great job!")
        else:
            st.error(f"Incorrect. The answer was {st.session_state.expected}")
