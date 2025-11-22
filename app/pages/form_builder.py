import streamlit as st

from app.services import forms as forms_service


def _format_form_choice(f):
    return f"{f['id']} - {f.get('title','Untitled')} (v{f.get('version',1)})"


def main():
    st.title("Form Builder — Dev Preview")

    st.sidebar.header("Create Form")
    new_title = st.sidebar.text_input("Title", "New Form")
    new_desc = st.sidebar.text_area("Description", "")
    if st.sidebar.button("Create Form"):
        form = forms_service.create_form({"title": new_title, "description": new_desc}, user_id=1)
        st.sidebar.success(f"Created form {form['id']}")

    forms = forms_service.list_forms()
    if not forms:
        st.info("No forms yet — create one from the sidebar.")
        return

    choices = [_format_form_choice(f) for f in forms]
    sel = st.selectbox("Select form", choices)
    form_id = int(sel.split(" - ")[0])
    form = forms_service.get_form(form_id)

    st.header(form.get("title") or f"Form {form_id}")
    st.write(form.get("description", ""))

    st.subheader("Questions")
    qs = form.get("questions", [])
    for idx, q in enumerate(qs):
        with st.expander(f"{idx+1}. {q.get('text','(no text)')}"):
            st.text_input("Question text", value=q.get("text",""), key=f"qtext-{form_id}-{q['id']}")
            st.selectbox("Type", ["short", "long", "radio", "checkbox", "select"], index=0, key=f"qtype-{form_id}-{q['id']}")
            cols = st.columns([1,1,4])
            if cols[0].button("Up", key=f"up-{form_id}-{q['id']}"):
                ids = [qq['id'] for qq in qs]
                if idx>0:
                    ids[idx], ids[idx-1] = ids[idx-1], ids[idx]
                    forms_service.reorder_questions(form_id, ids)
                    st.experimental_rerun()
            if cols[1].button("Down", key=f"down-{form_id}-{q['id']}"):
                ids = [qq['id'] for qq in qs]
                if idx < len(qs)-1:
                    ids[idx], ids[idx+1] = ids[idx+1], ids[idx]
                    forms_service.reorder_questions(form_id, ids)
                    st.experimental_rerun()
            if cols[2].button("Delete", key=f"del-{form_id}-{q['id']}"):
                forms_service.remove_question(form_id, q['id'])
                st.experimental_rerun()

    st.subheader("Add Question")
    q_text = st.text_input("Question text", key="new_q_text")
    q_type = st.selectbox("Question type", ["short", "long", "radio", "checkbox", "select"], key="new_q_type")
    if st.button("Add Question"):
        q = {"text": q_text, "type": q_type}
        forms_service.add_question(form_id, q)
        st.experimental_rerun()


if __name__ == "__main__":
    main()
