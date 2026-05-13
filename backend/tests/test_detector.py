from app.services.detector import detect


def test_detects_ssn_and_email():
    text = "Patient John Doe, SSN 123-45-6789, email jdoe@example.com."
    types = {m.entity_type for m in detect(text)}
    assert "US_SSN" in types
    assert "EMAIL" in types


def test_detects_phone_and_date():
    text = "Call (313) 555-0142 on 03/14/2026 to confirm."
    matches = detect(text)
    types = {m.entity_type for m in matches}
    assert "PHONE" in types
    assert "DATE" in types


def test_mrn_pattern():
    text = "Record MRN: A12345 on file."
    matches = detect(text)
    assert any(m.entity_type == "MRN" for m in matches)


def test_overlapping_spans_resolved():
    text = "SSN 123-45-6789 also looks like a phone."
    matches = detect(text)
    # The SSN should win over any low-confidence phone-shaped span.
    ssns = [m for m in matches if m.entity_type == "US_SSN"]
    assert len(ssns) == 1
    for m in matches:
        if m.entity_type != "US_SSN":
            assert m.end <= ssns[0].start or m.start >= ssns[0].end


def test_empty_text():
    assert detect("") == []
