from __future__ import annotations

import os
import re
from collections.abc import MutableMapping
from dataclasses import dataclass
from pathlib import Path

APP_DIRECTORY_NAME = "Microvid"
ENV_FILENAME = ".env"
PREFERRED_GOOGLE_CREDENTIALS_FILENAME = "google_cloud_credentials.json"
CONFIG_DIRECTORY_ENV = "MICROVID_CONFIG_DIR"
NON_SERVICE_ACCOUNT_JSON_FILENAMES = {
    "youtube_client_secret.json",
    "youtube_token.json",
}

_ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class RuntimeEnvironment:
    config_dir: Path
    env_file: Path | None
    google_credentials_file: Path | None
    loaded_env_keys: tuple[str, ...]


def local_config_directory(
    environ: MutableMapping[str, str] | None = None,
) -> Path:
    """Return the per-user directory used for untracked Microvid secrets."""
    env = os.environ if environ is None else environ
    override = env.get(CONFIG_DIRECTORY_ENV)
    if override:
        return Path(override).expanduser()

    local_app_data = env.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data).expanduser() / APP_DIRECTORY_NAME

    # This is also the documented fallback when LOCALAPPDATA is unavailable.
    return Path.home() / "AppData" / "Local" / APP_DIRECTORY_NAME


def _dotenv_entry(line: str) -> tuple[str, str] | None:
    candidate = line.strip().lstrip("\ufeff")
    if not candidate or candidate.startswith("#"):
        return None
    if candidate.startswith("export "):
        candidate = candidate[7:].lstrip()
    if "=" not in candidate:
        return None

    key, value = candidate.split("=", 1)
    key = key.strip()
    if not _ENV_KEY.fullmatch(key):
        return None

    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value


def _discover_google_credentials(config_dir: Path) -> Path | None:
    preferred = config_dir / PREFERRED_GOOGLE_CREDENTIALS_FILENAME
    if preferred.is_file():
        return preferred.resolve()

    # Accommodate the original filename supplied by Google when there is only
    # one JSON file. Do not guess when several JSON files are present.
    candidates = sorted(
        path
        for path in config_dir.glob("*.json")
        if path.is_file() and path.name.casefold() not in NON_SERVICE_ACCOUNT_JSON_FILENAMES
    )
    if len(candidates) == 1:
        return candidates[0].resolve()
    return None


def load_local_runtime_environment(
    environ: MutableMapping[str, str] | None = None,
    *,
    config_dir: str | Path | None = None,
) -> RuntimeEnvironment:
    """Load untracked per-user credentials without overriding explicit settings.

    Values already present in the process environment take precedence. The
    default directory is ``%LOCALAPPDATA%\\Microvid`` on Windows, with
    ``~/AppData/Local/Microvid`` as a fallback.
    """
    env = os.environ if environ is None else environ
    directory = (
        Path(config_dir).expanduser()
        if config_dir is not None
        else local_config_directory(env)
    )
    env_path = directory / ENV_FILENAME
    loaded_keys: list[str] = []

    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            entry = _dotenv_entry(line)
            if entry is None:
                continue
            key, value = entry
            if not env.get(key):
                env[key] = value
                loaded_keys.append(key)

    credentials: Path | None = None
    configured_credentials = env.get("GOOGLE_APPLICATION_CREDENTIALS")
    if configured_credentials:
        configured_path = Path(configured_credentials).expanduser()
        if not configured_path.is_absolute() and "GOOGLE_APPLICATION_CREDENTIALS" in loaded_keys:
            configured_path = directory / configured_path
            env["GOOGLE_APPLICATION_CREDENTIALS"] = str(configured_path.resolve())
        if configured_path.is_file():
            credentials = configured_path.resolve()
    else:
        credentials = _discover_google_credentials(directory)
        if credentials is not None:
            env["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials)
            loaded_keys.append("GOOGLE_APPLICATION_CREDENTIALS")

    return RuntimeEnvironment(
        config_dir=directory,
        env_file=env_path if env_path.is_file() else None,
        google_credentials_file=credentials,
        loaded_env_keys=tuple(loaded_keys),
    )
