"""
Tests for Gherkin JSON parsing in generator service.
"""
import pytest
from app.services.generator import _parse_gherkin_json


def test_parse_clean_json():
    raw = '[{"feature": "Login", "scenario": "Valid login", "gherkin_text": "Feature: Login\\n  Scenario: Valid login\\n    Given...", "type": "positive"}]'
    result = _parse_gherkin_json(raw)
    assert len(result) == 1
    assert result[0]['feature'] == 'Login'


def test_parse_with_markdown_fence():
    raw = '```json\n[{"feature": "F1", "scenario": "S1", "gherkin_text": "Feature: F1", "type": "positive"}]\n```'
    result = _parse_gherkin_json(raw)
    assert len(result) == 1


def test_parse_multiple_scenarios():
    scenarios = [{"feature": f"Feature{i}", "scenario": f"Scenario{i}", "gherkin_text": f"Feature: F{i}", "type": "positive"} for i in range(5)]
    import json
    raw = json.dumps(scenarios)
    result = _parse_gherkin_json(raw)
    assert len(result) == 5


def test_parse_invalid_raises():
    with pytest.raises((ValueError, Exception)):
        _parse_gherkin_json("this is not json at all!!!")
