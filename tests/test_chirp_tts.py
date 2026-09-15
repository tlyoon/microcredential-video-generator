from microvid import cli
from microvid.speech import normalize_scientific_speech
from microvid.tts import (
    FallbackTTSProvider,
    TTSConfig,
    _is_transient_tts_error,
    provider_from_tts_config,
)


def test_scientific_speech_normalization():
    text = "The result is 9.81 m s⁻² ± 0.02 m s⁻², or 0.2%."
    spoken = normalize_scientific_speech(text)
    assert "metres per second squared" in spoken
    assert "plus or minus" in spoken
    assert "percent" in spoken


def test_default_chirp_config_is_en_us_female():
    cfg = TTSConfig()
    assert cfg.provider == "google_cloud_chirp3"
    assert cfg.language_code == "en-US"
    assert cfg.voice_name == "en-US-Chirp-HD-F"
    assert cfg.ssml_gender == "FEMALE"
    assert cfg.audio_encoding == "LINEAR16"
    assert cfg.speaking_rate == 0.8
    assert cfg.output_suffix == ".wav"


def test_mapping_and_overrides_are_soft_coded():
    cfg = TTSConfig.from_mapping({
        "provider": "google_cloud_chirp3",
        "language_code": "en-US",
        "voice_name": "en-US-Chirp3-HD-Aoede",
        "speaking_rate": 0.95,
        "audition_voices": ["a", "b"],
    }).with_overrides(voice_name="en-US-Chirp3-HD-Kore")
    assert cfg.language_code == "en-US"
    assert cfg.voice_name == "en-US-Chirp3-HD-Kore"
    assert cfg.speaking_rate == 0.95
    assert cfg.audition_voices == ("a", "b")


def test_provider_wraps_chirp_with_sapi_fallback():
    provider = provider_from_tts_config(TTSConfig())
    assert isinstance(provider, FallbackTTSProvider)


def test_transient_tts_errors_are_identified_without_retrying_auth_errors():
    unavailable = type("ServiceUnavailable", (Exception,), {})()
    forbidden = type("Forbidden", (Exception,), {"code": 403})()

    assert _is_transient_tts_error(unavailable)
    assert not _is_transient_tts_error(forbidden)


def test_tts_audition_voice_name_override_selects_that_voice(monkeypatch, tmp_path):
    captured = {}

    def fake_audition(output_dir, text, config, voices=None):
        captured["voices"] = voices
        return []

    monkeypatch.setattr(cli, "audition_voices", fake_audition)
    args = cli.parser().parse_args([
        "tts-audition",
        "--output-dir",
        str(tmp_path),
        "--voice-name",
        "en-US-Chirp3-HD-Aoede",
        "--language-code",
        "en-US",
    ])

    assert args.func(args) == 0
    assert captured["voices"] == ["en-US-Chirp3-HD-Aoede"]
