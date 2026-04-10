import json

from pydantic import BaseModel

from src.gemini_client import _build_example, _extract_json
from src.models import GradingResult, TriageResult


class TestBuildExample:
    def test_triage_result(self):
        example = _build_example(TriageResult)
        assert example == {"is_readable": True, "reason": "..."}

    def test_grading_result_nested(self):
        example = _build_example(GradingResult)
        assert "tasks" in example
        assert isinstance(example["tasks"], list)
        assert len(example["tasks"]) == 1
        task = example["tasks"][0]
        assert "component_scores" in task
        assert isinstance(task["component_scores"], list)
        assert len(task["component_scores"]) == 1
        assert "mistakes" in task
        assert isinstance(task["mistakes"], list)

    def test_simple_types(self):
        class Simple(BaseModel):
            s: str
            i: int
            f: float
            b: bool

        example = _build_example(Simple)
        assert example == {"s": "...", "i": 0, "f": 0.0, "b": True}

    def test_nested_model(self):
        class Inner(BaseModel):
            value: str

        class Outer(BaseModel):
            inner: Inner

        example = _build_example(Outer)
        assert example == {"inner": {"value": "..."}}

    def test_list_of_models(self):
        class Item(BaseModel):
            name: str

        class Container(BaseModel):
            items: list[Item]

        example = _build_example(Container)
        assert example == {"items": [{"name": "..."}]}

    def test_list_of_primitives(self):
        class WithList(BaseModel):
            tags: list[str]

        example = _build_example(WithList)
        assert example == {"tags": []}


class TestExtractJson:
    def test_from_code_block(self):
        text = '```json\n{"a": 1}\n```'
        assert json.loads(_extract_json(text)) == {"a": 1}

    def test_from_code_block_with_surrounding(self):
        text = 'Here is the result:\n```json\n{"a": 1}\n```\nDone.'
        assert json.loads(_extract_json(text)) == {"a": 1}

    def test_raw_object(self):
        text = 'Some text {"a": 1} more text'
        assert json.loads(_extract_json(text)) == {"a": 1}

    def test_nested_braces(self):
        text = '{"a": {"b": 1}}'
        result = json.loads(_extract_json(text))
        assert result["a"]["b"] == 1

    def test_no_json_returns_text(self):
        text = "just plain text"
        assert _extract_json(text) == "just plain text"

    def test_prefers_code_block(self):
        text = '```json\n{"source": "block"}\n```\n{"source": "raw"}'
        result = json.loads(_extract_json(text))
        assert result["source"] == "block"

    def test_multiline(self):
        text = '```json\n{\n  "a": 1,\n  "b": 2\n}\n```'
        result = json.loads(_extract_json(text))
        assert result == {"a": 1, "b": 2}
