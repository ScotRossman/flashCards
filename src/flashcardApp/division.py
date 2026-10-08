import random


def generateDivisionQuestion():

    # for easy We need to generate a question that has a 0 remainder
    num2 = random.randint(1, 10)  # divisor
    result = random.randint(1, 10)  # the integer answer
    num1 = num2 * result  # dividend, always > num2 and evenly divisible

    return [num1, num2, result]
