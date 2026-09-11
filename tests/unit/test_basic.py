from app.core.text_utils import chunk_text


def test_basic():
    assert 1 + 1 == 2


def test_chunk_text():
    text = "A" * 500

    chunks = chunk_text(text, chunk_size=200)

    assert len(chunks) == 3
    assert len(chunks[0]) == 200
    assert len(chunks[1]) == 200
    assert len(chunks[2]) == 100