import pytest

from flashcardApp.aws_auth import create_aws_session


def test_create_aws_session_uses_streamlit_credentials():
    session = create_aws_session(
        {
            "aws_access_key_id": "test-access-key",
            "aws_secret_access_key": "test-secret-key",
            "aws_session_token": "test-session-token",
        }
    )

    credentials = session.get_credentials().get_frozen_credentials()
    assert credentials.access_key == "test-access-key"
    assert credentials.secret_key == "test-secret-key"
    assert credentials.token == "test-session-token"


def test_create_aws_session_rejects_incomplete_streamlit_credentials():
    with pytest.raises(ValueError, match="must include both"):
        create_aws_session({"aws_access_key_id": "test-access-key"})
