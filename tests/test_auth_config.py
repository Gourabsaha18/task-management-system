
"""Tests for authentication configuration validation."""

import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "secret_key",
    [
        None,
        "replace-this-with-a-random-secret",
        "short",
    ],
    ids=[
        "missing-secret",
        "default-secret",
        "short-secret",
    ],
)
def test_auth_rejects_invalid_secret_key(secret_key):
    """Importing app.auth should fail for invalid secret keys."""
    env = os.environ.copy()
    env["PYTHON_DOTENV_DISABLED"] = "1"

    if secret_key is None:
        env.pop("SECRET_KEY", None)
    else:
        env["SECRET_KEY"] = secret_key

    result = subprocess.run(
        [sys.executable, "-c", "import app.auth"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Set a strong SECRET_KEY" in result.stderr
