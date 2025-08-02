# French Audio Learning Tool - Setup Guide

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install System Dependencies

#### On macOS:

```bash
brew install ffmpeg portaudio
```

#### On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install ffmpeg portaudio19-dev python3-pyaudio
```

#### On Windows:

- Download and install FFmpeg from https://ffmpeg.org/download.html
- Add FFmpeg to your system PATH
- PyAudio should install automatically with pip

### 3. Verify Installation

Run this simple test:

```python
python3 -c "import speech_recognition, pydub, googletrans, pyttsx3; print('All dependencies installed successfully!')"
```

## Usage

### Basic Usage

```python
from french_audio_processor import FrenchAudioProcessor

# Initialize the processor
processor = FrenchAudioProcessor("my_output_directory")

# Process your French audio file
result = processor.process_audio_file("my_podcast.mp3")

# The result contains all the processed data
print(f"Processed {result['totalSegments']} segments")
```

### Command Line Usage

```bash
python3 french_audio_processor.py
# Enter file path when prompted
```

## Output Structure

The tool creates this directory structure:

```
output_directory/
├── french_audio/          # Original audio segments
│   ├── podcast_fr_001.mp3
│   ├── podcast_fr_002.mp3
│   └── ...
├── english_audio/         # English TTS audio files
│   ├── podcast_en_001.mp3
│   ├── podcast_en_002.mp3
│   └── ...
└── podcast_processed.json # Main JSON file with all data
```

## JSON Output Format

```json
{
  "fileName": "podcast.mp3",
  "processedAt": "2024-01-15T14:30:00",
  "totalSegments": 25,
  "totalDuration": 1800.5,
  "outputDirectory": "output",
  "sections": [
    {
      "frenchText": "Bonjour et bienvenue dans ce podcast...",
      "englishText": "Hello and welcome to this podcast...",
      "frenchAudioFilePath": "french_audio/podcast_fr_001.mp3",
      "englishAudioFilePath": "english_audio/podcast_en_001.mp3",
      "duration_seconds": 12.5,
      "segment_number": 1
    }
    // ... more sections
  ]
}
```

## Key Features

1. **Intelligent Audio Splitting**: Uses silence detection and duration limits to create logical segments
2. **French Speech Recognition**: Uses Google's speech recognition with French language models
3. **Automatic Translation**: Translates French to English using Google Translate
4. **Text-to-Speech**: Generates English audio using system TTS voices
5. **Structured Output**: Creates JSON file perfect for building interfaces

## Tips for Best Results

1. **Audio Quality**: Use clear audio with minimal background noise
2. **File Formats**: Supports MP3, WAV, M4A, and other common formats
3. **Processing Time**: Large files may take several minutes to process
4. **Internet Required**: Needs internet for speech recognition and translation
5. **Voice Selection**: The tool automatically selects French/English voices if available

## Troubleshooting

### Common Issues:

1. **"No module named 'pyaudio'"**

   - Install portaudio system dependency first
   - On Windows, try: `pip install pipwin && pipwin install pyaudio`

2. **FFmpeg not found**

   - Install FFmpeg and add to system PATH
   - Restart terminal after installation

3. **Speech recognition errors**

   - Check internet connection
   - Ensure audio quality is good
   - Try with shorter audio segments first

4. **No French/English voices**
   - Install additional TTS voices on your system
   - The tool will use default system voice if specific language voices aren't available

## Building Your Interface

The JSON output is designed to be easily consumed by web interfaces, mobile apps, or other tools. Each section contains:

- Original French text and audio
- English translation and TTS audio
- Timing information
- File paths for all resources

Perfect for creating flashcard apps, language learning interfaces, or study tools!
