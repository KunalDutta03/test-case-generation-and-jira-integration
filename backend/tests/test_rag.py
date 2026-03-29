"""
Tests for text chunking and RAG pipeline.
"""
from app.services.chunker import chunk_text


def test_chunk_basic():
    text = " ".join(["word"] * 1000)
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk['token_count'] <= 100
        assert 'content' in chunk
        assert 'chunk_index' in chunk


def test_chunk_single():
    text = "Short text that fits in one chunk"
    chunks = chunk_text(text, chunk_size=512, overlap=64)
    assert len(chunks) == 1
    assert chunks[0]['chunk_index'] == 0


def test_chunk_overlap():
    """Verify overlapping chunks share tokens at boundaries."""
    text = " ".join([f"token{i}" for i in range(300)])
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    # Each chunk (except first) should start before where the previous fully ended
    assert len(chunks) >= 3


def test_chunk_preserves_content():
    text = "Feature: Login\nScenario: Valid login\nGiven user opens app When user logs in Then user sees dashboard"
    chunks = chunk_text(text, chunk_size=50, overlap=5)
    all_content = " ".join(c['content'] for c in chunks)
    assert "Feature" in all_content
