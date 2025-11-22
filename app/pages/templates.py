import streamlit as st

from app.services import forms as forms_service


def main():
    st.title("Template Library — Dev Preview")

    tpls = list(forms_service._TEMPLATES.values()) if hasattr(forms_service, "_TEMPLATES") else []
    if not tpls:
        st.info("No templates yet.")

    st.subheader("Templates")
    for tpl in tpls:
        meta_name = tpl.get("meta", {}).get("name") or f"Template {tpl['id']}"
        st.write(f"{tpl['id']} — {meta_name}")
        if st.button(f"Create form from template {tpl['id']}", key=f"create-{tpl['id']}"):
            new = forms_service.create_from_template(tpl['id'], user_id=1)
            st.success(f"Created form {new['id']} from template {tpl['id']}")

    st.subheader("Save current form as template")
    forms = forms_service.list_forms()
    if forms:
        choices = [f"{f['id']} - {f.get('title','Untitled')}" for f in forms]
        sel = st.selectbox("Select form to save", choices)
        if st.button("Save as Template"):
            fid = int(sel.split(" - ")[0])
            tpl = forms_service.save_template(fid, meta={"name": f"Template from form {fid}"})
            st.success(f"Saved template {tpl['id']}")


if __name__ == "__main__":
    main()
