from telecom.diarization.alignment import align_document, align_segment, word_weight


def test_word_weight_adds_pause_for_punctuation():
    assert word_weight("casa.") > word_weight("casa")
    assert word_weight("casa,") > word_weight("casa")


def test_words_fill_segment_span_exactly():
    segment = {"textodefala": "Eu vou para casa.", "quemfala": "Juiz",
               "segundos_inicio": 10.0, "segundos_fim": 14.0, "chunk_origem": 2}
    words = align_segment(segment)
    assert [w.palavra for w in words] == ["Eu", "vou", "para", "casa."]
    assert words[0].segundos_inicio == 10.0
    assert words[-1].segundos_fim == 14.0
    assert all(a.segundos_fim == b.segundos_inicio for a, b in zip(words, words[1:]))


def test_empty_text_yields_no_words():
    assert align_segment({"textodefala": "   "}) == []


def test_document_counts_all_words():
    payload = {"arquivo": "a.mp4", "segmentos": [
        {"textodefala": "um dois", "segundos_inicio": 0.0, "segundos_fim": 1.0},
        {"textodefala": "tres", "segundos_inicio": 1.0, "segundos_fim": 2.0},
    ]}
    result = align_document(payload)
    assert result.total_palavras == 3
    assert result.arquivo == "a.mp4"
