#!/usr/bin/env python3
"""
French Audio Learning Tool
Processes French audio files to create learning materials with translations and TTS.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict
from pydub import AudioSegment
from pydub.silence import split_on_silence
import speech_recognition as sr
from googletrans import Translator
import pyttsx3
from gtts import gTTS
from datetime import datetime


class FrenchAudioProcessor:
    def __init__(self, output_dir: str = "output"):
        """Initialize the processor with necessary components."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (self.output_dir / "french_audio").mkdir(exist_ok=True)
        (self.output_dir / "english_audio").mkdir(exist_ok=True)

        # Initialize components
        self.recognizer = sr.Recognizer()
        self.translator = Translator()

        # Initialize TTS engines
        self.tts_engine = pyttsx3.init()
        self._setup_tts()

        print("French Audio Processor initialized successfully!")

    def _setup_tts(self):
        """Configure text-to-speech settings."""
        voices = self.tts_engine.getProperty('voices')

        # Try to find French and English voices
        self.french_voice = None
        self.english_voice = None

        for voice in voices:
            if 'french' in voice.name.lower() or 'fr' in voice.id.lower():
                self.french_voice = voice.id
            elif 'english' in voice.name.lower() or 'en' in voice.id.lower():
                self.english_voice = voice.id

        # Set speech rate
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.9)

    def load_and_preprocess_audio(self, file_path: str) -> AudioSegment:
        """Load audio file and convert to appropriate format."""
        print(f"Loading audio file: {file_path}")

        # Load audio using pydub (supports many formats)
        audio = AudioSegment.from_file(file_path)

        # Convert to mono and appropriate sample rate
        audio = audio.set_channels(1).set_frame_rate(16000)

        # Normalize audio
        audio = audio.normalize()

        return audio

    def split_audio_intelligently(self, audio: AudioSegment) -> List[AudioSegment]:
        """Split audio into logical segments based on silence and duration."""
        print("Splitting audio into segments...")

        # First, try splitting on silence
        segments = split_on_silence(
            audio,
            min_silence_len=1000,  # 1 second of silence
            silence_thresh=audio.dBFS - 16,  # 16dB below average
            keep_silence=500  # Keep 0.5s of silence at edges
        )

        # If segments are too long (>30s), split them further
        final_segments = []
        for segment in segments:
            if len(segment) > 30000:  # 30 seconds
                # Split long segments into smaller chunks
                chunk_length = 20000  # 20 seconds
                for i in range(0, len(segment), chunk_length):
                    chunk = segment[i:i + chunk_length]
                    if len(chunk) > 5000:  # Only keep chunks longer than 5s
                        final_segments.append(chunk)
            elif len(segment) > 3000:  # Only keep segments longer than 3s
                final_segments.append(segment)

        print(f"Created {len(final_segments)} audio segments")
        return final_segments

    def transcribe_audio_segment(self, audio_segment: AudioSegment) -> str:
        """Transcribe a single audio segment to French text."""
        # Export segment to temporary WAV file
        temp_path = self.output_dir / "temp_segment.wav"
        audio_segment.export(temp_path, format="wav")

        try:
            with sr.AudioFile(str(temp_path)) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)

            # Recognize speech in French
            text = self.recognizer.recognize_google(
                audio_data, language='fr-FR')
            return text.strip()

        except sr.UnknownValueError:
            print("Could not understand audio segment")
            return ""
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
            return ""
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

    def translate_text(self, french_text: str) -> str:
        """Translate French text to English."""
        if not french_text.strip():
            return ""

        try:
            translation = self.translator.translate(
                french_text, src='fr', dest='en')
            return translation.text
        except Exception as e:
            print(f"Translation error: {e}")
            return f"[Translation failed for: {french_text[:50]}...]"

    def generate_tts_audio(self, text: str, output_path: str, language: str = 'fr'):
        """Generate text-to-speech audio file."""
        print(
            f"Generating TTS: lang={language}, path={output_path}, text={text[:30]}, english_voice={self.english_voice is not None}, french_voice={self.french_voice is not None}")

        if not text.strip():
            return False

        try:
            if language == 'en':
                # Use gTTS for English
                tts = gTTS(text=text, lang='en')
                tts.save(output_path)
                return True
            else:
                # Use pyttsx3 for French
                if self.french_voice:
                    self.tts_engine.setProperty('voice', self.french_voice)
                self.tts_engine.save_to_file(text, output_path)
                self.tts_engine.runAndWait()
                return True
        except Exception as e:
            print(f"TTS error for {language}: {e}")
            return False

    def clean_text(self, text: str) -> str:
        """Clean and normalize text for better processing."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Fix common transcription issues
        text = text.replace(' .', '.')
        text = text.replace(' ,', ',')
        text = text.replace(' ?', '?')
        text = text.replace(' !', '!')

        return text

    def process_audio_file(self, input_file: str) -> Dict:
        """Main processing function."""
        print(f"\n=== Processing {input_file} ===")

        # Get base filename for output
        base_name = Path(input_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_base = f"{base_name}_{timestamp}"

        # Load and preprocess audio
        audio = self.load_and_preprocess_audio(input_file)

        # Split into segments
        segments = self.split_audio_intelligently(audio)

        # Process each segment
        processed_sections = []

        for i, segment in enumerate(segments):
            print(f"\nProcessing segment {i+1}/{len(segments)}")

            # Transcribe French audio
            french_text = self.transcribe_audio_segment(segment)

            if not french_text:
                print(f"Skipping segment {i+1} - no transcription")
                continue

            # Clean the transcription
            french_text = self.clean_text(french_text)
            print(f"French: {french_text[:100]}...")

            # Translate to English
            english_text = self.translate_text(french_text)
            english_text = self.clean_text(english_text)
            print(f"English: {english_text[:100]}...")

            # Generate audio file paths
            french_audio_path = self.output_dir / \
                "french_audio" / f"{output_base}_fr_{i+1:03d}.mp3"
            english_audio_path = self.output_dir / \
                "english_audio" / f"{output_base}_en_{i+1:03d}.mp3"

            # Save original French audio segment
            segment.export(french_audio_path, format="mp3")

            # Generate English TTS (now using gTTS)
            self.generate_tts_audio(
                english_text, str(english_audio_path), 'en')

            # Create section data
            section_data = {
                "frenchText": french_text,
                "englishText": english_text,
                "frenchAudioFilePath": str(french_audio_path.relative_to(self.output_dir)),
                "englishAudioFilePath": str(english_audio_path.relative_to(self.output_dir)),
                "duration_seconds": len(segment) / 1000.0,
                "segment_number": i + 1
            }

            processed_sections.append(section_data)

        # Create final JSON structure
        result = {
            "fileName": Path(input_file).name,
            "processedAt": datetime.now().isoformat(),
            "totalSegments": len(processed_sections),
            "totalDuration": len(audio) / 1000.0,
            "outputDirectory": str(self.output_dir),
            "sections": processed_sections
        }

        # Save JSON file
        json_path = self.output_dir / f"{output_base}_processed.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n=== Processing Complete ===")
        print(f"Processed {len(processed_sections)} segments")
        print(f"Results saved to: {json_path}")

        return result


def main():
    """Example usage of the French Audio Processor."""
    # Initialize processor
    processor = FrenchAudioProcessor("french_learning_output")

    # Example usage
    audio_file = input("Enter the path to your French audio file: ").strip()

    if not os.path.exists(audio_file):
        print(f"File not found: {audio_file}")
        return

    try:
        result = processor.process_audio_file(audio_file)
        print(f"\nSuccess! Check the output directory for your learning materials.")
        print(
            f"JSON file contains {result['totalSegments']} sections ready for your interface.")

    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
