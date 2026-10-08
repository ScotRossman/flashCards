# This is the main starting point for a simple math flashcard game

from . import addition
from . import division
from . import constants


def start():
    def validateAnswer(expected_answer, answer):
        if expected_answer == answer:
            print("great")

    # capture the name and save it for later use
    print("Hello and welcome.  It's time to practice our math facts")
    name = input("what is your first name:")

    # give some options of what type of flashcards you want to practice
    # options are 1 - addition, 2 - subtraction, 3 - multiplication, 4 - division
    while True:
        try:
            practice_type_inp = int(input(
                f"what type of math would you like to practice? {constants.practice_type}:"))

            if practice_type_inp in constants.practice_type:
                print("valid")
                break
            else:
                print("Error: you need to select valid choice.")
        except ValueError:
            # Handles cases where the input is not a number (e.g., 'abc')
        	print("Error: Invalid input. Please enter a whole number.")

    # addition.generateQuestion()
# numbers = division.generateDivisionQuestion()
# answer = input(f"Can you tell me what {numbers[0]} / {numbers[1]} equals?")


# validateAnswer(int(numbers[2]), int(answer))
if __name__ == "__main__":
    start()
