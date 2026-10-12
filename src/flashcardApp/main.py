# This is the main starting point for a simple math flashcard game

import sys
from . import operations
from . import constants


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


if __name__ == "__main__":
    start()
