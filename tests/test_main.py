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


def test_lambda_handler_lists_available_api_actions():
    response = lambda_handler(
        {"queryStringParameters": {"action": "capabilities"}}, None
    )

    assert response["statusCode"] == 200
    actions = json.loads(response["body"])["actions"]
    assert [action["name"] for action in actions] == [
        "get_question",
        "get_or_create_player",
        "log_session",
        "log_sessions",
        "get_database_overview",
        "get_player_stats",
    ]
    assert actions[0]["authorization"] == "public"
    assert actions[3]["authorization"] == "JWT"
    assert all(
        action["authorization"] == "AWS_IAM"
        for action in actions[1:]
        if action["name"] != "log_sessions"
    )


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


def test_lambda_handler_creates_or_finds_player(monkeypatch):
    captured_names = []

    def mock_get_or_create_player(name):
        captured_names.append(name)
        return 42

    monkeypatch.setattr(main, "get_or_create_player", mock_get_or_create_player)

    response = lambda_handler(
        {
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "get_or_create_player", "name": "  Ada  "}),
        },
        None,
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {
        "status": "player_ready",
        "player_id": 42,
        "name": "Ada",
    }
    assert captured_names == ["Ada"]


def test_lambda_handler_logs_session(monkeypatch):
    captured_sessions = []

    def mock_log_session(player_id, practice_type, score, total):
        captured_sessions.append((player_id, practice_type, score, total))

    monkeypatch.setattr(main, "log_session", mock_log_session)

    response = lambda_handler(
        {
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps(
                {
                    "action": "log_session",
                    "player_id": 42,
                    "practice_type": "addition",
                    "score": 3,
                    "total": 4,
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"status": "session_logged"}
    assert captured_sessions == [(42, "addition", 3, 4)]


def test_lambda_handler_logs_sessions_for_jwt_subject(monkeypatch):
    captured = []

    def mock_log_cognito_sessions(cognito_sub, name, email, sessions):
        captured.append((cognito_sub, name, email, sessions))

    monkeypatch.setattr(main, "log_cognito_sessions", mock_log_cognito_sessions)

    response = lambda_handler(
        {
            "requestContext": {
                "http": {"method": "POST"},
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "sub": "cognito-sub-123",
                            "email": "ada@example.com",
                            "email_verified": "true",
                        }
                    }
                },
            },
            "body": json.dumps(
                {
                    "action": "log_sessions",
                    "name": "Ada",
                    "sessions": [
                        {"practice_type": "addition", "score": 3, "total": 4},
                        {"practice_type": "division", "score": 2, "total": 3},
                    ],
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {
        "status": "sessions_logged",
        "sessions": 2,
    }
    assert captured == [
        (
            "cognito-sub-123",
            "Ada",
            "ada@example.com",
            [("addition", 3, 4), ("division", 2, 3)],
        )
    ]


def test_lambda_handler_logs_sessions_from_http_api_v1_claims(monkeypatch):
    captured = []
    monkeypatch.setattr(
        main,
        "log_cognito_sessions",
        lambda cognito_sub, name, email, sessions: captured.append(
            (cognito_sub, name, email, sessions)
        ),
    )

    response = lambda_handler(
        {
            "version": "1.0",
            "httpMethod": "POST",
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "cognito-sub-v1",
                        "email": "ada@example.com",
                        "email_verified": "true",
                    },
                    "scopes": None,
                }
            },
            "body": json.dumps(
                {
                    "action": "log_sessions",
                    "name": "Ada",
                    "sessions": [{"practice_type": "addition", "score": 1, "total": 1}],
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 200
    assert captured == [
        ("cognito-sub-v1", "Ada", "ada@example.com", [("addition", 1, 1)])
    ]


def test_lambda_handler_rejects_jwt_session_batch_without_subject():
    response = lambda_handler(
        {
            "requestContext": {
                "http": {"method": "POST"},
                "routeKey": "POST /flashcard",
                "authorizer": {"jwt": {"claims": {}}},
            },
            "body": json.dumps(
                {
                    "action": "log_sessions",
                    "name": "Ada",
                    "sessions": [{"practice_type": "addition", "score": 1, "total": 1}],
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 401
    assert json.loads(response["body"]) == {
        "error": "Session batches require Cognito authorization."
    }


def test_lambda_handler_rejects_iam_session_action_on_jwt_route():
    response = lambda_handler(
        {
            "requestContext": {
                "http": {"method": "POST"},
                "routeKey": "POST /flashcard",
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "sub": "cognito-sub-123",
                            "email": "ada@example.com",
                            "email_verified": "true",
                        }
                    }
                },
            },
            "body": json.dumps(
                {
                    "action": "log_session",
                    "player_id": 42,
                    "practice_type": "addition",
                    "score": 1,
                    "total": 1,
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 403


@pytest.mark.parametrize(
    "sessions",
    [
        [],
        [{"practice_type": "addition", "score": 0, "total": 0}],
        [{"practice_type": "other", "score": 0, "total": 1}],
        [
            {"practice_type": "addition", "score": 1, "total": 1},
            {"practice_type": "addition", "score": 1, "total": 1},
        ],
        [{"practice_type": "addition", "score": True, "total": 1}],
        [{"practice_type": "addition", "score": 2, "total": 1}],
    ],
)
def test_lambda_handler_rejects_invalid_jwt_session_batches(sessions):
    response = lambda_handler(
        {
            "requestContext": {
                "http": {"method": "POST"},
                "routeKey": "POST /flashcard",
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "sub": "cognito-sub-123",
                            "email": "ada@example.com",
                            "email_verified": "true",
                        }
                    }
                },
            },
            "body": json.dumps(
                {"action": "log_sessions", "name": "Ada", "sessions": sessions}
            ),
        },
        None,
    )

    assert response["statusCode"] == 400


@pytest.mark.parametrize(
    "claims",
    [
        {"sub": "cognito-sub-123", "email": "ada@example.com"},
        {
            "sub": "cognito-sub-123",
            "email": "ada@example.com",
            "email_verified": "false",
        },
        {
            "sub": "cognito-sub-123",
            "email": "x" * 321,
            "email_verified": "true",
        },
    ],
)
def test_lambda_handler_requires_verified_cognito_email(claims):
    response = lambda_handler(
        {
            "requestContext": {
                "http": {"method": "POST"},
                "routeKey": "POST /flashcard",
                "authorizer": {"jwt": {"claims": claims}},
            },
            "body": json.dumps(
                {
                    "action": "log_sessions",
                    "name": "Ada",
                    "sessions": [{"practice_type": "addition", "score": 1, "total": 1}],
                }
            ),
        },
        None,
    )

    assert response["statusCode"] == 403
    assert json.loads(response["body"]) == {
        "error": "A verified Cognito email is required."
    }


def test_lambda_handler_returns_database_overview(monkeypatch):
    overview = {
        "summary": {
            "players": 1,
            "sessions": 0,
            "correct_answers": 0,
            "questions_answered": 0,
            "accuracy_percent": 0.0,
        },
        "practice_stats": [],
        "players": [{"player_id": 1, "name": "Ada"}],
        "recent_sessions": [],
    }
    monkeypatch.setattr(main, "get_database_overview", lambda: overview)

    response = lambda_handler(
        {
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "get_database_overview"}),
        },
        None,
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == overview


def test_lambda_handler_returns_player_stats(monkeypatch):
    stats = {
        "player": {"player_id": 42, "name": "Ada"},
        "summary": {
            "sessions": 2,
            "correct_answers": 7,
            "questions_answered": 10,
            "accuracy_percent": 70.0,
        },
        "practice_stats": [],
    }
    captured_ids = []

    def mock_get_player_stats(player_id):
        captured_ids.append(player_id)
        return stats

    monkeypatch.setattr(main, "get_player_stats", mock_get_player_stats)

    response = lambda_handler(
        {
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "get_player_stats", "player_id": 42}),
        },
        None,
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == stats
    assert captured_ids == [42]


def test_lambda_handler_returns_not_found_for_unknown_player(monkeypatch):
    monkeypatch.setattr(main, "get_player_stats", lambda player_id: None)

    response = lambda_handler(
        {
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "get_player_stats", "player_id": 999}),
        },
        None,
    )

    assert response["statusCode"] == 404
    assert json.loads(response["body"]) == {"error": "Player was not found."}


@pytest.mark.parametrize("player_id", [None, 0, -1, "42", True])
def test_lambda_handler_rejects_invalid_player_stats_id(player_id):
    response = lambda_handler(
        {
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "get_player_stats", "player_id": player_id}),
        },
        None,
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {
        "error": "Player ID must be a positive integer."
    }


@pytest.mark.parametrize(
    ("body", "expected_error"),
    [
        ("{invalid json", "Request body must be JSON."),
        (
            json.dumps({"action": "get_or_create_player", "name": "  "}),
            "Player name is required.",
        ),
        (
            json.dumps({"action": "get_or_create_player", "name": "A" * 256}),
            "Player name must be 255 characters or fewer.",
        ),
        (
            json.dumps({"action": "unsupported", "name": "Ada"}),
            "Unsupported POST action.",
        ),
    ],
)
def test_lambda_handler_rejects_invalid_player_requests(body, expected_error):
    response = lambda_handler(
        {"requestContext": {"http": {"method": "POST"}}, "body": body}, None
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"error": expected_error}


@pytest.mark.parametrize(
    "session",
    [
        {"player_id": 0, "practice_type": "addition", "score": 0, "total": 0},
        {"player_id": 42, "practice_type": "other", "score": 0, "total": 0},
        {"player_id": 42, "practice_type": "addition", "score": 2, "total": 1},
        {"player_id": True, "practice_type": "addition", "score": 1, "total": 1},
    ],
)
def test_lambda_handler_rejects_invalid_session_requests(session):
    response = lambda_handler(
        {
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "log_session", **session}),
        },
        None,
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"]
