import pytest

from config import load_config


def test_load_existing_config():
    """Config loading test."""
    config = load_config("paris")
    assert isinstance(config, dict)
    assert "area" in config
    assert config["area"]["name"] == "Paris_Centre"


def test_load_missing_config_raises_error():
    """Missing file test."""
    with pytest.raises(FileNotFoundError) as exc_info:
        load_config("ville_inexistante")

    assert "Error: Configuration file" in str(exc_info.value)
