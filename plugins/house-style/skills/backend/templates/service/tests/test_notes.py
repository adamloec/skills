import pytest

from {{pkg}}.api.routes.notes import update_note
from {{pkg}}.lib.exceptions import BadRequestError
from {{pkg}}.services.note_service import NoteService


async def test_a_created_note_comes_back_with_its_name(client):
    response = await client.post("/v1/notes/", json={"display_name": "  Inbox  "})
    assert response.status_code == 201, response.text
    assert response.json()["display_name"] == "Inbox"


async def test_a_duplicate_name_is_a_conflict(client, make_note):
    await make_note("Inbox")
    response = await client.post("/v1/notes/", json={"display_name": "Inbox"})
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "conflict"


async def test_an_unknown_patch_field_is_refused_not_dropped(session, user, make_note):
    note = await make_note()
    with pytest.raises(BadRequestError, match="Cannot update org_id"):
        await update_note(note_id=note.id, body={"org_id": "other"}, user=user, session=session)


async def test_another_organizations_note_is_not_found(client, make_note):
    note = await make_note(org_id="org_someone_else")
    response = await client.get(f"/v1/notes/{note.id}")
    assert response.status_code == 404, response.text


async def test_a_cursor_resumes_after_the_last_row(session, user, make_note):
    for name in ("a", "b", "c"):
        await make_note(name)
    first = await NoteService.list_page(session, org_id=user.org_id, cursor=None, limit=2)
    second = await NoteService.list_page(
        session, org_id=user.org_id, cursor=first.next_cursor, limit=2,
    )
    assert len(first.items) == 2 and first.next_cursor is not None
    assert len(second.items) == 1 and second.next_cursor is None
    seen = {n.display_name for n in first.items + second.items}
    assert seen == {"a", "b", "c"}
