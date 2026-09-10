import pytest

from microvid.llm import LLMError
from microvid.narration_polisher import polish_lesson_narration


class PolishProvider:
    provider_name = "gemini"
    model = "fake-polish"

    def __init__(self, raw_latex=False):
        self.raw_latex = raw_latex
        self.prompt = ""

    def generate_json(self, prompt, schema):
        self.prompt = prompt
        narration = (
            r"The result follows from \\frac{a}{b}."
            if self.raw_latex
            else "Focus on the larger contribution first. It controls most of the uncertainty, so improving the smaller term would make little practical difference."
        )
        return {
            "slides": [
                {"slide_id": "V01S01", "narration": narration, "tts_text": None},
                {
                    "slide_id": "V01S02",
                    "narration": "Pause here and decide which contribution should be improved first.",
                    "tts_text": None,
                },
            ]
        }


def _manifest():
    return {
        "video_id": "V01",
        "title": "Uncertainty Budget",
        "focus": "Identify the dominant contribution.",
        "learning_outcomes": ["Identify the dominant contribution."],
        "generation": {"passes": 2},
        "slides": [
            {
                "id": "V01S01",
                "slide_type": "concept",
                "title": "Which term dominates?",
                "onscreen": ["Compare the contributions"],
                "narration": "Compare them.",
                "visual_direction": "Highlight the larger contribution.",
                "equation_latex": None,
                "source_block_ids": ["b0001"],
                "estimated_seconds": 40,
            },
            {
                "id": "V01S02",
                "slide_type": "check",
                "title": "Choose the improvement",
                "onscreen": ["Which measurement should be improved?"],
                "narration": "Choose one.",
                "visual_direction": "Show the two alternatives.",
                "equation_latex": None,
                "source_block_ids": [],
                "estimated_seconds": 25,
            },
        ],
    }


def _context():
    return {
        "course": {"narration_wpm": 130},
        "global_course_context": {"course_summary": "A short measurement course."},
        "lesson": {"id": "V01"},
        "authoritative_core_blocks": [
            {"id": "b0001", "text": "The larger contribution dominates the uncertainty budget."}
        ],
        "reference_blocks": [],
    }


def test_narration_polish_changes_only_spoken_fields_and_records_metrics():
    manifest = _manifest()
    original_title = manifest["slides"][0]["title"]
    original_source_ids = list(manifest["slides"][0]["source_block_ids"])
    provider = PolishProvider()

    polished = polish_lesson_narration(manifest, _context(), provider)

    assert "DEDICATED NARRATION POLISH PASS" in provider.prompt
    assert polished["slides"][0]["title"] == original_title
    assert polished["slides"][0]["source_block_ids"] == original_source_ids
    assert polished["slides"][0]["narration"].startswith("Focus on the larger contribution")
    assert polished["slides"][0]["narration_word_count"] > 0
    assert polished["generation"]["passes"] == 3
    assert polished["generation"]["narration_polish"]["prompt_set"] == "narration_polish_v1"


def test_narration_polish_rejects_raw_latex_in_final_speech():
    with pytest.raises(LLMError, match="speech-hygiene"):
        polish_lesson_narration(_manifest(), _context(), PolishProvider(raw_latex=True))
