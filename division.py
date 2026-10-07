import random
def generateDivisionQuestion(difficultylevel):
	num1 = random.randint(1,10)
	num2 = random.randint(1,10)

	# for easy We need to generate a question that has a 0 remainder
	while (num1 % num2) != 0:
		num1 = random.randint(1,10)
		num2 = random.randint(1,10)

	#answer = input(f"Can you tell me what {num1} / {num2} equals?")
	return [num1, num2]



