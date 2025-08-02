from french_audio_processor import FrenchAudioProcessor

# Initialize the processor
processor = FrenchAudioProcessor("processed")

# Process your French audio file
result = processor.process_audio_file("my_podcast.mp3")

# The result contains all the processed data
print(f"Processed {result['totalSegments']} segments")
