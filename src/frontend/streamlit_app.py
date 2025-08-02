
from pathlib import Path
import sys
import os
import streamlit as st
import tempfile
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')))  # noqa
from src.french_audio_processor import FrenchAudioProcessor


# Set output directory (same as used in your processor)
OUTPUT_DIR = Path("french_learning_output")

st.title("French Audio Learning Tool")

# Drag & drop audio file
uploaded_file = st.file_uploader(
    "Upload a French audio file", type=["mp3", "wav", "m4a"])

if uploaded_file:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.success(f"File uploaded: {uploaded_file.name}")

    if st.button("Process Audio File"):
        processor = FrenchAudioProcessor(str(OUTPUT_DIR))
        result = processor.process_audio_file(tmp_path)
        st.success(f"Processed {result['totalSegments']} segments.")
        st.write("JSON file:", result["fileName"])
        os.unlink(tmp_path)

# List processed files
st.header("Processed Files")
json_files = sorted(OUTPUT_DIR.glob("*_processed.json"))

if json_files:
    selected_file = st.selectbox("Select a processed file", [
                                 f.name for f in json_files])
    if selected_file:
        import json
        with open(OUTPUT_DIR / selected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        sections = data.get("sections", [])

        st.subheader("Sections")
        hide_english = st.checkbox(label="Hide English text and audio")
        page_size = st.selectbox("Page size", options=[5, 10, 20, 50], index=1)
        num_pages = (len(sections) + page_size - 1) // page_size
        if "page_num" not in st.session_state:
            st.session_state.page_num = 1
        col_prev, col_page, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("Previous", key="prev_page") and st.session_state.page_num > 1:
                st.session_state.page_num -= 1
        with col_page:
            st.write(f"Page {st.session_state.page_num} of {num_pages}")
        with col_next:
            if st.button("Next", key="next_page") and st.session_state.page_num < num_pages:
                st.session_state.page_num += 1
        page_num = st.session_state.page_num
        start_idx = (page_num - 1) * page_size
        end_idx = min(start_idx + page_size, len(sections))

        # Grid header
        cols = st.columns([2, 2])
        cols[0].write("French")
        cols[1].write("English" if not hide_english else "")

        # Grid rows (paginated)
        for i in range(start_idx, end_idx):
            section = sections[i]
            cols = st.columns([2, 2])
            with cols[0]:
                st.write(section.get("frenchText", ""))
                french_audio_path = OUTPUT_DIR / \
                    section.get("frenchAudioFilePath", "")
                if french_audio_path.exists():
                    st.audio(str(french_audio_path))
            if not hide_english:
                with cols[1]:
                    st.write(section.get("englishText", ""))
                    english_audio_path = OUTPUT_DIR / \
                        section.get("englishAudioFilePath", "")
                    if english_audio_path.exists():
                        st.audio(str(english_audio_path))
else:
    st.info("No processed files found.")
