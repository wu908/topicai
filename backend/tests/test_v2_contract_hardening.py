"""Contract hardening for v2 request models.

Covers findings from ocr scan session be776634:

* ``ContentProjectCreate.status`` accepted every ``ProjectStatus``, so a
  client could create a project already ``published``/``settled`` and
  bypass the ``ProjectTransition`` state machine entirely.
* ``MaterialCreate.mime_type`` was only length-capped, so CR/LF or other
  header characters could be stored and later echoed into response
  headers (``Content-Type``) at download time.
"""

import pytest
from pydantic import ValidationError

from app.models.v2.content_project import ContentProjectCreate, ProjectStatus
from app.models.v2.material import MaterialCreate

# ==================== ContentProjectCreate ====================


@pytest.mark.parametrize(
    "status", ["creating", "ready_to_publish", "published", "awaiting_review", "settled"]
)
def test_create_project_rejects_non_entry_status(status: str):
    """Only entry states may be set at creation time; later movement must
    go through ``ProjectTransition`` with its reason/version checks."""
    with pytest.raises(ValidationError):
        ContentProjectCreate(title="新选题", status=status, idempotency_key="k-entry")


@pytest.mark.parametrize("status", ["inbox", "preparing"])
def test_create_project_allows_entry_states(status: str):
    body = ContentProjectCreate(title="新选题", status=status, idempotency_key="k-entry")

    assert body.status == ProjectStatus(status)


def test_create_project_defaults_to_preparing():
    body = ContentProjectCreate(title="新选题", idempotency_key="k-entry")

    assert body.status == ProjectStatus.PREPARING


# ==================== MaterialCreate ====================


@pytest.mark.parametrize(
    "mime_type",
    [
        "application/pdf\r\nX-Injected: 1",
        "text/html; charset=evil",
        "not a mime",
        "/pdf",
        "application/",
        "application/pdf ",
    ],
)
def test_material_create_rejects_invalid_mime_type(mime_type: str):
    with pytest.raises(ValidationError):
        MaterialCreate(
            kind="document",
            title="材料",
            content_base64="aGk=",
            mime_type=mime_type,
            idempotency_key="k-mime",
        )


@pytest.mark.parametrize("mime_type", ["image/png", "application/pdf", "text/plain"])
def test_material_create_accepts_simple_mime_types(mime_type: str):
    body = MaterialCreate(
        kind="document",
        title="材料",
        content_base64="aGk=",
        mime_type=mime_type,
        idempotency_key="k-mime",
    )

    assert body.mime_type == mime_type


def test_material_create_allows_missing_mime_type():
    body = MaterialCreate(
        kind="text",
        title="材料",
        content="正文",
        idempotency_key="k-mime",
    )

    assert body.mime_type is None
