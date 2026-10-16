import json
import pytest
from flashcardApp import main
from flashcardApp.main import lambda_handler, start


def test_start_game_success(monkeypatch, capsys):
    inputs = iter(["Scot", "1", "4", "18", "18"])

    def mock_input(prompt=""):
        try:
            return next(inputs)
        except StopIteration:
            raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", mock_input)

    # 3. Run the start function
    with pytest.raises(SystemExit) as exc_info:
        start()

    # 4. Capture the terminal output
    captured = capsys.readouterr().out

    # 5. Assertions: Verify the game prints the correct welcomes and success messages
    assert "Hello and welcome" in captured


def test_start_game_bad_selection(monkeypatch, capsys):
    """Test 2: Negative Path - Tests both the except block and the else block in the loop."""
    # 1. Provide a careful sequence of inputs to trace every single line of your loop:
    # First:  Name ("Scot")
    # Second: "abc" -> Throws ValueError, hits 'except ValueError', loops back
    # Third:  "9"   -> Valid int but not a choice, hits 'else', loops back
    # Fourth: "4"   -> Valid int and choice, hits 'break', exits loop safely
    # Fifth:  "5"   -> Submits final math answer to finish execution
    inputs = iter(["Scot", "abc", "9", "1", "5", "18", "18", "23"])

    def mock_input(prompt=""):
        try:
            return next(inputs)
        except StopIteration:
            raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", mock_input)
    with pytest.raises(SystemExit) as exc_info:
        start()

    captured = capsys.readouterr().out

    # Verify that your 'except' error message was hit and printed
    assert "Error: Invalid input. Please enter a whole number." in captured

    # Verify that your 'else' error message was hit and printed
    assert "Error: you need to select valid choice." in captured


@pytest.mark.parametrize(
    ("practice_type", "generator", "question_values", "symbol"),
    [
        (1, "generateAdditionQuestion", (3, 4, 7), "+"),
        (2, "generateSubtractionQuestion", (9, 4, 5), "-"),
        (3, "generateMultiplicationQuestion", (3, 4, 12), "*"),
        (4, "generateDivisionQuestion", (12, 3, 4), "/"),
    ],
)
def test_start_game_runs_each_math_operation(
    monkeypatch, capsys, practice_type, generator, question_values, symbol
):
    monkeypatch.setattr(main.operations, generator, lambda: question_values)
    inputs = iter(["Scot", str(practice_type), str(question_values[2])])
    prompts = []

    def mock_input(prompt=""):
        prompts.append(prompt)
        try:
            return next(inputs)
        except StopIteration:
            raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", mock_input)

    with pytest.raises(SystemExit) as exc_info:
        start()

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert f"{question_values[0]} {symbol} {question_values[1]}" in prompts[2]
    assert "great job" in output
    assert "Your answered 1 questions correctly" in output


def test_start_game_reports_incorrect_answer_without_increasing_score(
    monkeypatch, capsys
):
    monkeypatch.setattr(
        main.operations, "generateAdditionQuestion", lambda: (10, 5, 15)
    )
    inputs = iter(["Scot", "1", "14"])

    def mock_input(prompt=""):
        try:
            return next(inputs)
        except StopIteration:
            raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", mock_input)

    with pytest.raises(SystemExit) as exc_info:
        start()

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "not quite The correct answer was 15" in output
    assert "Your answered 0 questions correctly" in output


@pytest.mark.parametrize(
    ("practice_type", "generator", "question_values", "symbol"),
    [
        (1, "generateAdditionQuestion", (3, 4, 7), "+"),
        (2, "generateSubtractionQuestion", (9, 4, 5), "-"),
        (3, "generateMultiplicationQuestion", (3, 4, 12), "*"),
        (4, "generateDivisionQuestion", (12, 3, 4), "/"),
    ],
)
def test_lambda_handler_generates_question_for_each_practice_type(
    monkeypatch, practice_type, generator, question_values, symbol
):
    monkeypatch.setattr(main.operations, generator, lambda: question_values)

    response = lambda_handler(
        {"queryStringParameters": {"practice_type": str(practice_type)}}, None
    )

    assert response["statusCode"] == 200
    assert response["headers"] == {"Content-Type": "application/json"}
    assert json.loads(response["body"]) == {
        "status": "question_generated",
        "question": f"Can you tell me what {question_values[0]} {symbol} {question_values[1]} equals?",
        "expected_answer": question_values[2],
    }


@pytest.mark.parametrize(
    "event",
    [
        {},
        {"practice_type": "not-a-number"},
        {"practice_type": "99"},
        None,
    ],
)
def test_lambda_handler_defaults_to_addition_for_missing_or_invalid_type(
    monkeypatch, event
):
    monkeypatch.setattr(main.operations, "generateAdditionQuestion", lambda: (2, 3, 5))

    response = lambda_handler(event, None)

    assert json.loads(response["body"]) == {
        "status": "question_generated",
        "question": "Can you tell me what 2 + 3 equals?",
        "expected_answer": 5,
    }


@pytest.mark.parametrize(
    ("user_answer", "expected_answer", "is_correct", "message"),
    [
        (8, 8, True, "great job"),
        (7, 8, False, "not quite. The correct answer was 8"),
    ],
)
def test_lambda_handler_evaluates_answer(
    user_answer, expected_answer, is_correct, message
):
    response = lambda_handler(
        {"user_answer": str(user_answer), "expected_answer": expected_answer}, None
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {
        "status": "evaluated",
        "correct": is_correct,
        "message": message,
    }
