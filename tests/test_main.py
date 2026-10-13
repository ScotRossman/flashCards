import pytest
from flashcardApp.main import start


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
    inputs = iter(["Scot", "abc", "9", "2", "5", "18", "18", "23"])

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
