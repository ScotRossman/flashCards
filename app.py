#This is the main starting point for a simple math flashcard game

import addition
import division
def validateAnswer(num1, num2, answer, type):
	if (num1 / num2) == answer:
		print("great")

math_types = {"addition": "+" ,"subtraction": "-", "multiplication": "*", "division": "/" }

print("Hello and welcome.  It's time to practice our math facts")
#name = input("what is your first name:")
#practice_type = input("what type of math would you like to practice?")

#addition.generateQuestion()
numbers = division.generateDivisionQuestion("e")
answer = input(f"Can you tell me what {numbers[0]} / {numbers[1]} equals?")

validateAnswer(numbers[0],numbers[1], answer, "/")


