# this is the module that will handle all the addition math functions.
import random


def generateAdditionQuestion():
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)

    answer = num1 + num2
    return [num1, num2, answer]


def generateSubtractionQuestion():
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    # first pass make sure num 1 is greater than num2 so we don't have negative answers.
    while num1 <= num2:
        # generate a different random number
        num2 = random.randint(1, 10)
    answer = num1 - num2
    return [num1, num2, answer]

def generateMultiplicationQuestion():
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    answer = num1 * num2
    return [num1, num2, answer]

def generateDivisionQuestion():
    num2 = random.randint(1, 10)  # divisor
    result = random.randint(1, 10)  # the integer answer
    num1 = num2 * result  # dividend, always > num2 and evenly divisible

    return [num1, num2, result]
