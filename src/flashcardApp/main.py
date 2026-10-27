# This is the main starting point for a simple math flashcard game

import sys
import json
import random
import os
import base64

try:
    from . import operations
    from . import constants
except (ImportError, SyntaxError, ValueError):
    import operations
    import constants

try:
    from .db import (
        get_database_overview,
        get_or_create_player,
        get_player_stats,
        log_session,
    )
except (ImportError, SyntaxError, ValueError):
    from db import (
        get_database_overview,
        get_or_create_player,
        get_player_stats,
        log_session,
    )


def start():

    correct_answer = 0

    def validateAnswer(expected_answer, answer):
        nonlocal correct_answer
        if expected_answer == answer:
            print("great job")
            # Keep track of number of correct answers
            correct_answer += 1
        else:
            print(f"not quite The correct answer was {expected_answer}")

    try:
        # capture the name and save it for later use
        print("Hello and welcome.  It's time to practice our math facts")
        print("(Press Ctrl + C at any prompt to instantly quit the game)\n")
        name = input("what is your first name:")

        # give some options of what type of flashcards you want to practice
        # options are 1 - addition, 2 - subtraction, 3 - multiplication, 4 - division
        while True:
            try:
                practice_type_inp = int(
                    input(
                        f"what type of math would you like to practice? {constants.practice_type}:"
                    )
                )

                if practice_type_inp in constants.practice_type:
                    print("valid")
                    break
                else:
                    print("Error: you need to select valid choice.")
            except ValueError:
                # Handles cases where the input is not a number (e.g., 'abc')
                print("Error: Invalid input. Please enter a whole number.")

        # We have a valid math type generate the question
        while True:
            match constants.practice_type[practice_type_inp]:
                case "addition":
                    question_values = operations.generateAdditionQuestion()
                    symbol = "+"
                case "subtraction":
                    question_values = operations.generateSubtractionQuestion()
                    symbol = "-"
                case "multiplication":
                    question_values = operations.generateMultiplicationQuestion()
                    symbol = "*"
                case "division":
                    question_values = operations.generateDivisionQuestion()
                    symbol = "/"
                case _:
                    return

            answer = input(
                f"Can you tell me what {question_values[0]} {symbol} {question_values[1]} equals?"
            )

            validateAnswer(int(question_values[2]), int(answer))
    except KeyboardInterrupt:
        print(f"\n\nYour answered {correct_answer} questions correctly")
        print("\nExiting game... Goodbye!")
        sys.exit(0)


# Handle AWS Lambda event so that we can use this code in a serverless environment
def lambda_handler(event, context):
    """
    The entrypoint for AWS Lambda. Safely unpacks the tuples returned by operations.py
    """
    if not isinstance(event, dict):
        event = {}

    request_context = event.get("requestContext") or {}
    http_context = request_context.get("http") or {}
    method = http_context.get("method", event.get("httpMethod", "GET")).upper()

    if method == "POST":
        body = event.get("body") or {}
        if isinstance(body, str):
            if event.get("isBase64Encoded"):
                body = base64.b64decode(body).decode("utf-8")
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return _json_response(400, {"error": "Request body must be JSON."})
        if not isinstance(body, dict):
            return _json_response(400, {"error": "Request body must be a JSON object."})
        action = body.get("action")
        if action == "get_or_create_player":
            name = body.get("name")
            if not isinstance(name, str) or not name.strip():
                return _json_response(400, {"error": "Player name is required."})
            name = name.strip()
            if len(name) > 255:
                return _json_response(
                    400, {"error": "Player name must be 255 characters or fewer."}
                )

            player_id = get_or_create_player(name)
            return _json_response(
                200,
                {"status": "player_ready", "player_id": player_id, "name": name},
            )

        if action == "log_session":
            player_id = body.get("player_id")
            practice_type = body.get("practice_type")
            score = body.get("score")
            total = body.get("total")
            if (
                not isinstance(player_id, int)
                or isinstance(player_id, bool)
                or player_id <= 0
            ):
                return _json_response(
                    400, {"error": "Player ID must be a positive integer."}
                )
            if (
                not isinstance(practice_type, str)
                or practice_type not in constants.practice_type.values()
            ):
                return _json_response(400, {"error": "Practice type is invalid."})
            if (
                not isinstance(score, int)
                or isinstance(score, bool)
                or not isinstance(total, int)
                or isinstance(total, bool)
                or score < 0
                or total < score
            ):
                return _json_response(400, {"error": "Session scores are invalid."})

            log_session(player_id, practice_type, score, total)
            return _json_response(200, {"status": "session_logged"})

        if action == "get_database_overview":
            return _json_response(200, get_database_overview())

        if action == "get_player_stats":
            player_id = body.get("player_id")
            if (
                not isinstance(player_id, int)
                or isinstance(player_id, bool)
                or player_id <= 0
            ):
                return _json_response(
                    400, {"error": "Player ID must be a positive integer."}
                )

            stats = get_player_stats(player_id)
            if stats is None:
                return _json_response(404, {"error": "Player was not found."})
            return _json_response(200, stats)

        else:
            return _json_response(400, {"error": "Unsupported POST action."})

    params = event.get("queryStringParameters") or {}
    practice_type_inp = event.get("practice_type") or params.get("practice_type", 1)
    user_answer = event.get("user_answer", None)
    expected_answer = event.get("expected_answer", None)

    # Scenario A: Evaluating a user's answer
    if user_answer is not None and expected_answer is not None:
        is_correct = int(user_answer) == int(expected_answer)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "status": "evaluated",
                    "correct": is_correct,
                    "message": (
                        "great job"
                        if is_correct
                        else f"not quite. The correct answer was {expected_answer}"
                    ),
                }
            ),
        }

    # Scenario B: Generating a fresh question (Fallback for browser visits)
    try:
        math_type = constants.practice_type.get(int(practice_type_inp), "addition")
    except (AttributeError, TypeError, ValueError):
        math_type = "addition"

    match math_type:
        case "addition":
            question_values = operations.generateAdditionQuestion()
            symbol = "+"
        case "subtraction":
            question_values = operations.generateSubtractionQuestion()
            symbol = "-"
        case "multiplication":
            question_values = operations.generateMultiplicationQuestion()
            symbol = "*"
        case "division":
            question_values = operations.generateDivisionQuestion()
            symbol = "/"
        case _:
            question_values = (1, 1, 2)  # Safety absolute tuple fallback
            symbol = "+"

    # Unpack the numbers from your tuple safely
    # question_values[0] = first number
    # question_values[1] = second number
    # question_values[2] = expected math answer
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "status": "question_generated",
                "question": f"Can you tell me what {question_values[0]} {symbol} {question_values[1]} equals?",
                "expected_answer": int(question_values[2]),
            }
        ),
    }


def _json_response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


if __name__ == "__main__":
    start()
