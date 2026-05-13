import io

import fitz


def _build_sample_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        (
            "Patient: Jane Doe\n"
            "DOB: 04/12/1981\n"
            "SSN: 123-45-6789\n"
            "Email: jane.doe@example.com\n"
            "Phone: (313) 555-0142\n"
            "MRN: A98765\n"
            "Visit Date: March 14, 2026\n"
        ),
        fontsize=12,
    )
    buf = doc.tobytes()
    doc.close()
    return buf


def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_upload_detect_and_redact(client):
    pdf_bytes = _build_sample_pdf()
    resp = client.post(
        "/api/documents",
        data={"file": (io.BytesIO(pdf_bytes), "intake.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    doc = resp.get_json()
    assert doc["status"] == "review"
    assert doc["entity_count"] >= 4

    detail = client.get(f"/api/documents/{doc['id']}").get_json()
    types = {e["entity_type"] for e in detail["entities"]}
    assert {"US_SSN", "EMAIL", "PHONE"}.issubset(types)

    redact_resp = client.post(f"/api/documents/{doc['id']}/redact")
    assert redact_resp.status_code == 200
    assert redact_resp.get_json()["status"] == "redacted"

    audit = client.get(f"/api/documents/{doc['id']}/audit").get_json()
    actions = {e["action"] for e in audit}
    assert {"upload", "analyze_complete", "redact"}.issubset(actions)


def test_rejects_non_pdf(client):
    resp = client.post(
        "/api/documents",
        data={"file": (io.BytesIO(b"not a pdf"), "note.txt")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


def test_entity_review_state_transition(client):
    pdf_bytes = _build_sample_pdf()
    resp = client.post(
        "/api/documents",
        data={"file": (io.BytesIO(pdf_bytes), "intake.pdf")},
        content_type="multipart/form-data",
    )
    doc_id = resp.get_json()["id"]
    detail = client.get(f"/api/documents/{doc_id}").get_json()
    entity_id = detail["entities"][0]["id"]

    patch = client.patch(
        f"/api/entities/{entity_id}",
        json={"review_state": "rejected"},
    )
    assert patch.status_code == 200
    assert patch.get_json()["review_state"] == "rejected"
