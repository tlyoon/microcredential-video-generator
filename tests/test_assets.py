from microvid.assets import seconds_to_srt


def test_srt_time():
    assert seconds_to_srt(65.432) == "00:01:05,432"
