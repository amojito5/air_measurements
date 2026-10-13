from pathlib import Path
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

CONFIG_DIR = Path(__file__).resolve().parent / "configs"


def load_config(env_name: str = "paris") -> dict:
    """Load a specific TOML configuration file from the configs directory."""
    config_path = CONFIG_DIR / f"{env_name}.toml"
    if not config_path.exists():
        available_configs = [f.stem for f in CONFIG_DIR.glob("*.toml")]
        raise FileNotFoundError(
            f"Error: Configuration file '{env_name}.toml' not found.\n"
            f"Available configurations in '{CONFIG_DIR.name}/': \n"
            f"{available_configs}"
        )

    with open(config_path, "rb") as f:
        return tomllib.load(f)
