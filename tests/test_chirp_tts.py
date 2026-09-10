from microvid.speech import normalize_scientific_speech
from microvid.tts import FallbackTTSProvider, TTSConfig, provider_from_tts_config


def test_scientific_speech_normalization():
    text = "The result is 9.81 m s⁻² ± 0.02 m s⁻², or 0.2%."
    spoken = normalize_scientific_speech(text)
    assert "metres per second squared" in spoken
    assert "plus or minus" in spoken
    assert "percent" in spoken


def test_default_chirp_config_is_female_leda():
    cfg = TTSConfig()
    assert cfg.provider == "google_cloud_chirp3"
    assert cfg.language_code == "en-GB"
    assert cfg.voice_name == "en-GB-Chirp3-HD-Leda"
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
