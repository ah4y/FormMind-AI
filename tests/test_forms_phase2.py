import pytest

from app.services import forms as forms_service


def test_create_and_get_form():
    f = forms_service.create_form({"title":"T1","description":"d"}, user_id=1)
    got = forms_service.get_form(f["id"])
    assert got is not None and got["title"] == "T1"


def test_add_and_remove_question():
    f = forms_service.create_form({"title":"QTest"}, user_id=2)
    q = forms_service.add_question(f["id"], {"text":"What is your name?"})
    assert q["id"]
    removed = forms_service.remove_question(f["id"], q["id"])
    assert removed is True
    # removing again should return False
    removed2 = forms_service.remove_question(f["id"], q["id"])
    assert removed2 is False


def test_reorder_questions():
    f = forms_service.create_form({"title":"RTest"}, user_id=3)
    q1 = forms_service.add_question(f["id"], {"text":"A"})
    q2 = forms_service.add_question(f["id"], {"text":"B"})
    ids = [q2["id"], q1["id"]]
    forms_service.reorder_questions(f["id"], ids)
    f2 = forms_service.get_form(f["id"])
    assert [q["id"] for q in f2["questions"]] == ids


def test_save_and_create_from_template():
    f = forms_service.create_form({"title":"TplTest"}, user_id=4)
    q = forms_service.add_question(f["id"], {"text":"X"})
    tpl = forms_service.save_template(f["id"], meta={"name":"m"})
    new = forms_service.create_from_template(tpl["id"], user_id=4)
    assert new["title"] == f["title"]
    assert new["id"] != f["id"]


def test_update_form_versioning():
    f = forms_service.create_form({"title":"VTest","status":"published"}, user_id=5)
    # simulate submissions exist => require new version
    updated = forms_service.update_form(f["id"], {"title":"VTest2"}, user_id=5, submissions_count=2)
    # if new version created, id should be different and version incremented
    assert updated["id"] != f["id"]
    assert updated["version"] == f.get("version",1)+1
