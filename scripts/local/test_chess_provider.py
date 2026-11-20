"""Offline provider-selection tests; no Modal or model calls."""
from argparse import Namespace

import pytest

from assignment.cli import _configure_chess_model


def args(**overrides):
    values = dict(model=None, model_env="OPENAI_MODEL", base_url=None,
                  base_url_env="OPENAI_BASE_URL", api_key_env="OPENAI_API_KEY")
    values.update(overrides)
    return Namespace(**values)


@pytest.fixture
def configured(monkeypatch):
    for key, value in {
        "OPENAI_MODEL": "default-model", "OPENAI_BASE_URL": "https://default.test/v1",
        "OPENAI_API_KEY": "default-test-key", "GPT_OSS_NAME": "openai/gpt-oss-120b",
        "GPT_OSS_URL": "https://openrouter.ai/api/v1", "GPT_OSS_KEY": "other-test-key",
    }.items():
        monkeypatch.setenv(key, value)


def test_default_provider_is_preserved(configured):
    import os
    assert _configure_chess_model(args()) == "default-model"
    assert os.environ["OPENAI_API_KEY"] == "default-test-key"
    assert os.environ["OPENAI_BASE_URL"] == "https://default.test/v1"


def test_named_provider_selects_all_three_values(configured):
    import os
    model = _configure_chess_model(args(model_env="GPT_OSS_NAME", base_url_env="GPT_OSS_URL", api_key_env="GPT_OSS_KEY"))
    assert model == "openai/gpt-oss-120b"
    assert os.environ["OPENAI_API_KEY"] == "other-test-key"
    assert os.environ["OPENAI_BASE_URL"] == "https://openrouter.ai/api/v1"


def test_explicit_model_and_url_override_environment(configured):
    import os
    assert _configure_chess_model(args(model="override", base_url="http://localhost:9000/v1")) == "override"
    assert os.environ["OPENAI_BASE_URL"] == "http://localhost:9000/v1"


@pytest.mark.parametrize("missing", ["GPT_OSS_NAME", "GPT_OSS_URL", "GPT_OSS_KEY"])
def test_missing_provider_setting_does_not_fall_back(configured, monkeypatch, missing):
    import os
    monkeypatch.setenv(missing, "")
    with pytest.raises(SystemExit, match=missing):
        _configure_chess_model(args(model_env="GPT_OSS_NAME", base_url_env="GPT_OSS_URL", api_key_env="GPT_OSS_KEY"))
    assert os.environ["OPENAI_API_KEY"] == "default-test-key"
    assert os.environ["OPENAI_BASE_URL"] == "https://default.test/v1"
