#this is the module that will handle all the addition math functions.
import random

def generateQuestion():
	num1 = random.randint(1,10)
	num2 = random.randint(1,10)

	answer = input(f"Can you tell me what {num1} + {num2} equals?")

	if (num1 + num2 == int(answer)):
		print("That's correct")
	else:
		print("you're stupid")