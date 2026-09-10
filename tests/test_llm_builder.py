from docx import Document
from microvid.docx_parser import extract_docx
from microvid.llm_manifest_builder import build_lesson_manifest_with_llm
from microvid.qa import validate_manifest

class FakeProvider:
    provider_name="gemini"; model="fake-gemini"
    def __init__(self): self.calls=0
    def generate_json(self,prompt,schema):
        self.calls+=1
        return {"lesson_title":"Measurement Basics","learning_outcomes":["Explain why a measurement needs a unit."],"slides":[
            {"slide_type":"hook","title":"What makes a measurement meaningful?","onscreen":["A number alone is incomplete."],"narration":"A laboratory result is more than a number. We need enough context to know what the number means.","lecturer_notes":["Use a familiar ruler example."],"visual_direction":"Show an unlabeled 12.4, then reveal mm.","equation_latex":None,"source_block_ids":[],"estimated_seconds":35},
            {"slide_type":"concept","title":"Value plus unit","onscreen":["12.4 mm"],"narration":"The source states that a measured value needs a unit, so the unit is part of the scientific meaning of the result.","lecturer_notes":["Stress that units are not optional labels."],"visual_direction":"Highlight the value and unit separately.","equation_latex":None,"source_block_ids":["b0001","b0002"],"estimated_seconds":55},
            {"slide_type":"check","title":"Check your understanding","onscreen":["What is missing from 12.4?"],"narration":"Pause and identify what information is needed before this can be treated as a measurement.","lecturer_notes":["Pause before discussion."],"visual_direction":"Keep only the question on screen.","equation_latex":None,"source_block_ids":[],"estimated_seconds":30},
            {"slide_type":"takeaway","title":"Takeaway","onscreen":["Report values with units."],"narration":"A measurement becomes interpretable only when the value and its unit are reported together.","lecturer_notes":["Close briefly."],"visual_direction":"Return to 12.4 mm with a check mark.","equation_latex":None,"source_block_ids":["b0002"],"estimated_seconds":30}],"editorial_flags":[]}

def test_llm_builder_uses_two_passes_and_preserves_provenance(tmp_path):
    p=tmp_path/"sample.docx"; d=Document(); d.add_heading("1. Measurement",level=1); d.add_paragraph("A measured value needs a unit."); d.save(p)
    extraction=extract_docx(p); course={"title":"Test","audience":"Freshmen","narration_wpm":130,"max_slides":7,"llm":{}}
    lesson={"id":"V01","title":"Measurement","focus":"Understand measurement reporting.","target_minutes":3,"core_selectors":[{"heading_contains":"Measurement"}]}
    provider=FakeProvider(); manifest=build_lesson_manifest_with_llm(extraction,course,lesson,provider,review_pass=True)
    assert provider.calls==2; assert manifest["generation"]["mode"]=="llm"; assert manifest["generation"]["passes"]==2
    assert manifest["editorial_status"]=="llm_draft_requires_review"; assert manifest["slides"][1]["source_block_ids"]==["b0001","b0002"]
    assert not any(i["severity"]=="error" for i in validate_manifest(manifest))
