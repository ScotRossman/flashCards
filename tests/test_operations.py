import pytest
from unittest.mock import patch
from flashcardApp import operations



# Test for addition
@patch("random.randint")
def test_generate_addition_question_logic(mock_randint):
    mock_randint.side_effect = [4, 7]
    num1, num2, answer = operations.generateAdditionQuestion()

    assert num1 == 4
    assert num2 == 7
    assert answer == 11


def test_generate_addition_question_range():
    # test that we will never get a number > 10 as we call the function multiple times

    for _ in range(100):
        num1, num2, answer = operations.generateAdditionQuestion()

        assert 1 <= num1 <= 10
        assert 1 <= num2 <= 10
        assert answer == num1 + num2

@patch("random.randint")
def test_generate_subtraction_question_logic(mock_randint):
    mock_randint.side_effect = [7, 4]
    num1, num2, answer = operations.generateSubtractionQuestion()
    assert num1 == 7
    assert num2 == 4
    assert answer == 3

@patch("random.randint")
def test_generate_subtraction_question_logic_while(mock_randint):
    mock_randint.side_effect = [5, 5, 2]

    result = operations.generateSubtractionQuestion()
    assert result == [5,2,3]