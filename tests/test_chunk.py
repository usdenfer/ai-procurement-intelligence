import chunk


def test_short_document_is_single_chunk():
    chunks = chunk.chunk_document(
        "https://x.test/a", "一段不长的公告正文", "标题A", "2026-08-01"
    )
    assert len(chunks) == 1
    c = chunks[0]
    assert c.text == "一段不长的公告正文"
    assert c.url == "https://x.test/a"
    assert c.title == "标题A"
    assert c.published_date == "2026-08-01"
    assert c.index == 0
    assert c.metadata()["chunk_index"] == 0


def test_long_document_splits_by_paragraph():
    para = "这是很长的一段正文内容。" * 100
    text = "\n\n".join([para, para, para])
    chunks = chunk.chunk_document("https://x.test/b", text)
    assert len(chunks) > 1
    assert [c.index for c in chunks] == list(range(len(chunks)))
    assert all(c.text.strip() for c in chunks)


def test_blank_document_produces_no_chunks():
    assert chunk.chunk_document("https://x.test/c", "   \n  ") == []
