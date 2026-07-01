import streamlit as st

from pipeline import run_full_pipeline


st.set_page_config(page_title="ScaffoldAI", page_icon="S", layout="wide")

st.title("ScaffoldAI")
st.markdown(
    "Upload a CS assignment PDF to extract the core concepts, get a concise "
    "conceptual scaffold, and generate focused warm-up coding drills."
)

uploaded_file = st.file_uploader("Upload assignment PDF", type=["pdf"])
generate_clicked = st.button(
    "Generate Drills", type="primary", disabled=uploaded_file is None
)

if generate_clicked:
    if uploaded_file is None:
        st.warning("Please upload a PDF first.")
    else:
        try:
            with st.spinner("Analyzing assignment and generating drills..."):
                result = run_full_pipeline(uploaded_file)

            st.success("Analysis complete.")

            st.subheader("Detected Language")
            st.markdown(f"`{result['primary_language']}`")

            st.subheader("Extracted Concepts")
            st.markdown(
                "\n".join(f"- `{primitive}`" for primitive in result["primitives"])
            )

            st.subheader("Conceptual Scaffolding")
            st.markdown(result["scaffolding"])

            st.subheader("Warm-Up Drills")
            for drill in result["drills"].split("\n\n## Drill "):
                if not drill.strip():
                    continue
                if drill.startswith("## Drill "):
                    st.markdown(drill)
                else:
                    st.markdown(f"## Drill {drill}")
        except Exception as exc:
            st.error("The pipeline failed while processing this assignment.")
            st.exception(exc)
