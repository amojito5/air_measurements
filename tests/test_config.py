import pytest
from config import load_config


def test_load_existing_config():
    """Vérifie qu'une configuration existante se charge correctement."""
    config = load_config("paris")
    assert isinstance(config, dict)
    assert "area" in config
    assert config["area"]["name"] == "Paris_Centre"


def test_load_missing_config_raises_error():
    """Vérifie qu'une erreur explicite est levée si le fichier n'existe pas."""
    with pytest.raises(FileNotFoundError) as exc_info:
        load_config("ville_inexistante")
    
    assert "Error: Configuration file" in str(exc_info.value)
