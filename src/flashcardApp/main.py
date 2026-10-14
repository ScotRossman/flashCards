# This is the main starting point for a simple math flashcard game

import sys
import json
import random
import os

try:
    from . import operations
    from . import constants
except (ImportError, SyntaxError, ValueError):
    import operations
    import constants


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


def lambda_handler(event, context):
    """
    The entrypoint for AWS Lambda. Safely unpacks the tuples returned by operations.py
    """
    if not isinstance(event, dict):
        event = {}

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


if __name__ == "__main__":
    start()
