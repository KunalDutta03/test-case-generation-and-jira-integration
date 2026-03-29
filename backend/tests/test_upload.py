"""
Tests for document upload and parsing functionality.
"""
import pytest
import json
import os
import tempfile
from app.services.parser import parse_document


def test_parse_txt():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("Hello World\nLine 2")
        path = f.name
    try:
        result = parse_document(path, '.txt')
        assert "Hello World" in result
        assert "Line 2" in result
    finally:
        os.unlink(path)


def test_parse_json():
    data = {"feature": "Login", "steps": ["Given user opens app", "When user logs in"]}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        result = parse_document(path, '.json')
        assert "Login" in result
        assert "Login" in result or "feature" in result.lower()
    finally:
        os.unlink(path)


def test_parse_csv():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("name,age,email\nAlice,30,alice@test.com\nBob,25,bob@test.com")
        path = f.name
    try:
        result = parse_document(path, '.csv')
        assert "Alice" in result
        assert "Bob" in result
    finally:
        os.unlink(path)


def test_unsupported_type():
    with pytest.raises(ValueError, match="Unsupported"):
        parse_document("test.xyz", ".xyz")
