from microvid.media import media_capabilities


def test_media_capabilities_shape():
    caps = media_capabilities()
    assert "ffmpeg" in caps
    assert "powerpoint_automation_possible" in caps
    assert "sapi_tts_possible" in caps
