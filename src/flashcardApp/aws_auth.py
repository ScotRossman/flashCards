from collections.abc import Mapping

import boto3


def create_aws_session(
    aws_secrets: Mapping[str, str] | None,
) -> boto3.Session:
    if aws_secrets is None:
        return boto3.Session()

    access_key = aws_secrets.get("aws_access_key_id")
    secret_key = aws_secrets.get("aws_secret_access_key")
    session_token = aws_secrets.get("aws_session_token")

    if not access_key and not secret_key and not session_token:
        return boto3.Session()
    if not access_key or not secret_key:
        raise ValueError(
            "Streamlit [aws] secrets must include both aws_access_key_id "
            "and aws_secret_access_key."
        )

    credentials = {
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
    }
    if session_token:
        credentials["aws_session_token"] = session_token

    return boto3.Session(**credentials)
