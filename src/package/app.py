#This is the main starting point for a simple math flashcard game

import addition
import division
import constants
def validateAnswer(expected_answer, answer):
	if expected_answer == answer:
		print("great")

#capture the name and save it for later use
print("Hello and welcome.  It's time to practice our math facts")
name = input("what is your first name:")

#give some options of what type of flashcards you want to practice
#options are 1 - addition, 2 - subtraction, 3 - multiplication, 4 - division
practice_type_inp = input(f"what type of math would you like to practice? {constants.practice_type}:")


#addition.generateQuestion()
numbers = division.generateDivisionQuestion()
answer = input(f"Can you tell me what {numbers[0]} / {numbers[1]} equals?")

validateAnswer(int(numbers[2]), int(answer))


