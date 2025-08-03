
from pathlib import Path
import sys
import os
import streamlit as st
from datetime import datetime
from stopwords import get_stopwords
import json
import collections
import pickle
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')))  # noqa
from src.french_audio_processor import FrenchAudioProcessor


# Set output directory (same as used in your processor)
OUTPUT_DIR = Path("french_learning_output")

st.title("French Audio Learning Tool")

uploaded_files = st.file_uploader(
    "Upload French audio files", type=["mp3", "wav", "m4a"], accept_multiple_files=True)

if uploaded_files:
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)
    file_paths = []
    for uploaded_file in uploaded_files:
        tmp_path = tmp_dir / uploaded_file.name
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.read())
        file_paths.append(tmp_path)

    st.success(
        f"Uploaded {len(uploaded_files)} files: {[f.name for f in uploaded_files]}")

    if st.button("Process Audio Files"):
        processor = FrenchAudioProcessor(str(OUTPUT_DIR))
        import types

        def process_audio_file_with_progress(self, input_file: str):
            print(f"\n=== Processing {input_file} ===")
            base_name = Path(input_file).stem
            output_base = f"{base_name}"
            audio = self.load_and_preprocess_audio(input_file)
            segments = self.split_audio_intelligently(audio)
            processed_sections = []
            total_segments = len(segments)
            progress_bar = st.progress(0, text=f"Processing {input_file}...")
            for i, segment in enumerate(segments):
                progress_bar.progress(
                    (i+1)/total_segments, text=f"Processing segment {i+1}/{total_segments} ({input_file})")
                french_text = self.transcribe_audio_segment(segment)
                if not french_text:
                    continue
                french_text = self.clean_text(french_text)
                english_text = self.translate_text(french_text)
                english_text = self.clean_text(english_text)
                french_audio_path = self.output_dir / \
                    "french_audio" / f"{output_base}_fr_{i+1:03d}.mp3"
                english_audio_path = self.output_dir / \
                    "english_audio" / f"{output_base}_en_{i+1:03d}.mp3"
                segment.export(french_audio_path, format="mp3")
                self.generate_tts_audio(
                    english_text, str(english_audio_path), 'en')
                section_data = {
                    "frenchText": french_text,
                    "englishText": english_text,
                    "frenchAudioFilePath": str(french_audio_path.relative_to(self.output_dir)),
                    "englishAudioFilePath": str(english_audio_path.relative_to(self.output_dir)),
                    "duration_seconds": len(segment) / 1000.0,
                    "segment_number": i + 1
                }
                processed_sections.append(section_data)
            result = {
                "fileName": Path(input_file).name,
                "processedAt": datetime.now().isoformat(),
                "totalSegments": len(processed_sections),
                "totalDuration": len(audio) / 1000.0,
                "outputDirectory": str(self.output_dir),
                "sections": processed_sections
            }
            json_path = self.output_dir / f"{output_base}_processed.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            progress_bar.progress(
                1.0, text=f"Processing complete for {input_file}!")
            return result
        processor.process_audio_file = types.MethodType(
            process_audio_file_with_progress, processor)
        for tmp_path in file_paths:
            result = processor.process_audio_file(tmp_path)
            st.success(
                f"Processed {result['totalSegments']} segments for {tmp_path.name}.")
            st.write("JSON file:", result["fileName"])
        # Remove tmp files and folder
        try:
            for tmp_path in file_paths:
                tmp_path.unlink()
            tmp_dir.rmdir()
        except Exception:
            pass

# List processed files
st.header("Processed Files")
json_files = sorted(OUTPUT_DIR.glob("*_processed.json"))

if json_files:
    selected_file = st.selectbox("Select a processed file", [
                                 f.name for f in json_files])
    if selected_file:
        with open(OUTPUT_DIR / selected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        sections = data.get("sections", [])
        french_stopwords = set(get_stopwords("fr"))

        # --- User-defined filter list ---
        st.markdown(
            "**Additional word filter list (e.g. names, custom words):**")
        filter_words_input = st.text_area(
            "Enter words to filter (comma or newline separated)",
            value="jean, marie, pierre, luc, julie", key="filter_words_input")
        # Parse input into a set
        user_filter_words = set()
        for line in filter_words_input.splitlines():
            for word in line.split(","):
                w = word.strip().lower()
                if w:
                    user_filter_words.add(w)

        # --- Vocab Extraction ---
        def extract_vocab(texts):
            words = []
            for text in texts:
                for w in text.split():
                    w_lower = w.lower()
                    # Filter stopwords and user filter words
                    if w_lower.isalpha() and w_lower not in french_stopwords and w_lower not in user_filter_words:
                        words.append(w_lower)
            return words

        # Per-file vocab
        file_vocab_words = extract_vocab(
            [s.get("frenchText", "") for s in sections])
        file_vocab_counter = collections.Counter(file_vocab_words)

        # Global vocab cache
        vocab_cache_path = OUTPUT_DIR / "vocab_cache.pkl"
        if vocab_cache_path.exists():
            with open(vocab_cache_path, "rb") as f:
                global_vocab_counter = pickle.load(f)
        else:
            global_vocab_counter = collections.Counter()

        # Update global vocab if new file processed
        if st.session_state.get("update_global_vocab", False):
            global_vocab_counter.update(file_vocab_counter)
            with open(vocab_cache_path, "wb") as f:
                pickle.dump(global_vocab_counter, f)
            st.session_state["update_global_vocab"] = False

        # Tabs for vocab views
        tab_sections, tab_file_vocab, tab_global_vocab = st.tabs(
            ["Sections", "File Vocab", "Global Vocab"])

        # --- Sections Tab ---
        with tab_sections:
            st.subheader("Sections")
            hide_english = st.checkbox(label="Hide English text and audio")
            page_size = st.selectbox("Page size", options=[
                                     5, 10, 20, 50], index=1)
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

        # --- File Vocab Tab ---
        with tab_file_vocab:
            st.subheader(f"French Vocab (Current File)")
            file_vocab_sorted = file_vocab_counter.most_common()
            file_vocab_page_size = st.selectbox(
                "Page size", options=[10, 20, 50], index=0, key="file_vocab_page_size")
            file_vocab_num_pages = max(
                1, (len(file_vocab_sorted) + file_vocab_page_size - 1) // file_vocab_page_size)
            file_vocab_page_num = st.number_input(
                "Page", min_value=1, max_value=file_vocab_num_pages, value=1, key="file_vocab_page_num")
            file_vocab_start = (file_vocab_page_num - 1) * file_vocab_page_size
            file_vocab_end = min(file_vocab_start +
                                 file_vocab_page_size, len(file_vocab_sorted))
            st.write(f"Page {file_vocab_page_num} of {file_vocab_num_pages}")
            st.table([
                {"Word": word, "Frequency": freq}
                for word, freq in file_vocab_sorted[file_vocab_start:file_vocab_end]
            ])

        # --- Global Vocab Tab ---
        with tab_global_vocab:
            st.subheader("French Vocab (All Files)")
            global_vocab_sorted = global_vocab_counter.most_common()
            global_vocab_page_size = st.selectbox(
                "Page size", options=[10, 20, 50], index=0, key="global_vocab_page_size")
            global_vocab_num_pages = max(
                1, (len(global_vocab_sorted) + global_vocab_page_size - 1) // global_vocab_page_size)
            global_vocab_page_num = st.number_input(
                "Page", min_value=1, max_value=global_vocab_num_pages, value=1, key="global_vocab_page_num")
            global_vocab_start = (global_vocab_page_num -
                                  1) * global_vocab_page_size
            global_vocab_end = min(
                global_vocab_start + global_vocab_page_size, len(global_vocab_sorted))
            st.write(
                f"Page {global_vocab_page_num} of {global_vocab_num_pages}")
            st.table([
                {"Word": word, "Frequency": freq}
                for word, freq in global_vocab_sorted[global_vocab_start:global_vocab_end]
            ])
else:
    st.info("No processed files found.")
