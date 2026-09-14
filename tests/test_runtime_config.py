from microvid.runtime_config import load_local_runtime_environment


def test_loads_dotenv_and_preferred_google_credentials(tmp_path):
    config_dir = tmp_path / "Microvid"
    config_dir.mkdir()
    (config_dir / ".env").write_text(
        '# Local secrets\nGEMINI_API_KEY="test-gemini-key"\n',
        encoding="utf-8",
    )
    credentials = config_dir / "google_cloud_credentials.json"
    credentials.write_text('{"type":"service_account"}', encoding="utf-8")
    environ = {}

    result = load_local_runtime_environment(environ, config_dir=config_dir)

    assert environ["GEMINI_API_KEY"] == "test-gemini-key"
    assert environ["GOOGLE_APPLICATION_CREDENTIALS"] == str(credentials.resolve())
    assert result.env_file == config_dir / ".env"
    assert result.google_credentials_file == credentials.resolve()


def test_explicit_environment_values_take_precedence(tmp_path):
    config_dir = tmp_path / "Microvid"
    config_dir.mkdir()
    (config_dir / ".env").write_text(
        "GEMINI_API_KEY=file-key\nGOOGLE_APPLICATION_CREDENTIALS=file.json\n",
        encoding="utf-8",
    )
    explicit_credentials = tmp_path / "explicit.json"
    explicit_credentials.write_text("{}", encoding="utf-8")
    environ = {
        "GEMINI_API_KEY": "explicit-key",
        "GOOGLE_APPLICATION_CREDENTIALS": str(explicit_credentials),
    }

    result = load_local_runtime_environment(environ, config_dir=config_dir)

    assert environ["GEMINI_API_KEY"] == "explicit-key"
    assert environ["GOOGLE_APPLICATION_CREDENTIALS"] == str(explicit_credentials)
    assert result.loaded_env_keys == ()
    assert result.google_credentials_file == explicit_credentials.resolve()


def test_uses_the_only_json_file_when_google_filename_is_unchanged(tmp_path):
    config_dir = tmp_path / "Microvid"
    config_dir.mkdir()
    downloaded_credentials = config_dir / "project-name-123456.json"
    downloaded_credentials.write_text('{"type":"service_account"}', encoding="utf-8")
    environ = {}

    result = load_local_runtime_environment(environ, config_dir=config_dir)

    assert result.google_credentials_file == downloaded_credentials.resolve()
    assert environ["GOOGLE_APPLICATION_CREDENTIALS"] == str(
        downloaded_credentials.resolve()
    )


def test_relative_google_credentials_path_in_dotenv_is_relative_to_config_dir(tmp_path):
    config_dir = tmp_path / "Microvid"
    config_dir.mkdir()
    credentials = config_dir / "credentials.json"
    credentials.write_text("{}", encoding="utf-8")
    (config_dir / ".env").write_text(
        "GOOGLE_APPLICATION_CREDENTIALS=credentials.json\n",
        encoding="utf-8",
    )
    environ = {}

    result = load_local_runtime_environment(environ, config_dir=config_dir)

    assert result.google_credentials_file == credentials.resolve()
    assert environ["GOOGLE_APPLICATION_CREDENTIALS"] == str(credentials.resolve())


def test_youtube_json_files_are_not_mistaken_for_tts_credentials(tmp_path):
    config_dir = tmp_path / "Microvid"
    config_dir.mkdir()
    (config_dir / "youtube_client_secret.json").write_text("{}", encoding="utf-8")
    (config_dir / "youtube_token.json").write_text("{}", encoding="utf-8")
    environ = {}

    result = load_local_runtime_environment(environ, config_dir=config_dir)

    assert result.google_credentials_file is None
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in environ
