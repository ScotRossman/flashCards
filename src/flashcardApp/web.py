import json
import os

import streamlit as st
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from streamlit.errors import StreamlitSecretNotFoundError

try:
    from .aws_auth import create_aws_session
except ImportError:
    from aws_auth import create_aws_session

# api AWSURL
API_URL = "https://62x9u9qzf1.execute-api.us-east-1.amazonaws.com/flashcard"

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
        response = requests.get(f"{API_URL}?practice_type={practice_code}", timeout=10)
        response.raise_for_status()
        response = response.json()
        # If your Lambda returns the structure you defined:
        st.session_state.question = response.get("question")
        st.session_state.expected = response.get("expected_answer")
        st.session_state.submitted = False
        st.session_state.user_input = ""
    except Exception as e:
        # Fallback if the API response structure differs slightly
        st.error(f"Could not fetch question: {e}")


def post_api_action(payload):
    body = json.dumps(payload)
    try:
        aws_secrets = st.secrets["aws"]
    except KeyError:
        aws_secrets = None
    except StreamlitSecretNotFoundError as error:
        if error.error_id != "no-secrets-found":
            raise
        aws_secrets = None

    credentials = create_aws_session(aws_secrets).get_credentials()
    if credentials is None:
        raise ValueError(
            "AWS credentials were not found. Add an [aws] section with "
            "aws_access_key_id and aws_secret_access_key to Streamlit secrets, "
            "or configure the default Boto3 credential chain."
        )

    request = AWSRequest(
        method="POST",
        url=API_URL,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    SigV4Auth(
        credentials.get_frozen_credentials(),
        "execute-api",
        os.getenv("API_AWS_REGION", "us-east-1"),
    ).add_auth(request)

    response = requests.post(
        API_URL,
        data=body,
        headers=dict(request.headers),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_or_create_player(name):
    payload = post_api_action({"action": "get_or_create_player", "name": name})
    player_id = payload.get("player_id")
    if not isinstance(player_id, int) or player_id <= 0:
        raise ValueError("Player API returned an invalid player ID.")
    return player_id


def log_session(player_id, practice_type, score, total):
    post_api_action(
        {
            "action": "log_session",
            "player_id": player_id,
            "practice_type": practice_type,
            "score": score,
            "total": total,
        }
    )


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
            try:
                st.session_state.player_id = get_or_create_player(
                    st.session_state.player_name
                )
            except (requests.RequestException, ValueError) as e:
                st.error(f"Could not create or find player: {e}")
            else:
                fetch_question(practice_type_code)
                st.rerun()
with sb_col2:
    if st.session_state.player_name != "" and selected_option is not None:
        if sb_col2.button("quit"):
            try:
                if st.session_state.player_id > 0:
                    log_session(
                        st.session_state.player_id,
                        selected_option,
                        st.session_state.correct_answers,
                        st.session_state.correct_answers
                        + st.session_state.wrong_answers,
                    )
            except (requests.RequestException, ValueError) as e:
                st.error(f"Could not save the practice session: {e}")
            else:
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
                st.session_state.player_id = 0
                st.rerun()


st.sidebar.markdown("---")
st.sidebar.markdown(f"**Score:** {st.session_state.correct_answers} correct")

st.subheader(st.session_state.player_name + " " + st.session_state.question)

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
