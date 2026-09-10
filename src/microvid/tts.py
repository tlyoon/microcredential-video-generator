from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol
import os
import warnings


@dataclass(frozen=True)
class TTSConfig:
    provider: str = "google_cloud_chirp3"
    language_code: str = "en-GB"
    voice_name: str = "en-GB-Chirp3-HD-Leda"
    audio_encoding: str = "LINEAR16"
    speaking_rate: float = 1.0
    location: str = "global"
    normalize_scientific_speech: bool = True
    fallback_provider: str | None = "sapi"
    fallback_on_error: bool = True
    audition_voices: tuple[str, ...] = (
        "en-GB-Chirp3-HD-Leda",
        "en-GB-Chirp3-HD-Aoede",
        "en-GB-Chirp3-HD-Kore",
    )

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> "TTSConfig":
        data = dict(data or {})
        voices = data.get("audition_voices")
        if voices is not None:
            data["audition_voices"] = tuple(str(v) for v in voices)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def with_overrides(self, **overrides: Any) -> "TTSConfig":
        return replace(self, **{k: v for k, v in overrides.items() if v is not None})

    @property
    def output_suffix(self) -> str:
        return ".mp3" if self.audio_encoding.upper() == "MP3" else ".wav"


@dataclass(frozen=True)
class SynthesisResult:
    path: Path
    provider: str
    voice_name: str | None = None
    language_code: str | None = None


class TTSProvider(Protocol):
    def synthesize(self, text: str, output_path: Path) -> SynthesisResult: ...


class SapiTTSProvider:
    def __init__(self, config: TTSConfig):
        self.config = config

    def synthesize(self, text: str, output_path: Path) -> SynthesisResult:
        if os.name != "nt":
            raise RuntimeError("SAPI TTS requires Windows.")
        try:
            import win32com.client  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install the package with the [windows] extra to use SAPI TTS.") from exc
        output_path = output_path.with_suffix(".wav")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        voice = win32com.client.Dispatch("SAPI.SpVoice")
        stream = win32com.client.Dispatch("SAPI.SpFileStream")
        stream.Open(str(output_path.resolve()), 3, False)
        try:
            voice.AudioOutputStream = stream
            voice.Speak(text)
        finally:
            stream.Close()
        return SynthesisResult(output_path, "sapi")


class GoogleCloudChirp3TTSProvider:
    def __init__(self, config: TTSConfig):
        self.config = config

    def synthesize(self, text: str, output_path: Path) -> SynthesisResult:
        try:
            from google.cloud import texttospeech  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install google-cloud-texttospeech to use Chirp 3 HD.") from exc
        location = (self.config.location or "global").strip().lower()
        options = None if location in {"", "global"} else {"api_endpoint": f"{location}-texttospeech.googleapis.com"}
        client = texttospeech.TextToSpeechClient(client_options=options) if options else texttospeech.TextToSpeechClient()
        encoding_name = self.config.audio_encoding.upper()
        try:
            encoding = getattr(texttospeech.AudioEncoding, encoding_name)
        except AttributeError as exc:
            raise ValueError(f"Unsupported Google Cloud TTS audio encoding: {encoding_name}") from exc
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=texttospeech.VoiceSelectionParams(
                language_code=self.config.language_code,
                name=self.config.voice_name,
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=encoding,
                speaking_rate=float(self.config.speaking_rate),
            ),
        )
        output_path = output_path.with_suffix(self.config.output_suffix)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.audio_content)
        return SynthesisResult(output_path, "google_cloud_chirp3", self.config.voice_name, self.config.language_code)


class FallbackTTSProvider:
    def __init__(self, primary: TTSProvider, fallback: TTSProvider | None):
        self.primary = primary
        self.fallback = fallback

    def synthesize(self, text: str, output_path: Path) -> SynthesisResult:
        try:
            return self.primary.synthesize(text, output_path)
        except Exception as primary_exc:
            if self.fallback is None:
                raise
            warnings.warn(f"Primary TTS failed ({primary_exc!s}); using configured fallback provider.", RuntimeWarning, stacklevel=2)
            try:
                return self.fallback.synthesize(text, output_path)
            except Exception as fallback_exc:
                raise RuntimeError(f"Primary TTS failed: {primary_exc!s}; fallback TTS also failed: {fallback_exc!s}") from fallback_exc


def _single_provider(config: TTSConfig, provider_name: str) -> TTSProvider:
    name = provider_name.strip().lower()
    if name in {"google_cloud_chirp3", "chirp3", "google", "google_cloud"}:
        return GoogleCloudChirp3TTSProvider(config)
    if name == "sapi":
        return SapiTTSProvider(config)
    raise ValueError(f"Unsupported TTS provider: {provider_name}")


def provider_from_tts_config(config: TTSConfig) -> TTSProvider:
    primary = _single_provider(config, config.provider)
    if not config.fallback_on_error or not config.fallback_provider:
        return primary
    return FallbackTTSProvider(primary, _single_provider(config, config.fallback_provider))
